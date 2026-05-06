/*
 * Robot Command Client (C++)
 * ==========================
 * 
 * 功能说明:
 *   - 提供高层运动命令接口 (前进、后退、转向、跳跃等)
 *   - 将高层命令转换为底层平衡控制目标
 *   - 支持持续发送和一次性命令
 * 
 * 命令类型:
 *   - STOP (0): 停止移动
 *   - FORWARD (1): 前进
 *   - BACKWARD (2): 后退
 *   - TURN_LEFT (3): 左转
 *   - TURN_RIGHT (4): 右转
 *   - STRAFE_LEFT (5): 左侧向移动
 *   - STRAFE_RIGHT (6): 右侧向移动
 *   - JUMP (7): 跳跃
 *   - BALANCE (8): 进入平衡模式
 * 
 * 使用示例:
 *   rosrun balance_control robot_command_client _command:=1 _speed:=0.5
 *   rosrun balance_control robot_command_client _command:=3 _yaw_rate:=1.0
 *   rosrun balance_control robot_command_client _continuous:=true
 * 
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#ifndef ROBOT_COMMAND_CLIENT_H
#define ROBOT_COMMAND_CLIENT_H

#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <balance_control/BalanceControlAction.h>
#include <geometry_msgs/Twist.h>
#include <std_msgs/Float64.h>
#include <vector>
#include <string>

namespace balance_control {

/**
 * @brief 命令类型枚举
 */
enum class RobotCommandType {
    STOP = 0,
    FORWARD = 1,
    BACKWARD = 2,
    TURN_LEFT = 3,
    TURN_RIGHT = 4,
    STRAFE_LEFT = 5,
    STRAFE_RIGHT = 6,
    JUMP = 7,
    BALANCE = 8
};

/**
 * @brief 关节配置
 */
struct JointConfig {
    std::string name;
    uint8_t leg;       // 0=左, 1=右
    uint8_t index;     // 0=HIP_ROLL, 1=HIP_PITCH, 2=KNEE_PITCH, 3=WHEEL
};

/**
 * @brief 目标姿态结构
 */
struct TargetOrientation {
    double roll;
    double pitch;
    double yaw;
};

/**
 * @brief 机器人命令客户端类
 * 
 * 功能:
 *   - 订阅 /cmd_vel 话题获取运动命令 (可选)
 *   - 将运动命令转换为平衡控制目标
 *   - 通过 Action 接口发送控制目标
 * 
 * 坐标系 (B frame):
 *   - X轴: 指向机器人右侧
 *   - Y轴: 指向机器人后方 (前进方向为-Y)
 *   - Z轴: 指向上方
 */
class RobotCommandClient {
public:
    /**
     * @brief 构造函数
     * @param nh ROS节点句柄
     */
    explicit RobotCommandClient(ros::NodeHandle& nh);

    /**
     * @brief 析构函数
     */
    ~RobotCommandClient();

    /**
     * @brief 发送命令
     * @param command 命令类型
     * @param speed 速度 m/s (0.0 ~ 2.0)
     * @param yaw_rate 偏航角速度 rad/s (0.0 ~ 3.14)
     * @param jump_height 跳跃高度 m (0.0 ~ 0.5)
     * @param duration 持续时间 s (0.0 = 持续)
     */
    void sendCommand(RobotCommandType command, double speed, double yaw_rate,
                     double jump_height = 0.0, double duration = 0.0);

    /**
     * @brief 发送停止命令
     */
    void sendStop();

    /**
     * @brief 发送启用平衡控制命令
     */
    void sendEnable();

    /**
     * @brief 发送目标姿态
     * @param roll 目标横滚角 (rad)
     * @param pitch 目标俯仰角 (rad)
     * @param yaw 目标偏航角 (rad)
     */
    void sendTarget(double roll, double pitch, double yaw);

    /**
     * @brief 订阅 /cmd_vel 话题进入持续模式
     * @param enabled 是否启用
     */
    void setCmdVelEnabled(bool enabled);

private:
    /**
     * @brief cmd_vel回调
     * @param msg Twist消息
     */
    void cmdVelCallback(const geometry_msgs::Twist::ConstPtr& msg);

    /**
     * @brief 根据命令计算目标姿态
     * @param command 命令类型
     * @param speed 速度
     * @param yaw_rate 转向角速度
     * @return 目标姿态
     */
    TargetOrientation computeTargetOrientation(RobotCommandType command,
                                                double speed, double yaw_rate);

    /**
     * @brief 将命令转换为字符串
     * @param command 命令类型
     * @return 命令名称
     */
    std::string commandToString(RobotCommandType command);

    // ROS接口
    ros::NodeHandle& nh_;
    actionlib::SimpleActionClient<balance_control::BalanceControlAction> action_client_;
    ros::Subscriber cmd_vel_sub_;

    // 参数
    RobotCommandType command_;
    double speed_;
    double yaw_rate_;
    double jump_height_;
    double duration_;
    bool continuous_mode_;

    // 关节配置
    std::vector<JointConfig> joint_configs_;

    // 控制启用标志
    bool cmd_vel_enabled_;
};

} // namespace balance_control

#endif // ROBOT_COMMAND_CLIENT_H