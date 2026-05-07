/*
 * LQR Controller Implementation (URDF匹配版)
 * ==========================================
 *
 * 8路输出: [左h_roll, 左h_pitch, 左k_pitch, 左wheel, 右h_roll, 右h_pitch, 右k_pitch, 右wheel]
 *
 * 关节映射 (基于URDF关节轴):
 *   hip_roll  (绕X) → 控制左右平衡 (roll)
 *   hip_pitch (绕Y) → 控制前后平衡 (pitch)
 *   knee_pitch(绕Y) → 辅助高度/姿态
 *   wheel     (绕Y) → 前向/转向驱动
 */

#include "lqr_controller.h"
#include <cmath>

namespace balance_control {

LQRController::LQRController()
    : state_dim_(6) {
    Q_.setIdentity(state_dim_, state_dim_);
    R_.setIdentity(state_dim_, state_dim_);

    // K矩阵: 轮子为主平衡执行器 (类Segway倒立摆)
    // pitch → wheel torque (主), hip_pitch (辅)
    // roll  → hip_roll
    // yaw   → wheel differential
    K_.setZero(state_dim_, state_dim_);
    K_(0, 0) = 10.0;   // roll → u[0]
    K_(1, 1) = 50.0;   // pitch → u[1] (wheel主平衡)
    K_(2, 2) = 5.0;    // yaw → u[2]
    K_(3, 3) = 1.0;    // wx_D
    K_(4, 4) = 8.0;    // wy_D (wheel速度阻尼)
    K_(5, 5) = 0.5;    // wz_D

    state_error_.setZero(state_dim_);
}

void LQRController::reset() {
    state_error_.setZero(state_dim_);
}

void LQRController::computeControl(const Eigen::VectorXd& state,
                                   const Eigen::VectorXd& target,
                                   Eigen::VectorXd& output) {
    if (output.size() != 8) {
        output.resize(8);
    }

    if (state.size() != (int)state_dim_ || target.size() != (int)state_dim_) {
        output.setZero();
        return;
    }

    state_error_ = target - state;

    // 自适应Q矩阵调整
    for (size_t i = 0; i < state_dim_; ++i) {
        Q_(i, i) = 1.0 + std::abs(state_error_(i)) * 0.1;
    }

    // 从K矩阵计算控制: u = -K * error
    Eigen::VectorXd u = -K_ * state_error_;

    // 映射到8个电机
    // pitch → 轮子 (主平衡, 倒立摆类Segway机制)
    //        u[1]是pitch误差项, u[4]是wy阻尼项
    //        前倾(pitch>0, err<0) → u[1]>0 → 轮正力矩 → 前加速 → 反力后推
    // roll  → hip_roll (侧倾修正)
    // yaw   → wheel差速 (转向)
    output.setZero();

    double wheel_torque = u(1) + u(4);       // pitch P + D
    double wheel_diff   = u(2) + u(5);       // yaw P + D (差动)
    double hip_pitch_aux = u(1) * 0.3;        // pitch辅助 (COM前移)

    // 左腿
    output(0) = u(0);                          // hip_roll
    output(1) = hip_pitch_aux;                 // hip_pitch (辅)
    output(2) = hip_pitch_aux * 0.5;           // knee_pitch (辅)
    output(3) = wheel_torque / 2.0 + wheel_diff;  // 左轮 (主+差动)

    // 右腿 (hip_roll方向相反)
    output(4) = -u(0);                         // hip_roll
    output(5) = hip_pitch_aux;                 // hip_pitch (辅)
    output(6) = hip_pitch_aux * 0.5;           // knee_pitch (辅)
    output(7) = wheel_torque / 2.0 - wheel_diff;  // 右轮 (主-差动)

    // 力矩限幅
    double max_tau = params_.max_torque;
    for (int i = 0; i < 8; ++i) {
        output(i) = std::max(-max_tau, std::min(max_tau, output(i)));
    }
}

void LQRController::setLQRParams(const Eigen::MatrixXd& Q, const Eigen::MatrixXd& R) {
    if (Q.rows() == (int)state_dim_ && Q.cols() == (int)state_dim_) Q_ = Q;
    if (R.rows() == (int)state_dim_ && R.cols() == (int)state_dim_) R_ = R;
    // 求解Riccati方程重新计算K (简化版: 对角)
    for (size_t i = 0; i < state_dim_; ++i) {
        K_(i, i) = Q_(i, i) / (R_(i, i) + 0.1);
    }
}

} // namespace balance_control
