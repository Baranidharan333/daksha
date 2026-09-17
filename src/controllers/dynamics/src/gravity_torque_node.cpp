#include <rclcpp/rclcpp.hpp>
#include <rcl_interfaces/msg/floating_point_range.hpp>
#include <rcl_interfaces/msg/parameter_descriptor.hpp>
#include <rcl_interfaces/msg/set_parameters_result.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <ament_index_cpp/get_package_share_directory.hpp>
#include <dynamics/dynamics.hpp>

#include <tinyxml2.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

// Reads the per-joint motor `direction` sign out of every <ros2_control>
// hardware block in the URDF. This is the same sign arm_interface.cpp
// applies to position/velocity/effort when talking to the physical motor,
// so gravity feedforward computed here (from /joint_states, which is
// already in that direction-corrected convention) must be flipped by the
// same sign before it can be trusted as a torque command.
std::unordered_map<std::string, double> ParseJointDirections(const std::string &urdf_path) {
    std::unordered_map<std::string, double> directions;

    tinyxml2::XMLDocument doc;
    if (doc.LoadFile(urdf_path.c_str()) != tinyxml2::XML_SUCCESS) {
        fprintf(stderr, "[GravityTorqueNode] Failed to load URDF for direction parsing: %s\n",
                urdf_path.c_str());
        return directions;
    }

    const tinyxml2::XMLElement *robot = doc.RootElement();
    if (!robot) return directions;

    for (const tinyxml2::XMLElement *ros2_control = robot->FirstChildElement("ros2_control");
         ros2_control != nullptr; ros2_control = ros2_control->NextSiblingElement("ros2_control")) {
        const tinyxml2::XMLElement *hardware = ros2_control->FirstChildElement("hardware");
        if (!hardware) continue;

        std::string direction_text;
        bool found = false;
        for (const tinyxml2::XMLElement *param = hardware->FirstChildElement("param"); param != nullptr;
             param = param->NextSiblingElement("param")) {
            const char *name_attr = param->Attribute("name");
            if (name_attr && std::string(name_attr) == "direction") {
                if (param->GetText()) direction_text = param->GetText();
                found = true;
                break;
            }
        }
        if (!found) continue;

        std::vector<double> signs;
        std::stringstream ss(direction_text);
        std::string item;
        while (std::getline(ss, item, ',')) {
            const size_t start = item.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) continue;
            const size_t end = item.find_last_not_of(" \t\r\n");
            item = item.substr(start, end - start + 1);
            if (item.empty()) continue;
            signs.push_back(std::stod(item));
        }

        std::vector<std::string> joint_names;
        for (const tinyxml2::XMLElement *joint = ros2_control->FirstChildElement("joint"); joint != nullptr;
             joint = joint->NextSiblingElement("joint")) {
            const char *jn = joint->Attribute("name");
            if (jn) joint_names.push_back(jn);
        }

        for (size_t i = 0; i < joint_names.size() && i < signs.size(); ++i) {
            directions[joint_names[i]] = signs[i];
        }
    }

    return directions;
}

}  // namespace

