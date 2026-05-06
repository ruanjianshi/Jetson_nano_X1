/*
 * Robot Command Client Implementation
 * ===================================
 * 
 * Author: Qi Xiao
Email: 2408128687@qq.com
 * 日期: 2026-05-06
 */

#include "robot_command_client.h"
#include <ros/ros.h>

namespace balance_control {

RobotCommandClient::RobotCommandClient(ros::NodeHandle& nh)
    : nh_(nh)
    , action_client_("balance_control", true)
    , command_(RobotCommandType::STOP)
    , speed_(0.0)
    , yaw_rate_(0.0)
    , jump_height_(0.0)
    , duration_(0.0)
    , continuous_mode_(false)
    , cmd_vel_enabled_(false)
{
    // ========== 获取参数 ==========
    int command_int = 0;
    nh.param("command", command_int, 0);
    command_ = static_cast<RobotCommandType>(command_int);
    nh.param("speed", speed_, 0.0);
    nh.param("yaw_rate", yaw_rate_, 0.0);
    nh.param("jump_height", jump_height_, 0.0);
    nh.param("duration", duration_, 0.0);
    nh.param("continuous", continuous_mode_, false);

    // ========== 初始化关节配置 ==========
    joint_configs_.push_back({"joint_left_leg_1", 0, 0});
    joint_configs_.push_back({"joint_left_leg_2", 0, 1});
    joint_configs_.push_back({"joint_left_leg_3", 0, 2});
    joint_configs_.push_back({"joint_left_leg_4", 0, 3});
    joint_configs_.push_back({"joint_right_leg_1", 1, 0});
    joint_configs_.push_back({"joint_right_leg_2", 1, 1});
    joint_configs_.push_back({"joint_right_leg_3", 1, 2});
    joint_configs_.push_back({"joint_right_leg_4", 1, 3});

    // ========== 等待Action Server ==========
    ROS_INFO("等待 Balance Control Action Server...");

    if (!action_client_.waitForServer(ros::Duration(10.0))) {
        ROS_ERROR("无法连接到 Action Server!");
        return;
    }

    ROS_INFO("已连接到 Action Server");
    ROS_INFO("==========================================");

    // ========== 如果是持续模式，订阅cmd_vel ==========
    if (continuous_mode_) {
        cmd_vel_sub_ = nh.subscribe("/cmd_vel", 10,
                                    &RobotCommandClient::cmdVelCallback, this);
        cmd_vel_enabled_ = true;
        ROS_INFO("订阅 /cmd_vel 话题 (持续模式)");
    }

    // ========== 发送初始命令 ==========
    sendCommand(command_, speed_, yaw_rate_, jump_height_, duration_);

    // ========== 如果不是持续模式，则完成后退出 ==========
    if (!continuous_mode_) {
        ROS_INFO("命令已发送，客户端将退出");
        return;
    }

    // ========== 持续模式主循环 ==========
    ROS_INFO("进入持续控制模式...");
    ros::Rate rate(10);  // 10Hz

    while (ros::ok()) {
        ros::spinOnce();
        rate.sleep();
    }

    // 退出前发送停止命令
    sendStop();
    ROS_INFO("客户端退出");
}

RobotCommandClient::~RobotCommandClient() {
    if (cmd_vel_enabled_) {
        cmd_vel_sub_.shutdown();
    }
}

void RobotCommandClient::cmdVelCallback(const geometry_msgs::Twist::ConstPtr& msg) {
    // 从 cmd_vel 提取速度
    // 注意: 机器人坐标系中前进方向是-Y
    double forward_speed = -msg->linear.x;
    double lateral_speed = msg->linear.y;
    double yaw_rate = msg->angular.z;

    // 判断命令类型
    RobotCommandType command = RobotCommandType::FORWARD;
    double speed = 0.0;

    if (std::abs(forward_speed) > 0.01) {
        command = (forward_speed > 0) ? RobotCommandType::FORWARD : RobotCommandType::BACKWARD;
        speed = std::abs(forward_speed);
    } else if (std::abs(lateral_speed) > 0.01) {
        command = (lateral_speed > 0) ? RobotCommandType::STRAFE_RIGHT : RobotCommandType::STRAFE_LEFT;
        speed = std::abs(lateral_speed);
    } else if (std::abs(yaw_rate) > 0.01) {
        command = (yaw_rate > 0) ? RobotCommandType::TURN_LEFT : RobotCommandType::TURN_RIGHT;
        speed = std::abs(yaw_rate);
    } else {
        command = RobotCommandType::STOP;
        speed = 0.0;
    }

    sendCommand(command, speed, yaw_rate, 0.0, 0.0);
}

TargetOrientation RobotCommandClient::computeTargetOrientation(
    RobotCommandType command, double speed, double yaw_rate) {

    TargetOrientation target = {0.0, 0.0, 0.0};

    switch (command) {
        case RobotCommandType::FORWARD:
            // 前进: 身体微微前倾，角度与速度成正比
            target.pitch = -speed * 0.15;  // 最大约 -0.3 rad (约17度)
            break;

        case RobotCommandType::BACKWARD:
            // 后退: 身体微微后仰
            target.pitch = speed * 0.15;
            break;

        case RobotCommandType::TURN_LEFT:
            // 左转: 身体微微右倾，帮助转向
            target.roll = yaw_rate * 0.1;
            target.yaw = yaw_rate * 0.5;  // 直接控制偏航
            break;

        case RobotCommandType::TURN_RIGHT:
            // 右转: 身体微微左倾
            target.roll = -yaw_rate * 0.1;
            target.yaw = -yaw_rate * 0.5;
            break;

        case RobotCommandType::STRAFE_LEFT:
            // 左侧向: 身体微微右倾
            target.roll = 0.1;
            break;

        case RobotCommandType::STRAFE_RIGHT:
            // 右侧向: 身体微微左倾
            target.roll = -0.1;
            break;

        case RobotCommandType::STOP:
            // 停止: 回到中立姿态
            target.roll = 0.0;
            target.pitch = 0.0;
            target.yaw = 0.0;
            break;

        case RobotCommandType::JUMP:
            // 跳跃: 身体微微下蹲准备
            target.pitch = -0.2;
            break;

        case RobotCommandType::BALANCE:
            // 平衡模式: 保持当前姿态
            break;
    }

    return target;
}

void RobotCommandClient::sendCommand(RobotCommandType command, double speed,
                                     double yaw_rate, double jump_height, double duration) {
    // 计算目标姿态
    TargetOrientation target = computeTargetOrientation(command, speed, yaw_rate);

    // 创建 Action Goal
    balance_control::BalanceControlGoal goal;
    goal.enable_control = true;
    goal.algorithm_id = 0;  // 0=LQR, 1=VMC, 2=MPC
    goal.target_roll = target.roll;
    goal.target_pitch = target.pitch;
    goal.target_yaw = target.yaw;

    // 发送目标
    action_client_.sendGoal(goal);

    // 打印命令信息
    ROS_INFO("==========================================");
    ROS_INFO("发送命令: %s", commandToString(command).c_str());
    ROS_INFO("  速度: %.2f m/s", speed);
    ROS_INFO("  转向: %.2f rad/s", yaw_rate);
    ROS_INFO("  目标姿态: roll=%.3f, pitch=%.3f, yaw=%.3f",
             target.roll, target.pitch, target.yaw);
    ROS_INFO("==========================================");

    // 如果不是持续命令，等待结果
    if (duration > 0) {
        ros::Duration(duration).sleep();
        sendStop();
    }
}

void RobotCommandClient::sendStop() {
    balance_control::BalanceControlGoal goal;
    goal.enable_control = false;
    action_client_.sendGoal(goal);
    ROS_INFO("发送停止命令");
}

void RobotCommandClient::sendEnable() {
    balance_control::BalanceControlGoal goal;
    goal.enable_control = true;
    action_client_.sendGoal(goal);
    ROS_INFO("发送启用命令");
}

void RobotCommandClient::sendTarget(double roll, double pitch, double yaw) {
    balance_control::BalanceControlGoal goal;
    goal.enable_control = true;
    goal.target_roll = roll;
    goal.target_pitch = pitch;
    goal.target_yaw = yaw;
    action_client_.sendGoal(goal);
    ROS_INFO("发送目标姿态: roll=%.3f, pitch=%.3f, yaw=%.3f", roll, pitch, yaw);
}

void RobotCommandClient::setCmdVelEnabled(bool enabled) {
    cmd_vel_enabled_ = enabled;
    if (enabled && !cmd_vel_sub_) {
        cmd_vel_sub_ = nh_.subscribe("/cmd_vel", 10,
                                     &RobotCommandClient::cmdVelCallback, this);
    }
}

std::string RobotCommandClient::commandToString(RobotCommandType command) {
    switch (command) {
        case RobotCommandType::STOP: return "STOP";
        case RobotCommandType::FORWARD: return "FORWARD";
        case RobotCommandType::BACKWARD: return "BACKWARD";
        case RobotCommandType::TURN_LEFT: return "TURN_LEFT";
        case RobotCommandType::TURN_RIGHT: return "TURN_RIGHT";
        case RobotCommandType::STRAFE_LEFT: return "STRAFE_LEFT";
        case RobotCommandType::STRAFE_RIGHT: return "STRAFE_RIGHT";
        case RobotCommandType::JUMP: return "JUMP";
        case RobotCommandType::BALANCE: return "BALANCE";
        default: return "UNKNOWN";
    }
}

} // namespace balance_control

/*
 * Main Entry Point
 * ================
 */
int main(int argc, char** argv) {
    ros::init(argc, argv, "robot_command_client");

    try {
        ros::NodeHandle nh;
        balance_control::RobotCommandClient client(nh);
    } catch (const std::exception& e) {
        ROS_ERROR("异常: %s", e.what());
        return 1;
    }

    return 0;
}