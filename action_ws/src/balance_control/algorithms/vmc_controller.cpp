/*
 * VMC Controller Implementation (URDF匹配版)
 * ==========================================
 */

#include "vmc_controller.h"
#include <cmath>

namespace balance_control {

VMCController::VMCController()
    : leg_stiffness_(200.0)
    , leg_damping_(20.0)
    , body_stiffness_(50.0)
    , body_damping_(5.0)
{
    left_foot_pos_.setZero();
    right_foot_pos_.setZero();
    body_force_.setZero();
    body_torque_.setZero();
}

void VMCController::reset() {
    body_force_.setZero();
    body_torque_.setZero();
}

void VMCController::computeControl(const Eigen::VectorXd& state,
                                   const Eigen::VectorXd& target,
                                   Eigen::VectorXd& output) {
    if (output.size() != 8) {
        output.resize(8);
    }

    if (state.size() < 6 || target.size() < 6) {
        output.setZero();
        return;
    }

    // 弹簧力 F = -K*(当前-目标), 指向恢复方向; 阻尼力 = -D*当前速度
    Eigen::Vector3d body_pos_error(state[0] - target[0], state[1] - target[1], state[2] - target[2]);
    Eigen::Vector3d body_vel_error(state[3], state[4], state[5]);

    Eigen::Vector3d desired_force = -(body_stiffness_ * body_pos_error)
                                    - (body_damping_ * body_vel_error);

    Eigen::Vector3d left_foot_error = left_foot_pos_;
    Eigen::Vector3d right_foot_error = right_foot_pos_;

    Eigen::Vector3d left_force = leg_stiffness_ * left_foot_error;
    Eigen::Vector3d right_force = leg_stiffness_ * right_foot_error;

    body_force_ = (left_force + right_force) * 0.5 + desired_force;

    body_torque_[0] = (right_force[1] - left_force[1]) * 0.1;
    body_torque_[1] = (left_force[0] - right_force[0]) * 0.1;
    body_torque_[2] = (left_force[1] + right_force[1]) * 0.05;

    // 轮子为主平衡执行器, 腿关节为辅
    double wheel_torque = -body_force_[1] * 0.8;     // Fy → wheel主平衡
    double wheel_diff   = body_torque_[2] * 0.2;      // Tz → yaw差动
    double hip_pitch_aux = -body_force_[1] * 0.15;    // 辅

    output.setZero();
    output(0) = -body_force_[0] * 0.5;     // 左hip_roll
    output(1) = hip_pitch_aux;             // 左hip_pitch
    output(2) = hip_pitch_aux * 0.5;       // 左knee_pitch
    output(3) = wheel_torque + wheel_diff; // 左轮
    output(4) = body_force_[0] * 0.5;      // 右hip_roll
    output(5) = hip_pitch_aux;             // 右hip_pitch
    output(6) = hip_pitch_aux * 0.5;       // 右knee_pitch
    output(7) = wheel_torque - wheel_diff; // 右轮

    double max_tau = params_.max_torque;
    for (int i = 0; i < 8; ++i) {
        output(i) = std::max(-max_tau, std::min(max_tau, output(i)));
    }
}

void VMCController::setVirtualModelParams(double leg_stiffness, double leg_damping,
                                          double body_stiffness, double body_damping) {
    leg_stiffness_ = leg_stiffness;
    leg_damping_ = leg_damping;
    body_stiffness_ = body_stiffness;
    body_damping_ = body_damping;
}

void VMCController::setFootPositions(const Eigen::Vector3d& left_foot,
                                     const Eigen::Vector3d& right_foot) {
    left_foot_pos_ = left_foot;
    right_foot_pos_ = right_foot;
}

} // namespace balance_control
