/*
 * Balance Control Algorithm Base Class
 * =====================================
 * 
 * 功能说明:
 *   - 定义平衡控制算法的统一接口
 *   - 所有算法(LQR/VMC/MPC)都继承此类
 * 
 * 使用方法:
 *   1. 创建算法实例 (如 LQRController)
 *   2. 设置参数 (setParams)
 *   3. 调用 computeControl 计算控制输出
 * 
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#ifndef BALANCE_ALGORITHM_BASE_H
#define BALANCE_ALGORITHM_BASE_H

#include <string>
#include <vector>
#include <Eigen/Dense>

namespace balance_control {

/**
 * @brief 控制算法枚举
 * @details 定义支持的平衡控制算法类型
 */
enum class ControlAlgorithm {
    LQR = 0,    // 线性二次调节器
    VMC = 1,    // 虚拟模型控制
    MPC = 2,    // 模型预测控制
    ADP = 3     // 自适应动态规划
};

/**
 * @brief 算法参数结构体
 * @details 包含PID控制器的增益参数和限制值
 */
struct AlgorithmParams {
    // Roll (横滚) PID参数 - 控制左右倾斜
    double kp_roll = 10.0;   // 比例增益
    double kd_roll = 1.0;   // 微分增益
    double ki_roll = 0.0;   // 积分增益

    // Pitch (俯仰) PID参数 - 控制前后倾斜
    double kp_pitch = 10.0;
    double kd_pitch = 1.0;
    double ki_pitch = 0.0;

    // Yaw (偏航) PID参数 - 控制转向
    double kp_yaw = 5.0;
    double kd_yaw = 0.5;
    double ki_yaw = 0.0;

    // 输出限制
    double max_torque = 50.0;    // 最大力矩 (Nm)
    double max_velocity = 10.0;  // 最大速度 (rad/s)

    // 控制选项
    bool enable_integration = false;      // 是否启用积分项
    bool enable_adaptive_gain = false;    // 是否启用自适应增益
};

/**
 * @brief 平衡算法基类
 * @details 提供算法的统一接口，子类必须实现以下方法:
 *   - reset(): 重置算法状态
 *   - computeControl(): 计算控制输出
 *   - getName(): 返回算法名称
 */
class BalanceAlgorithm {
public:
    virtual ~BalanceAlgorithm() = default;

    /**
     * @brief 重置算法内部状态
     * @details 调用后清除积分项、误差历史等
     */
    virtual void reset() = 0;

    /**
     * @brief 计算控制输出
     * @param state 当前状态向量 [roll, pitch, yaw, omega_x, omega_y, omega_z]
     * @param target 目标状态向量
     * @param output 计算出的控制输出 (力矩)
     */
    virtual void computeControl(const Eigen::VectorXd& state,
                                const Eigen::VectorXd& target,
                                Eigen::VectorXd& output) = 0;

    /**
     * @brief 获取算法名称
     * @return 算法名称字符串
     */
    virtual std::string getName() const = 0;

    /**
     * @brief 设置算法参数
     * @param params 算法参数结构体
     */
    void setParams(const AlgorithmParams& params) { params_ = params; }

    /**
     * @brief 获取当前参数
     * @return 算法参数结构体
     */
    AlgorithmParams getParams() const { return params_; }

protected:
    AlgorithmParams params_;           // 算法参数
    Eigen::VectorXd state_error_;      // 状态误差向量
};

} // namespace balance_control

#endif // BALANCE_ALGORITHM_BASE_H