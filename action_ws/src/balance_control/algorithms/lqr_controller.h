/*
 * LQR Controller (Linear Quadratic Regulator)
 * ============================================
 * 
 * 功能说明:
 *   - 实现LQR最优控制算法
 *   - 通过状态反馈最小化二次成本函数
 *   - 适用于线性化后的系统
 * 
 * 算法原理:
 *   J = ∫(x'Qx + u'Ru)dt
 *   u = -Kx
 *   K = (R + B'PB)^(-1) * B'PA
 * 
 * 使用方法:
 *   1. 创建 LQRController 实例
 *   2. 设置 Q,R 矩阵 (setLQRParams)
 *   3. 调用 computeControl 计算控制输出
 * 
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#ifndef LQR_CONTROLLER_H
#define LQR_CONTROLLER_H

#include "balance_algorithm_base.h"

namespace balance_control {

/**
 * @brief LQR控制器类
 * @details 实现线性二次调节器，用于平衡控制
 */
class LQRController : public BalanceAlgorithm {
public:
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW

    /**
     * @brief 构造函数
     * @details 初始化LQR控制器，默认状态维度为6
     */
    LQRController();

    /**
     * @brief 重置控制器状态
     * @details 清除状态误差历史
     */
    void reset() override;

    /**
     * @brief 计算LQR控制输出
     * @param state 当前状态 [roll, pitch, yaw, omega_x, omega_y, omega_z]
     * @param target 目标状态
     * @param output 控制输出 (力矩向量)
     */
    void computeControl(const Eigen::VectorXd& state,
                        const Eigen::VectorXd& target,
                        Eigen::VectorXd& output) override;

    /**
     * @brief 获取算法名称
     * @return "LQR"
     */
    std::string getName() const override { return "LQR"; }

    /**
     * @brief 设置LQR参数矩阵
     * @param Q 状态权重矩阵 (6x6)
     * @param R 控制权重矩阵 (6x6)
     */
    void setLQRParams(const Eigen::MatrixXd& Q, const Eigen::MatrixXd& R);

    /**
     * @brief 设置状态维度
     * @param dim 状态向量维度
     */
    void setStateDimension(size_t dim) { state_dim_ = dim; }

private:
    Eigen::MatrixXd Q_;        // 状态权重矩阵
    Eigen::MatrixXd R_;        // 控制权重矩阵
    Eigen::MatrixXd K_;        // 反馈增益矩阵
    size_t state_dim_;         // 状态维度
};

} // namespace balance_control

#endif // LQR_CONTROLLER_H