// Publishes /gravity_torque from two KDL chains (left/right arm), the same
// way OpenArm's gravity_compensation.cpp computes gravity torque, with the
// sign/scale pattern from gen3's hw_interface Dynamics integration:
//   effort = gravity(q) * direction * ff_scale
// - `direction` comes straight from the URDF's <ros2_control> hardware block
//   (single source of truth, matches what arm_interface.cpp applies).
// - `ff_scale` is per-joint and live-tunable via
//   `ros2 param set gravity_torque_node ff_scale.<joint> <value>`.
class GravityTorqueNode : public rclcpp::Node {
public:
    GravityTorqueNode() : Node("gravity_torque_node") {
        const std::string default_urdf_path =
            ament_index_cpp::get_package_share_directory("daksha_description_full_body") +
            "/urdf/robot.urdf";
        this->declare_parameter<std::string>("urdf_path", default_urdf_path);
        this->declare_parameter<std::string>("root_link", "base_link");
        this->declare_parameter<std::string>("right_leaf_link", "right_link_8");
        this->declare_parameter<std::string>("left_leaf_link", "left_link_8");
        this->declare_parameter<std::string>("joint_states_topic", "/joint_states");
        this->declare_parameter<std::string>("gravity_torque_topic", "/gravity_torque");

        const std::string urdf_path = this->get_parameter("urdf_path").as_string();
        const std::string root_link = this->get_parameter("root_link").as_string();
        const std::string right_leaf = this->get_parameter("right_leaf_link").as_string();
        const std::string left_leaf = this->get_parameter("left_leaf_link").as_string();

        right_dynamics_ = std::make_unique<Dynamics>(urdf_path, root_link, right_leaf);
        left_dynamics_ = std::make_unique<Dynamics>(urdf_path, root_link, left_leaf);

        if (!right_dynamics_->Init() || !left_dynamics_->Init()) {
            throw std::runtime_error("Dynamics::Init() failed, check urdf_path/root_link/leaf_link parameters");
        }

        right_joint_names_ = right_dynamics_->GetJointNames();
        left_joint_names_ = left_dynamics_->GetJointNames();

        right_q_.assign(right_joint_names_.size(), 0.0);
        left_q_.assign(left_joint_names_.size(), 0.0);
        right_gravity_.assign(right_joint_names_.size(), 0.0);
        left_gravity_.assign(left_joint_names_.size(), 0.0);

        joint_direction_ = ParseJointDirections(urdf_path);

        // Safety staging for incremental bring-up: only publish nonzero
        // gravity feedforward for joints in this list; all others report 0
        // effort regardless of computed gravity. Empty = all enabled.
        // Live-tunable via `ros2 param set gravity_torque_node enabled_joints "['joint1']"`.
        rcl_interfaces::msg::ParameterDescriptor enabled_desc;
        enabled_desc.description =
            "Joint names to publish nonzero gravity feedforward for (empty = all enabled). "
            "Used to test motors individually during bring-up.";
        const auto enabled_joints_vec = this->declare_parameter<std::vector<std::string>>(
            "enabled_joints", std::vector<std::string>{}, enabled_desc);
        SetEnabledJoints(enabled_joints_vec);

        // Per-joint gravity scale, tunable at runtime via
        // `ros2 param set gravity_torque_node ff_scale.<joint_name> <value>`.
        right_ff_scale_.assign(right_joint_names_.size(), kDefaultFfScale);
        left_ff_scale_.assign(left_joint_names_.size(), kDefaultFfScale);
        DeclareFfScaleParams(right_joint_names_, right_ff_scale_, right_ff_param_index_);
        DeclareFfScaleParams(left_joint_names_, left_ff_scale_, left_ff_param_index_);

        // Per-joint torque clamp, tunable at runtime via
        // `ros2 param set gravity_torque_node tau_limit.<joint_name> <value>`.
        right_tau_limit_ = MakeDefaultTauLimits(right_joint_names_.size());
        left_tau_limit_ = MakeDefaultTauLimits(left_joint_names_.size());
        DeclareTauLimitParams(right_joint_names_, right_tau_limit_, right_tau_limit_param_index_);
        DeclareTauLimitParams(left_joint_names_, left_tau_limit_, left_tau_limit_param_index_);

        param_callback_handle_ = this->add_on_set_parameters_callback(
            std::bind(&GravityTorqueNode::OnSetParameters, this, std::placeholders::_1));

        const std::string gravity_topic = this->get_parameter("gravity_torque_topic").as_string();
        const std::string joint_states_topic = this->get_parameter("joint_states_topic").as_string();

        gravity_pub_ = this->create_publisher<sensor_msgs::msg::JointState>(gravity_topic, 10);

        joint_state_sub_ = this->create_subscription<sensor_msgs::msg::JointState>(
            joint_states_topic, 10,
            std::bind(&GravityTorqueNode::JointStateCallback, this, std::placeholders::_1));

        RCLCPP_INFO(this->get_logger(),
                    "Gravity torque node started (right joints: %zu, left joints: %zu), "
                    "subscribing '%s', publishing '%s'",
                    right_joint_names_.size(), left_joint_names_.size(), joint_states_topic.c_str(),
                    gravity_topic.c_str());
    }

private:
    static constexpr double kDefaultFfScale = 0.15;

    // Per-joint safety clamp [Nm] applied to gravity feedforward after
    // direction/scale, indexed by position (joint_1..joint_7). Matches the
    // limits used by openarm's gravity_comp_node reference. Joints beyond
    // this array (e.g. a gripper) are left unclamped.
    static constexpr std::array<double, 7> kDefaultTauLimit = {20.0, 20.0, 7.0, 7.0, 2.0, 2.0, 2.0};

