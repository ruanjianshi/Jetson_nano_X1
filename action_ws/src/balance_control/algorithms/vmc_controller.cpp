/*
 * VMC Controller Implementation
 * ==============================
 */

#include "vmc_controller.h"
#include <cmath>

namespace balance_control {

VMCController::VMCController()
    : leg_stiffness_(200.0)    // 默认腿部刚度 200 N/m
    , leg_damping_(20.0)       // 默认腿部阻尼 20 Ns/m
    , body_stiffness_(50.0)    // 默认身体刚度 50 N/m
    , body_damping_(5.0)       // 默认身体阻尼 5 Ns/m
{
    // 初始化足端位置为零
    left_foot_pos_.setZero();
    right_foot_pos_.setZero();
    body_force_.setZero();
    body_torque_.setZero();
}

void VMCController::reset() {
    // 重置身体力和力矩
    body_force_.setZero();
    body_torque_.setZero();
}

void VMCController::computeControl(const Eigen::VectorXd& state,
                                   const Eigen::VectorXd& target,
                                   Eigen::VectorXd& output) {
    // 检查输入维度
    if (state.size() < 6 || target.size() < 6) {
        return;
    }

    // 从目标状态提取位置和速度误差
    // target[0-2]: 位置误差 (roll, pitch, yaw)
    // target[3-5]: 速度误差 (omega_x, omega_y, omega_z)
    Eigen::Vector3d body_pos_error(target[0], target[1], target[2]);
    Eigen::Vector3d body_vel_error(target[3], target[4], target[5]);

    // 计算期望的身体力 (弹簧阻尼力)
    // F = K * error_pos + D * error_vel
    Eigen::Vector3d desired_force = body_stiffness_ * body_pos_error + body_damping_ * body_vel_error;

    // 计算足端误差 (相对于平衡位置)
    Eigen::Vector3d left_foot_error = left_foot_pos_;
    Eigen::Vector3d right_foot_error = right_foot_pos_;

    // 计算腿部弹簧力
    Eigen::Vector3d left_force = leg_stiffness_ * left_foot_error;
    Eigen::Vector3d right_force = leg_stiffness_ * right_foot_error;

    // 合并所有力: 腿部力 + 期望力
    body_force_ = (left_force + right_force) * 0.5 + desired_force;

    // 计算力矩:
    // Tx = (右腿Y力 - 左腿Y力) * 腿长
    // Ty = (左腿X力 - 右腿X力) * 腿长
    // Tz = (左腿Y力 + 右腿Y力) * 腿长 (用于转向)
    body_torque_[0] = (right_force[1] - left_force[1]) * 0.1;
    body_torque_[1] = (left_force[0] - right_force[0]) * 0.1;
    body_torque_[2] = (left_force[1] + right_force[1]) * 0.05;

    // 构建输出向量: [Fx, Fy, Fz, Tx, Ty, Tz, 0, 0, 0, 0, 0, 0]
    output.resize(12);
    output.segment<3>(0) = body_force_;
    output.segment<3>(3) = body_torque_;
    output.segment<6>(6).setZero();  // 后6个元素保留
}

void VMCController::setVirtualModelParams(double leg_stiffness, double leg_damping,
                                          double body_stiffness, double body_damping) {
    leg_stiffness_ = leg_stiffness;
    leg_damping_ = leg_damping;
    body_stiffness_ = body_stiffness;
    body_damping_ = body_damping;
}

void VMCController::setFootPositions(const Eigen::Vector3d& left_foot, const Eigen::Vector3d& right_foot) {
    left_foot_pos_ = left_foot;
    right_foot_pos_ = right_foot;
}

} // namespace balance_control