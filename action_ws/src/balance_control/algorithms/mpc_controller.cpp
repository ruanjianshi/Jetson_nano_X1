/*
 * MPC Controller Implementation
 * ===============================
 */

#include "mpc_controller.h"
#include <cmath>

namespace balance_control {

MPCController::MPCController()
    : horizon_(10)   // 默认预测10步
    , dt_(0.01)      // 默认10ms时间步长
{
    // 初始化为单位矩阵
    A_.setIdentity(6, 6);
    B_.setZero(6, 6);
    Q_mpc_.setIdentity(6, 6);
    R_mpc_.setIdentity(6, 6);
}

void MPCController::reset() {
    // 清除预测序列
    predicted_states_.clear();
    control_inputs_.clear();
}

void MPCController::computeControl(const Eigen::VectorXd& state,
                                  const Eigen::VectorXd& target,
                                  Eigen::VectorXd& output) {
    // 检查输入维度
    if (state.size() < 6 || target.size() < 6) {
        return;
    }

    // 初始状态
    Eigen::VectorXd x0 = state;

    // 初始化预测序列
    predicted_states_.resize(horizon_ + 1);
    control_inputs_.resize(horizon_);

    // 第一个预测状态是当前状态
    predicted_states_[0] = x0;

    // 预测未来状态
    for (size_t k = 0; k < horizon_; ++k) {
        // 获取控制输入 (如果没有则为零)
        Eigen::VectorXd u_k(6);
        u_k.setZero();

        if (k > 0 && control_inputs_.size() > k - 1) {
            u_k = control_inputs_[k - 1];
        }

        // 使用模型预测下一个状态: x(k+1) = A*x(k) + B*u(k)
        Eigen::VectorXd x_next = A_ * predicted_states_[k] + B_ * u_k;
        predicted_states_[k + 1] = x_next;

        // 保存控制输入
        control_inputs_[k] = u_k;
    }

    // 求解QP得到最优控制
    Eigen::VectorXd u_optimal(6);
    solveQP(x0, u_optimal);

    // 构建输出向量
    output.resize(12);
    output.segment<6>(0) = u_optimal;  // 前6个是控制力/力矩
    output.segment<6>(6).setZero();    // 后6个保留
}

void MPCController::solveQP(const Eigen::VectorXd& x0, Eigen::VectorXd& u_optimal) {
    // 初始化最优控制为零
    u_optimal.setZero();

    // 使用梯度下降法求解
    Eigen::VectorXd x_pred = x0;
    for (size_t k = 0; k < horizon_; ++k) {
        // 计算梯度: grad = B' * (x_pred - x0)
        // 更新控制: u = u - alpha * grad
        Eigen::VectorXd u_k = -0.5 * (R_mpc_ + Eigen::MatrixXd::Identity(6, 6)).inverse() * B_.transpose() * (x_pred - x0);

        // 限制控制输出在允许范围内
        for (int i = 0; i < 6; ++i) {
            u_k(i) = std::max(-params_.max_torque, std::min(params_.max_torque, u_k(i)));
        }

        // 更新预测状态
        x_pred = A_ * x_pred + B_ * u_k;
        
        // 保存最优控制
        u_optimal = u_k;
    }
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