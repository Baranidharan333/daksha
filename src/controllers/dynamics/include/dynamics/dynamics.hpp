#pragma once

#include <array>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include <Eigen/Dense>
#include <kdl/chain.hpp>
#include <kdl/chaindynparam.hpp>
#include <kdl/chainfksolverpos_recursive.hpp>
#include <kdl/chainjnttojacsolver.hpp>
#include <kdl/jntarray.hpp>
#include <kdl/jntspaceinertiamatrix.hpp>
#include <kdl/tree.hpp>

// Gravity/dynamics solver for a single serial chain (root_link -> leaf_link),
// ported from OpenArm's KDL-based Dynamics class (openarm_teleop/src/controller/dynamics.cpp)
// and extended with the coriolis/jacobian/null-space/live-COM-tuning logic from
// gen3's hw_interface Dynamics class. No sign flips, no scale factors: the
// returned torque is the raw KDL gravity torque for the joint angles given.
class Dynamics {
public:
    Dynamics(std::string urdf_path, std::string root_link, std::string leaf_link);

    // Load the URDF from urdf_path_ (this package's original entry point).
    bool Init();

    // Load from an in-memory URDF string, e.g. a ros2_control HardwareInfo's
    // original_xml, when there is no file on disk to read.
    bool InitFromURDFString(const std::string &urdf_string);

    // joint_position must have GetNumJoints() entries, ordered as GetJointNames().
    void GetGravity(const double *joint_position, double *gravity);
    void GetCoriolis(const double *joint_position, const double *joint_velocity, double *coriolis);
    void GetMassMatrixDiagonal(const double *joint_position, double *inertia_diag);

    void GetJacobian(const double *joint_position, Eigen::MatrixXd &jacobian);
    void GetNullSpace(const double *joint_position, Eigen::MatrixXd &nullspace);
    void GetNullSpaceTauSpace(const double *joint_position, Eigen::MatrixXd &nullspace_T);

    void GetEECordinate(const double *joint_position, Eigen::Matrix3d &R, Eigen::Vector3d &p);
    void GetPreEECordinate(const double *joint_position, Eigen::Matrix3d &R, Eigen::Vector3d &p);

    // -------- Live COM tuning --------
    // Names of chain segments that carry mass (the tunable links).
    std::vector<std::string> GetMassiveSegmentNames() const;

    // Set the COG offset (segment-local frame) for one segment and rebuild
    // the dynamics solver. Returns false if the name is unknown.
    bool SetComOffset(const std::string &seg_name, double dx, double dy, double dz);

    // For RViz: per massive segment, the COG position expressed in the chain
    // base (root_link) frame at the given joint configuration, plus its mass.
    void GetComMarkers(const double *joint_position, std::vector<std::string> &names,
                        std::vector<std::array<double, 3>> &positions, std::vector<double> &masses);

    size_t GetNumJoints() const;
    const std::vector<std::string> &GetJointNames() const;
    const std::string &GetBaseFrame() const { return root_link_; }

private:
    bool InitFromModel();
    void CacheBaseInertia();
    void RebuildSolver();

    std::string urdf_path_;
    std::string root_link_;
    std::string leaf_link_;

    KDL::Tree kdl_tree_;
    KDL::Chain kdl_chain_;
    std::unique_ptr<KDL::ChainDynParam> solver_;
    KDL::JntArray gravity_forces_;
    KDL::JntArray coriolis_forces_;

    std::vector<std::string> joint_names_;

    // -------- Live COM tuning state --------
    // Guards solver_ / kdl_chain_ against concurrent rebuild (param thread)
    // vs. evaluation (read/callback thread).
    std::mutex solver_mutex_;
    KDL::Vector gravity_vec_{0.0, 0.0, -9.81};
    KDL::Chain base_chain_;                       // pristine geometry + inertia
    std::vector<std::string> seg_names_;          // one per chain segment
    std::vector<double> seg_mass_;                // original mass per segment
    std::vector<KDL::Vector> base_cog_;           // original COG (segment frame)
    std::vector<KDL::RotationalInertia> base_Ic_; // inertia about original COG
    std::vector<KDL::Vector> com_offset_;         // live COG offset per segment
};
