/*
 * LQR Controller Implementation
 * ==============================
 */

#include "lqr_controller.h"
#include <cmath>

namespace balance_control {

LQRController::LQRController()
    : state_dim_(6) {
    // 初始化权重矩阵
    Q_.setIdentity(state_dim_, state_dim_);
    R_.setIdentity(state_dim_, state_dim_);

    // 初始化LQR增益矩阵 (默认PID-like values)
    // K = [kp_roll, kp_pitch, kp_yaw, kd_roll, kd_pitch, kd_yaw]
    // 简化为对角矩阵
    K_.setZero(state_dim_, state_dim_);
    K_(0, 0) = 10.0;  // roll - P gain
    K_(1, 1) = 10.0;  // pitch - P gain
    K_(2, 2) = 5.0;   // yaw - P gain
    K_(3, 3) = 1.0;   // roll - D gain
    K_(4, 4) = 1.0;   // pitch - D gain
    K_(5, 5) = 0.5;   // yaw - D gain

    state_error_.setZero(state_dim_);
}

void LQRController::reset() {
    // 重置状态误差
    state_error_.setZero(state_dim_);
}

void LQRController::computeControl(const Eigen::VectorXd& state,
                                   const Eigen::VectorXd& target,
                                   Eigen::VectorXd& output) {
    // 确保输出向量大小正确 (12: 前8个是电机力矩, 后4个保留)
    if (output.size() != 12) {
        output.resize(12);
    }

    // 检查维度是否匹配
    if (state.size() != state_dim_ || target.size() != state_dim_) {
        output.setZero();
        return;
    }

    // 计算状态误差: error = target - current
    state_error_ = target - state;

    // 自适应调整Q矩阵: 根据误差大小增加对应状态的权重
    for (size_t i = 0; i < state_dim_; ++i) {
        Q_(i, i) *= (1.0 + std::abs(state_error_(i)) * 0.1);
    }

    // 计算控制输出: u = -K * error
    // K是状态反馈增益矩阵 (简化为单位阵)
    Eigen::VectorXd u = -K_ * state_error_;

    // 将控制输出映射到8个电机
    // roll控制髋横滚 (motor 0,4)
    // pitch控制髋俯仰和膝俯仰 (motor 1,2,5,6)
    // yaw控制转向 (保留)
    output.setZero();
    output(0) = u(0);  // 左髋横滚
    output(1) = u(1);  // 左髋俯仰
    output(2) = u(1) * 0.5;  // 左膝俯仰 (较小)
    output(3) = 0.0;  // 左轮
    output(4) = -u(0);  // 右髋横滚 (方向相反)
    output(5) = u(1);  // 右髋俯仰
    output(6) = u(1) * 0.5;  // 右膝俯仰
    output(7) = 0.0;  // 右轮
}

void LQRController::setLQRParams(const Eigen::MatrixXd& Q, const Eigen::MatrixXd& R) {
    Q_ = Q;
    R_ = R;
}

} // namespace balance_control