    void SetEnabledJoints(const std::vector<std::string> &names) {
        enabled_joints_ = std::unordered_set<std::string>(names.begin(), names.end());
        if (enabled_joints_.empty()) {
            RCLCPP_INFO(this->get_logger(), "[Enabled] Gravity feedforward active for all joints");
        } else {
            std::ostringstream joined;
            for (const auto &n : enabled_joints_) joined << n << " ";
            RCLCPP_INFO(this->get_logger(), "[Safety mode] Gravity feedforward restricted to: %s",
                        joined.str().c_str());
        }
    }

    void DeclareFfScaleParams(const std::vector<std::string> &joint_names, std::vector<double> &ff_scale,
                               std::unordered_map<std::string, size_t> &param_index) {
        rcl_interfaces::msg::ParameterDescriptor scale_desc;
        scale_desc.description = "Per-joint gravity feedforward scale (0=off)";
        {
            rcl_interfaces::msg::FloatingPointRange r;
            r.from_value = 0.0;
            r.to_value = 2.0;
            r.step = 0.0;  // continuous: a non-zero step makes declare_parameter throw
                           // if the default doesn't land exactly on the grid.
            scale_desc.floating_point_range.push_back(r);
        }

        for (size_t i = 0; i < joint_names.size(); ++i) {
            const std::string scale_param = "ff_scale." + joint_names[i];
            ff_scale[i] = this->declare_parameter<double>(scale_param, ff_scale[i], scale_desc);
            param_index[scale_param] = i;
        }
    }

    static std::vector<double> MakeDefaultTauLimits(size_t num_joints) {
        std::vector<double> limits(num_joints, std::numeric_limits<double>::infinity());
        for (size_t i = 0; i < num_joints && i < kDefaultTauLimit.size(); ++i) {
            limits[i] = kDefaultTauLimit[i];
        }
        return limits;
    }

    void DeclareTauLimitParams(const std::vector<std::string> &joint_names, std::vector<double> &tau_limit,
                                std::unordered_map<std::string, size_t> &param_index) {
        rcl_interfaces::msg::ParameterDescriptor limit_desc;
        limit_desc.description = "Per-joint gravity feedforward torque clamp [Nm] (abs value)";

        for (size_t i = 0; i < joint_names.size(); ++i) {
            const std::string limit_param = "tau_limit." + joint_names[i];
            tau_limit[i] = this->declare_parameter<double>(limit_param, tau_limit[i], limit_desc);
            param_index[limit_param] = i;
        }
    }

    rcl_interfaces::msg::SetParametersResult OnSetParameters(const std::vector<rclcpp::Parameter> &parameters) {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;

        for (const auto &param : parameters) {
            if (param.get_name() == "enabled_joints" &&
                param.get_type() == rclcpp::ParameterType::PARAMETER_STRING_ARRAY) {
                SetEnabledJoints(param.as_string_array());
                continue;
            }

            if (param.get_type() != rclcpp::ParameterType::PARAMETER_DOUBLE) continue;

            auto right_it = right_ff_param_index_.find(param.get_name());
            if (right_it != right_ff_param_index_.end()) {
                right_ff_scale_[right_it->second] = param.as_double();
                continue;
            }
            auto left_it = left_ff_param_index_.find(param.get_name());
            if (left_it != left_ff_param_index_.end()) {
                left_ff_scale_[left_it->second] = param.as_double();
                continue;
            }

            auto right_tau_it = right_tau_limit_param_index_.find(param.get_name());
            if (right_tau_it != right_tau_limit_param_index_.end()) {
                right_tau_limit_[right_tau_it->second] = std::abs(param.as_double());
                continue;
            }
            auto left_tau_it = left_tau_limit_param_index_.find(param.get_name());
            if (left_tau_it != left_tau_limit_param_index_.end()) {
                left_tau_limit_[left_tau_it->second] = std::abs(param.as_double());
            }
        }

        return result;
    }

