#include <dynamics/dynamics.hpp>

#include <fstream>
#include <sstream>

#include <kdl_parser/kdl_parser.hpp>
#include <urdf_parser/urdf_parser.h>

Dynamics::Dynamics(std::string urdf_path, std::string root_link, std::string leaf_link)
    : urdf_path_(std::move(urdf_path)),
      root_link_(std::move(root_link)),
      leaf_link_(std::move(leaf_link)) {}

bool Dynamics::Init() {
    std::ifstream file(urdf_path_);
    if (!file.is_open()) {
        fprintf(stderr, "[Dynamics] Failed to open URDF file: %s\n", urdf_path_.c_str());
        return false;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    file.close();

    return InitFromURDFString(buffer.str());
}

bool Dynamics::InitFromURDFString(const std::string &urdf_string) {
    auto urdf_model = urdf::parseURDF(urdf_string);
    if (!urdf_model) {
        fprintf(stderr, "[Dynamics] Failed to parse URDF string\n");
        return false;
    }

    if (!kdl_parser::treeFromUrdfModel(*urdf_model, kdl_tree_)) {
        fprintf(stderr, "[Dynamics] Failed to extract KDL tree from URDF\n");
        return false;
    }

    return InitFromModel();
}

bool Dynamics::InitFromModel() {
    if (!kdl_tree_.getChain(root_link_, leaf_link_, kdl_chain_)) {
        fprintf(stderr, "[Dynamics] Failed to get KDL chain from '%s' to '%s'\n", root_link_.c_str(),
                leaf_link_.c_str());
        return false;
    }

    joint_names_.clear();
    for (unsigned int i = 0; i < kdl_chain_.getNrOfSegments(); ++i) {
        const KDL::Joint &joint = kdl_chain_.getSegment(i).getJoint();
        if (joint.getType() != KDL::Joint::None) {
            joint_names_.push_back(joint.getName());
        }
    }

    gravity_forces_.resize(kdl_chain_.getNrOfJoints());
    gravity_forces_.data.setZero();
    coriolis_forces_.resize(kdl_chain_.getNrOfJoints());
    coriolis_forces_.data.setZero();

    // Same convention as OpenArm: gravity along -Z.
    solver_ = std::make_unique<KDL::ChainDynParam>(kdl_chain_, gravity_vec_);

    // Snapshot pristine geometry/inertia so live COM offsets are always
    // applied relative to the original URDF values (not accumulated).
    CacheBaseInertia();

    fprintf(stdout, "[Dynamics] chain '%s' -> '%s': %u joints\n", root_link_.c_str(),
            leaf_link_.c_str(), kdl_chain_.getNrOfJoints());

    return true;
}

// --------------------------------------------------------------------
// Snapshot each segment's mass, original COG and the rotational inertia
// *about that COG* (Ic). KDL stores inertia about the segment origin, so
// we strip the parallel-axis term to recover Ic, which the RigidBodyInertia
// constructor expects. This lets us later rebuild a segment with a shifted
// COG while keeping mass and rotational inertia physically consistent.
// --------------------------------------------------------------------
void Dynamics::CacheBaseInertia() {
    base_chain_ = kdl_chain_;
    seg_names_.clear();
    seg_mass_.clear();
    base_cog_.clear();
    base_Ic_.clear();
    com_offset_.clear();

    for (unsigned int s = 0; s < kdl_chain_.getNrOfSegments(); ++s) {
        const KDL::Segment &seg = kdl_chain_.getSegment(s);
        const KDL::RigidBodyInertia I0 = seg.getInertia();

        const double m = I0.getMass();
        const KDL::Vector c = I0.getCOG();
        const KDL::RotationalInertia Io = I0.getRotationalInertia();  // about origin

        // Parallel-axis term P = m * (|c|^2 * Id - c c^T)
        const double cx = c.x(), cy = c.y(), cz = c.z();
        const double P[9] = {
            m * (cy * cy + cz * cz), -m * cx * cy,             -m * cx * cz,
            -m * cx * cy,            m * (cx * cx + cz * cz),  -m * cy * cz,
            -m * cx * cz,            -m * cy * cz,             m * (cx * cx + cy * cy)};

        KDL::RotationalInertia Ic;
        for (int k = 0; k < 9; ++k) {
            Ic.data[k] = Io.data[k] - P[k];  // Ic = Io - P  (inertia about COG)
        }

        seg_names_.push_back(seg.getName());
        seg_mass_.push_back(m);
        base_cog_.push_back(c);
        base_Ic_.push_back(Ic);
        com_offset_.push_back(KDL::Vector::Zero());
    }
}

// Rebuild kdl_chain_ + solver_ with the current COM offsets applied.
void Dynamics::RebuildSolver() {
    KDL::Chain new_chain;

    for (unsigned int s = 0; s < base_chain_.getNrOfSegments(); ++s) {
        const KDL::Segment &seg = base_chain_.getSegment(s);
        const KDL::Vector new_cog = base_cog_[s] + com_offset_[s];
        const KDL::RigidBodyInertia new_I(seg_mass_[s], new_cog, base_Ic_[s]);

        new_chain.addSegment(KDL::Segment(seg.getName(), seg.getJoint(), seg.getFrameToTip(), new_I));
    }

    std::lock_guard<std::mutex> lock(solver_mutex_);
    kdl_chain_ = new_chain;
    solver_ = std::make_unique<KDL::ChainDynParam>(kdl_chain_, gravity_vec_);
}

std::vector<std::string> Dynamics::GetMassiveSegmentNames() const {
    std::vector<std::string> names;
    for (size_t s = 0; s < seg_names_.size(); ++s) {
        if (seg_mass_[s] > 1e-9) names.push_back(seg_names_[s]);
    }
    return names;
}

bool Dynamics::SetComOffset(const std::string &seg_name, double dx, double dy, double dz) {
    for (size_t s = 0; s < seg_names_.size(); ++s) {
        if (seg_names_[s] == seg_name) {
            com_offset_[s] = KDL::Vector(dx, dy, dz);
            RebuildSolver();
            return true;
        }
    }
    return false;
}

void Dynamics::GetComMarkers(const double *joint_position, std::vector<std::string> &names,
                              std::vector<std::array<double, 3>> &positions,
                              std::vector<double> &masses) {
    names.clear();
    positions.clear();
    masses.clear();

    std::lock_guard<std::mutex> lock(solver_mutex_);

    KDL::JntArray q(kdl_chain_.getNrOfJoints());
    for (unsigned int i = 0; i < kdl_chain_.getNrOfJoints(); ++i) {
        q(i) = joint_position[i];
    }

    KDL::ChainFkSolverPos_recursive fk(kdl_chain_);

    for (unsigned int s = 0; s < kdl_chain_.getNrOfSegments(); ++s) {
        if (seg_mass_[s] <= 1e-9) continue;

        KDL::Frame F;
        // Frame of segment s' reference (tip) relative to the chain base.
        if (fk.JntToCart(q, F, s + 1) < 0) continue;

        const KDL::Vector world_cog = F * (base_cog_[s] + com_offset_[s]);

        names.push_back(seg_names_[s]);
        positions.push_back({world_cog.x(), world_cog.y(), world_cog.z()});
        masses.push_back(seg_mass_[s]);
    }
}

void Dynamics::GetGravity(const double *joint_position, double *gravity) {
    std::lock_guard<std::mutex> lock(solver_mutex_);

    const unsigned int njoints = kdl_chain_.getNrOfJoints();

    KDL::JntArray q(njoints);
    for (unsigned int i = 0; i < njoints; ++i) {
        q(i) = joint_position[i];
    }

    solver_->JntToGravity(q, gravity_forces_);

    for (unsigned int i = 0; i < njoints; ++i) {
        gravity[i] = gravity_forces_(i);
    }
}

void Dynamics::GetCoriolis(const double *joint_position, const double *joint_velocity, double *coriolis) {
    std::lock_guard<std::mutex> lock(solver_mutex_);

    const unsigned int njoints = kdl_chain_.getNrOfJoints();

    KDL::JntArray q(njoints);
    KDL::JntArray q_dot(njoints);
    for (unsigned int i = 0; i < njoints; ++i) {
        q(i) = joint_position[i];
        q_dot(i) = joint_velocity[i];
    }

    solver_->JntToCoriolis(q, q_dot, coriolis_forces_);

    for (unsigned int i = 0; i < njoints; ++i) {
        coriolis[i] = coriolis_forces_(i);
    }
}

void Dynamics::GetMassMatrixDiagonal(const double *joint_position, double *inertia_diag) {
    std::lock_guard<std::mutex> lock(solver_mutex_);

    const unsigned int njoints = kdl_chain_.getNrOfJoints();

    KDL::JntArray q(njoints);
    KDL::JntSpaceInertiaMatrix inertia_matrix(njoints);
    for (unsigned int i = 0; i < njoints; ++i) {
        q(i) = joint_position[i];
    }

    solver_->JntToMass(q, inertia_matrix);

    for (unsigned int i = 0; i < njoints; ++i) {
        inertia_diag[i] = inertia_matrix(i, i);
    }
}

void Dynamics::GetJacobian(const double *joint_position, Eigen::MatrixXd &jacobian) {
    std::lock_guard<std::mutex> lock(solver_mutex_);

    const unsigned int njoints = kdl_chain_.getNrOfJoints();

    KDL::JntArray q(njoints);
    for (unsigned int i = 0; i < njoints; ++i) {
        q(i) = joint_position[i];
    }

    KDL::Jacobian kdl_jac(njoints);
    KDL::ChainJntToJacSolver jac_solver(kdl_chain_);
    jac_solver.JntToJac(q, kdl_jac);

    jacobian = Eigen::MatrixXd(6, njoints);
    for (unsigned int i = 0; i < 6; ++i) {
        for (unsigned int j = 0; j < njoints; ++j) {
            jacobian(i, j) = kdl_jac(i, j);
        }
    }
}

namespace {
Eigen::MatrixXd PseudoInverse(const Eigen::MatrixXd &J) {
    return J.transpose() * (J * J.transpose()).inverse();
}
}  // namespace

void Dynamics::GetNullSpace(const double *joint_position, Eigen::MatrixXd &nullspace) {
    Eigen::MatrixXd J;
    GetJacobian(joint_position, J);

    const unsigned int dof = static_cast<unsigned int>(J.cols());
    const Eigen::MatrixXd J_pinv = PseudoInverse(J);
    const Eigen::MatrixXd I = Eigen::MatrixXd::Identity(dof, dof);
    nullspace = I - J_pinv * J;
}

void Dynamics::GetNullSpaceTauSpace(const double *joint_position, Eigen::MatrixXd &nullspace_T) {
    Eigen::MatrixXd nullspace;
    GetNullSpace(joint_position, nullspace);
    nullspace_T = nullspace.transpose();
}

void Dynamics::GetEECordinate(const double *joint_position, Eigen::Matrix3d &R, Eigen::Vector3d &p) {
    std::lock_guard<std::mutex> lock(solver_mutex_);

    const unsigned int njoints = kdl_chain_.getNrOfJoints();

    KDL::JntArray q(njoints);
    for (unsigned int i = 0; i < njoints; ++i) {
        q(i) = joint_position[i];
    }

    KDL::ChainFkSolverPos_recursive fk_solver(kdl_chain_);
    KDL::Frame kdl_frame;

    if (fk_solver.JntToCart(q, kdl_frame) < 0) {
        return;
    }

    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) R(i, j) = kdl_frame.M(i, j);

    p << kdl_frame.p[0], kdl_frame.p[1], kdl_frame.p[2];
}

void Dynamics::GetPreEECordinate(const double *joint_position, Eigen::Matrix3d &R, Eigen::Vector3d &p) {
    std::lock_guard<std::mutex> lock(solver_mutex_);

    const unsigned int njoints = kdl_chain_.getNrOfJoints();

    KDL::JntArray q(njoints);
    for (unsigned int i = 0; i < njoints; ++i) {
        q(i) = joint_position[i];
    }

    KDL::ChainFkSolverPos_recursive fk_solver(kdl_chain_);
    KDL::Frame kdl_frame;

    if (fk_solver.JntToCart(q, kdl_frame, kdl_chain_.getNrOfSegments() - 1) < 0) {
        return;
    }

    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j) R(i, j) = kdl_frame.M(i, j);

    p << kdl_frame.p[0], kdl_frame.p[1], kdl_frame.p[2];
}

size_t Dynamics::GetNumJoints() const { return joint_names_.size(); }

const std::vector<std::string> &Dynamics::GetJointNames() const { return joint_names_; }
