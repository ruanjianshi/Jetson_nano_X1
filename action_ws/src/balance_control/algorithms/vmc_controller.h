/*
 * VMC Controller (Virtual Model Control)
 * =======================================
 * 
 * 功能说明:
 *   - 实现虚拟模型控制算法
 *   - 通过虚拟弹簧阻尼器模拟机器人肢体
 *   - 计算维持平衡所需的力和力矩
 * 
 * 算法原理:
 *   虚拟弹簧: F = k * (x_desired - x_current) - b * v
 *   虚拟阻尼: D = -b * v
 * 
 * 使用方法:
 *   1. 创建 VMCController 实例
 *   2. 设置腿部和身体刚度阻尼参数 (setVirtualModelParams)
 *   3. 设置足端位置 (setFootPositions)
 *   4. 调用 computeControl 计算控制输出
 * 
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#ifndef VMC_CONTROLLER_H
#define VMC_CONTROLLER_H

#include "balance_algorithm_base.h"

namespace balance_control {

/**
 * @brief VMC控制器类
 * @details 实现虚拟模型控制，通过弹簧阻尼器模拟肢体
 */
class VMCController : public BalanceAlgorithm {
public:
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW

    /**
     * @brief 构造函数
     * @details 初始化虚拟模型参数
     */
    VMCController();

    /**
     * @brief 重置控制器状态
     * @details 清除身体力和力矩
     */
    void reset() override;

    /**
     * @brief 计算VMC控制输出
     * @param state 当前状态 [roll, pitch, yaw, omega_x, omega_y, omega_z]
     * @param target 目标状态
     * @param output 控制输出 [Fx, Fy, Fz, Tx, Ty, Tz, ...]
     */
    void computeControl(const Eigen::VectorXd& state,
                        const Eigen::VectorXd& target,
                        Eigen::VectorXd& output) override;

    /**
     * @brief 获取算法名称
     * @return "VMC"
     */
    std::string getName() const override { return "VMC"; }

    /**
     * @brief 设置虚拟模型参数
     * @param leg_stiffness 腿部弹簧刚度
     * @param leg_damping 腿部阻尼系数
     * @param body_stiffness 身体弹簧刚度
     * @param body_damping 身体阻尼系数
     */
    void setVirtualModelParams(double leg_stiffness, double leg_damping,
                               double body_stiffness, double body_damping);

    /**
     * @brief 设置足端位置
     * @param left_foot 左脚位置 (相对于髋关节)
     * @param right_foot 右脚位置 (相对于髋关节)
     */
    void setFootPositions(const Eigen::Vector3d& left_foot, const Eigen::Vector3d& right_foot);

private:
    Eigen::Vector3d left_foot_pos_;   // 左脚位置
    Eigen::Vector3d right_foot_pos_;  // 右脚位置

    double leg_stiffness_;    // 腿部弹簧刚度 (N/m)
    double leg_damping_;      // 腿部阻尼系数
    double body_stiffness_;   // 身体弹簧刚度 (N/m)
    double body_damping_;     // 身体阻尼系数

    Eigen::Vector3d body_force_;  // 计算得到的身体力
    Eigen::Vector3d body_torque_;  // 计算得到的身体力矩
};

} // namespace balance_control

#endif // VMC_CONTROLLER_H