    void JointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg) {
        std::unordered_map<std::string, double> position_map;
        position_map.reserve(msg->name.size());
        for (size_t i = 0; i < msg->name.size() && i < msg->position.size(); ++i) {
            position_map[msg->name[i]] = msg->position[i];
        }

        for (size_t i = 0; i < right_joint_names_.size(); ++i) {
            auto it = position_map.find(right_joint_names_[i]);
            if (it != position_map.end()) right_q_[i] = it->second;
        }
        for (size_t i = 0; i < left_joint_names_.size(); ++i) {
            auto it = position_map.find(left_joint_names_[i]);
            if (it != position_map.end()) left_q_[i] = it->second;
        }

        right_dynamics_->GetGravity(right_q_.data(), right_gravity_.data());
        left_dynamics_->GetGravity(left_q_.data(), left_gravity_.data());

        ApplyFeedforward(right_joint_names_, right_gravity_, right_ff_scale_, right_tau_limit_);
        ApplyFeedforward(left_joint_names_, left_gravity_, left_ff_scale_, left_tau_limit_);

        sensor_msgs::msg::JointState out;
        out.header.stamp = this->now();
        out.name.reserve(right_joint_names_.size() + left_joint_names_.size());
        out.effort.reserve(right_joint_names_.size() + left_joint_names_.size());

        for (size_t i = 0; i < right_joint_names_.size(); ++i) {
            out.name.push_back(right_joint_names_[i]);
            out.effort.push_back(right_gravity_[i]);
        }
        for (size_t i = 0; i < left_joint_names_.size(); ++i) {
            out.name.push_back(left_joint_names_[i]);
            out.effort.push_back(left_gravity_[i]);
        }

        gravity_pub_->publish(out);
    }

    // In place: gravity[i] = clamp(gravity(q)[i] * direction[i] * ff_scale[i], +-tau_limit[i]),
    // or 0 if joint_names[i] is excluded by enabled_joints_ (safety staging).
    void ApplyFeedforward(const std::vector<std::string> &joint_names, std::vector<double> &gravity,
                           const std::vector<double> &ff_scale, const std::vector<double> &tau_limit) {
        for (size_t i = 0; i < gravity.size(); ++i) {
            if (!enabled_joints_.empty() && enabled_joints_.find(joint_names[i]) == enabled_joints_.end()) {
                gravity[i] = 0.0;
                continue;
            }

            auto dir_it = joint_direction_.find(joint_names[i]);
            const double direction = dir_it != joint_direction_.end() ? dir_it->second : 1.0;

            const double limit = std::abs(tau_limit[i]);
            gravity[i] = std::clamp(gravity[i] * direction * ff_scale[i], -limit, limit);
        }
    }

    std::unique_ptr<Dynamics> right_dynamics_;
    std::unique_ptr<Dynamics> left_dynamics_;

    std::vector<std::string> right_joint_names_;
    std::vector<std::string> left_joint_names_;

    std::vector<double> right_q_;
    std::vector<double> left_q_;
    std::vector<double> right_gravity_;
    std::vector<double> left_gravity_;

    // joint_name -> direction sign, sourced from the URDF's <ros2_control>
    // hardware "direction" param (single source of truth).
    std::unordered_map<std::string, double> joint_direction_;

    // Joints allowed to receive nonzero gravity feedforward; empty = all
    // enabled. Mirrors the ENABLED_JOINTS safety-staging pattern used for
    // per-motor bring-up testing.
    std::unordered_set<std::string> enabled_joints_;

    std::vector<double> right_ff_scale_;
    std::vector<double> left_ff_scale_;
    std::unordered_map<std::string, size_t> right_ff_param_index_;
    std::unordered_map<std::string, size_t> left_ff_param_index_;

    std::vector<double> right_tau_limit_;
    std::vector<double> left_tau_limit_;
    std::unordered_map<std::string, size_t> right_tau_limit_param_index_;
    std::unordered_map<std::string, size_t> left_tau_limit_param_index_;

    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr gravity_pub_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
    OnSetParametersCallbackHandle::SharedPtr param_callback_handle_;
};

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);

    try {
        auto node = std::make_shared<GravityTorqueNode>();
        rclcpp::spin(node);
    } catch (const std::exception &e) {
        RCLCPP_FATAL(rclcpp::get_logger("gravity_torque_node"), "%s", e.what());
        rclcpp::shutdown();
        return 1;
    }

    rclcpp::shutdown();
    return 0;
}
