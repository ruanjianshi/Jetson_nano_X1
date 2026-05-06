/*
 * MPC Controller (Model Predictive Control)
 * ==========================================
 * 
 * 功能说明:
 *   - 实现模型预测控制算法
 *   - 在有限时域内优化控制输入
 *   - 处理系统约束和成本函数
 * 
 * 算法原理:
 *   预测模型: x(k+1) = A*x(k) + B*u(k)
 *   成本函数: J = Σ(x'Qx + u'Ru)
 *   在每个时刻求解优化问题得到最优控制序列
 * 
 * 使用方法:
 *   1. 创建 MPCController 实例
 *   2. 设置预测时域和时间步长 (setMPCParams)
 *   3. 设置预测模型矩阵A,B (setPredictionModel)
 *   4. 调用 computeControl 计算控制输出
 * 
 * Author: Qi Xiao
Email: 2408128687@qq.com
 * 日期: 2026-05-06
 */

#ifndef MPC_CONTROLLER_H
#define MPC_CONTROLLER_H

#include "balance_algorithm_base.h"
#include <vector>

namespace balance_control {

/**
 * @brief MPC控制器类
 * @details 实现模型预测控制，用于平衡控制
 */
class MPCController : public BalanceAlgorithm {
public:
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW

    /**
     * @brief 构造函数
     * @details 初始化MPC控制器，默认时域10步，时间步长10ms
     */
    MPCController();

    /**
     * @brief 重置控制器状态
     * @details 清除预测状态和控制输入历史
     */
    void reset() override;

    /**
     * @brief 计算MPC控制输出
     * @param state 当前状态 [roll, pitch, yaw, omega_x, omega_y, omega_z]
     * @param target 目标状态
     * @param output 控制输出
     */
    void computeControl(const Eigen::VectorXd& state,
                        const Eigen::VectorXd& target,
                        Eigen::VectorXd& output) override;

    /**
     * @brief 获取算法名称
     * @return "MPC"
     */
    std::string getName() const override { return "MPC"; }

    /**
     * @brief 设置MPC参数
     * @param horizon 预测时域步数
     * @param dt 时间步长 (秒)
     */
    void setMPCParams(size_t horizon, double dt);

    /**
     * @brief 设置预测模型
     * @param A 状态转移矩阵 (6x6)
     * @param B 控制输入矩阵 (6x6)
     */
    void setPredictionModel(const Eigen::MatrixXd& A, const Eigen::MatrixXd& B);

private:
    /**
     * @brief 求解二次规划
     * @param x0 初始状态
     * @param u_optimal 最优控制输入
     * @details 使用梯度下降法求解QP问题
     */
    void solveQP(const Eigen::VectorXd& x0, Eigen::VectorXd& u_optimal);

    size_t horizon_;       // 预测时域步数
    double dt_;             // 时间步长 (秒)

    Eigen::MatrixXd A_;     // 状态转移矩阵
    Eigen::MatrixXd B_;     // 控制输入矩阵
    Eigen::MatrixXd Q_mpc_; // 状态权重矩阵
    Eigen::MatrixXd R_mpc_; // 控制权重矩阵

    std::vector<Eigen::VectorXd> predicted_states_;  // 预测状态序列
    std::vector<Eigen::VectorXd> control_inputs_;    // 控制输入序列
};

} // namespace balance_control

#endif // MPC_CONTROLLER_H