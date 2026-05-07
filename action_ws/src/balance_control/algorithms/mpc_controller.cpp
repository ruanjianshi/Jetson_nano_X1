/*
 * MPC Controller Implementation (URDF匹配版)
 * ==========================================
 */

#include "mpc_controller.h"
#include <cmath>

namespace balance_control {

MPCController::MPCController()
    : horizon_(10)
    , dt_(0.01)
{
    A_.setIdentity(6, 6);
    // 初始化控制矩阵 B: 简单的对角输入模型 dt*I
    B_.setZero(6, 6);
    for (int i = 0; i < 6; ++i) B_(i, i) = dt_;
    Q_mpc_.setIdentity(6, 6);
    R_mpc_.setIdentity(6, 6);
}

void MPCController::reset() {
    predicted_states_.clear();
    control_inputs_.clear();
}

void MPCController::computeControl(const Eigen::VectorXd& state,
                                  const Eigen::VectorXd& target,
                                  Eigen::VectorXd& output) {
    if (output.size() != 8) {
        output.resize(8);
    }

    if (state.size() < 6 || target.size() < 6) {
        output.setZero();
        return;
    }

    Eigen::VectorXd x0 = state;

    predicted_states_.resize(horizon_ + 1);
    control_inputs_.resize(horizon_);

    predicted_states_[0] = x0;

    for (size_t k = 0; k < horizon_; ++k) {
        Eigen::VectorXd u_k(6);
        u_k.setZero();

        if (k > 0 && control_inputs_.size() > k - 1) {
            u_k = control_inputs_[k - 1];
        }

        Eigen::VectorXd x_next = A_ * predicted_states_[k] + B_ * u_k;
        predicted_states_[k + 1] = x_next;
        control_inputs_[k] = u_k;
    }

    Eigen::VectorXd u_optimal(6);
    solveQP(x0, target, u_optimal);

    // 映射: pitch → 轮子主平衡, roll → hip_roll, yaw → wheel差速
    double wheel_torque = u_optimal(1) + u_optimal(4);
    double wheel_diff   = u_optimal(2) + u_optimal(5);
    double hip_pitch_aux = u_optimal(1) * 0.3;

    output.setZero();
    output(0) = u_optimal(0);                  // 左hip_roll
    output(1) = hip_pitch_aux;                 // 左hip_pitch
    output(2) = hip_pitch_aux * 0.5;           // 左knee_pitch
    output(3) = wheel_torque / 2.0 + wheel_diff;  // 左轮
    output(4) = -u_optimal(0);                 // 右hip_roll
    output(5) = hip_pitch_aux;                 // 右hip_pitch
    output(6) = hip_pitch_aux * 0.5;           // 右knee_pitch
    output(7) = wheel_torque / 2.0 - wheel_diff;  // 右轮

    double max_tau = params_.max_torque;
    for (int i = 0; i < 8; ++i) {
        output(i) = std::max(-max_tau, std::min(max_tau, output(i)));
    }
}

void MPCController::solveQP(const Eigen::VectorXd& x0, const Eigen::VectorXd& target,
                             Eigen::VectorXd& u_optimal) {
    u_optimal.setZero();

    Eigen::VectorXd error = target - x0;

    // 反馈 u = -K * error, K ≈ 1000*I (匹配LQR增益 ~10*B^-1)
    Eigen::VectorXd u_k = -1000.0 * Q_mpc_ * B_.transpose() * error;

    // 限幅
    for (int i = 0; i < 6; ++i) {
        u_k(i) = std::max(-params_.max_torque,
                 std::min(params_.max_torque, u_k(i)));
    }

    u_optimal = u_k;
}

void MPCController::setMPCParams(size_t horizon, double dt) {
    horizon_ = horizon;
    dt_ = dt;
}

void MPCController::setPredictionModel(const Eigen::MatrixXd& A, const Eigen::MatrixXd& B) {
    A_ = A;
    B_ = B;
}

} // namespace balance_control
