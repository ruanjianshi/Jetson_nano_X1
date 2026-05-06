/*
 * Robot Hardware Parameters Implementation
 * ========================================
 *
 * 功能说明:
 *   - 从YAML文件或ROS参数服务器加载硬件参数
 *   - 提供统一的参数访问接口
 *   - 支持参数的动态修改
 *
 * 使用方法:
 *   RobotHardwareParams params;
 *   params.loadFromYaml("/path/to/config.yaml");
 *   params.loadFromParamServer(nh);
 *
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#include "robot_hardware_params.h"
#include <ros/ros.h>
#include <yaml-cpp/yaml.h>
#include <cmath>

namespace balance_control {

RobotHardwareParams::RobotHardwareParams() {
    initDefaultParams();
}

void RobotHardwareParams::initDefaultParams() {
    // ========== 机器人基本信息 ==========
    robot_name_ = "wheeled_legged_robot";
    robot_type_ = "biped_wheeled";
    mass_ = 15.0;
    gravity_ = 9.81;

    // ========== 腿部几何 ==========
    leg_geometry_.upper_leg_length = 0.20;
    leg_geometry_.lower_leg_length = 0.20;
    leg_geometry_.hip_offset_x = 0.10;
    leg_geometry_.hip_offset_y = 0.0;
    leg_geometry_.hip_offset_z = 0.0;
    leg_geometry_.leg_length_min = 0.20;
    leg_geometry_.leg_length_max = 0.40;
    leg_geometry_.foot_height_min = -0.30;
    leg_geometry_.foot_height_max = 0.20;

    // ========== 轮子配置 ==========
    wheel_config_.radius = 0.10;
    wheel_config_.width = 0.08;
    wheel_config_.wheel_base = 0.40;
    wheel_config_.max_wheel_speed = 30.0;
    wheel_config_.driver_kp = 20.0;
    wheel_config_.driver_kd = 2.0;

    // ========== IMU配置 ==========
    imu_config_.position_x = 0.0;
    imu_config_.position_y = 0.0;
    imu_config_.position_z = 0.15;
    imu_config_.rotation_roll = 0.0;
    imu_config_.rotation_pitch = 0.0;
    imu_config_.rotation_yaw = 0.0;
    imu_config_.neutral_roll = 0.0;
    imu_config_.neutral_pitch = 0.0;
    imu_config_.neutral_yaw = 0.0;
    imu_config_.balance_roll_max = 0.52;   // 约30度
    imu_config_.balance_pitch_max = 0.52;
    imu_config_.balance_yaw_max = 3.14;

    // ========== R86电机限幅 ==========
    r86_limits_.max_torque = 100.0;
    r86_limits_.max_velocity = 37.7;
    r86_limits_.position_min = -6.28;
    r86_limits_.position_max = 6.28;
    r86_limits_.kp_default = 20.0;
    r86_limits_.kd_default = 2.0;

    // ========== R52电机限幅 ==========
    r52_limits_.max_torque = 50.0;
    r52_limits_.max_velocity = 25.1;
    r52_limits_.position_min = -6.28;
    r52_limits_.position_max = 6.28;
    r52_limits_.kp_default = 15.0;
    r52_limits_.kd_default = 1.5;

    // ========== 电机配置 (8个电机) ==========
    // 左腿 (4个电机)
    motor_configs_.push_back({"joint_left_leg_1", 3, 1, "POWER_FLOW_R86", "hip_roll", 1});
    motor_configs_.push_back({"joint_left_leg_2", 3, 1, "POWER_FLOW_R86", "hip_pitch", 1});
    motor_configs_.push_back({"joint_left_leg_3", 3, 2, "POWER_FLOW_R52", "knee_pitch", 1});
    motor_configs_.push_back({"joint_left_leg_4", 3, 2, "POWER_FLOW_R52", "wheel", 1});

    // 右腿 (4个电机)
    motor_configs_.push_back({"joint_right_leg_1", 2, 1, "POWER_FLOW_R86", "hip_roll", -1});
    motor_configs_.push_back({"joint_right_leg_2", 2, 1, "POWER_FLOW_R86", "hip_pitch", 1});
    motor_configs_.push_back({"joint_right_leg_3", 5, 2, "POWER_FLOW_R52", "knee_pitch", 1});
    motor_configs_.push_back({"joint_right_leg_4", 5, 2, "POWER_FLOW_R52", "wheel", 1});

    // ========== 控制参数 ==========
    control_params_.control_frequency = 500;
    control_params_.ethercat_if = "eth0";
    control_params_.cycle_ns = 2000000;
    control_params_.enable_dc = false;
    control_params_.default_mode = "MIT";
    control_params_.emergency_stop_threshold = 150.0;

    // ========== PID参数 ==========
    pid_params_.kp_roll = 10.0;
    pid_params_.kd_roll = 1.0;
    pid_params_.ki_roll = 0.0;
    pid_params_.kp_pitch = 10.0;
    pid_params_.kd_pitch = 1.0;
    pid_params_.ki_pitch = 0.0;
    pid_params_.kp_yaw = 5.0;
    pid_params_.kd_yaw = 0.5;
    pid_params_.ki_yaw = 0.0;

    // ========== 关节软限位 ==========
    joint_limits_.hip_roll_min = -1.57;
    joint_limits_.hip_roll_max = 1.57;
    joint_limits_.hip_pitch_min = -1.57;
    joint_limits_.hip_pitch_max = 1.57;
    joint_limits_.knee_pitch_min = -2.35;
    joint_limits_.knee_pitch_max = 0.0;
    joint_limits_.wheel_min = -50.0;
    joint_limits_.wheel_max = 50.0;

    // ========== 标零位置 ==========
    joint_home_.hip_roll = 0.0;
    joint_home_.hip_pitch = 0.0;
    joint_home_.knee_pitch = 0.0;
    joint_home_.wheel = 0.0;
    joint_home_.hip_roll_offset = 0.0;
    joint_home_.hip_pitch_offset = 0.0;
    joint_home_.knee_pitch_offset = 0.0;
    joint_home_.wheel_offset = 0.0;

    // ========== 目标姿态 ==========
    target_pose_.roll = 0.0;
    target_pose_.pitch = 0.0;
    target_pose_.yaw = 0.0;

    // ========== 算法 ==========
    algorithm_ = "LQR";
    max_torque_ = 50.0;
    max_velocity_ = 10.0;
}

void RobotHardwareParams::loadFromParamServer(ros::NodeHandle& nh,
                                               const std::string& namespace_prefix) {
    std::string ns = namespace_prefix.empty() ? "" : namespace_prefix + "/";

    // ========== 加载机器人基本信息 ==========
    nh.param(ns + "robot/name", robot_name_, robot_name_);
    nh.param(ns + "robot/type", robot_type_, robot_type_);
    nh.param(ns + "robot/mass", mass_, mass_);
    nh.param(ns + "robot/gravity", gravity_, gravity_);

    // ========== 加载腿部几何 ==========
    nh.param(ns + "leg/upper_leg_length", leg_geometry_.upper_leg_length, leg_geometry_.upper_leg_length);
    nh.param(ns + "leg/lower_leg_length", leg_geometry_.lower_leg_length, leg_geometry_.lower_leg_length);
    nh.param(ns + "leg/hip_offset_x", leg_geometry_.hip_offset_x, leg_geometry_.hip_offset_x);
    nh.param(ns + "leg/hip_offset_y", leg_geometry_.hip_offset_y, leg_geometry_.hip_offset_y);
    nh.param(ns + "leg/hip_offset_z", leg_geometry_.hip_offset_z, leg_geometry_.hip_offset_z);
    nh.param(ns + "leg/leg_length_min", leg_geometry_.leg_length_min, leg_geometry_.leg_length_min);
    nh.param(ns + "leg/leg_length_max", leg_geometry_.leg_length_max, leg_geometry_.leg_length_max);
    nh.param(ns + "leg/foot_height_min", leg_geometry_.foot_height_min, leg_geometry_.foot_height_min);
    nh.param(ns + "leg/foot_height_max", leg_geometry_.foot_height_max, leg_geometry_.foot_height_max);

    // ========== 加载轮子配置 ==========
    nh.param(ns + "wheel/radius", wheel_config_.radius, wheel_config_.radius);
    nh.param(ns + "wheel/width", wheel_config_.width, wheel_config_.width);
    nh.param(ns + "wheel/wheel_base", wheel_config_.wheel_base, wheel_config_.wheel_base);
    nh.param(ns + "wheel/max_wheel_speed", wheel_config_.max_wheel_speed, wheel_config_.max_wheel_speed);
    nh.param(ns + "wheel/wheel_driver_kp", wheel_config_.driver_kp, wheel_config_.driver_kp);
    nh.param(ns + "wheel/wheel_driver_kd", wheel_config_.driver_kd, wheel_config_.driver_kd);

    // ========== 加载IMU配置 ==========
    nh.param(ns + "imu/position_x", imu_config_.position_x, imu_config_.position_x);
    nh.param(ns + "imu/position_y", imu_config_.position_y, imu_config_.position_y);
    nh.param(ns + "imu/position_z", imu_config_.position_z, imu_config_.position_z);
    nh.param(ns + "imu/rotation_roll", imu_config_.rotation_roll, imu_config_.rotation_roll);
    nh.param(ns + "imu/rotation_pitch", imu_config_.rotation_pitch, imu_config_.rotation_pitch);
    nh.param(ns + "imu/rotation_yaw", imu_config_.rotation_yaw, imu_config_.rotation_yaw);
    nh.param(ns + "imu/neutral_pose/roll", imu_config_.neutral_roll, imu_config_.neutral_roll);
    nh.param(ns + "imu/neutral_pose/pitch", imu_config_.neutral_pitch, imu_config_.neutral_pitch);
    nh.param(ns + "imu/neutral_pose/yaw", imu_config_.neutral_yaw, imu_config_.neutral_yaw);
    nh.param(ns + "imu/balance_range/roll_max", imu_config_.balance_roll_max, imu_config_.balance_roll_max);
    nh.param(ns + "imu/balance_range/pitch_max", imu_config_.balance_pitch_max, imu_config_.balance_pitch_max);
    nh.param(ns + "imu/balance_range/yaw_max", imu_config_.balance_yaw_max, imu_config_.balance_yaw_max);

    // ========== 加载电机限幅参数 ==========
    // R86
    nh.param(ns + "motor_limits/r86/max_torque", r86_limits_.max_torque, r86_limits_.max_torque);
    nh.param(ns + "motor_limits/r86/max_velocity", r86_limits_.max_velocity, r86_limits_.max_velocity);
    nh.param(ns + "motor_limits/r86/position_min", r86_limits_.position_min, r86_limits_.position_min);
    nh.param(ns + "motor_limits/r86/position_max", r86_limits_.position_max, r86_limits_.position_max);
    nh.param(ns + "motor_limits/r86/kp_default", r86_limits_.kp_default, r86_limits_.kp_default);
    nh.param(ns + "motor_limits/r86/kd_default", r86_limits_.kd_default, r86_limits_.kd_default);

    // R52
    nh.param(ns + "motor_limits/r52/max_torque", r52_limits_.max_torque, r52_limits_.max_torque);
    nh.param(ns + "motor_limits/r52/max_velocity", r52_limits_.max_velocity, r52_limits_.max_velocity);
    nh.param(ns + "motor_limits/r52/position_min", r52_limits_.position_min, r52_limits_.position_min);
    nh.param(ns + "motor_limits/r52/position_max", r52_limits_.position_max, r52_limits_.position_max);
    nh.param(ns + "motor_limits/r52/kp_default", r52_limits_.kp_default, r52_limits_.kp_default);
    nh.param(ns + "motor_limits/r52/kd_default", r52_limits_.kd_default, r52_limits_.kd_default);

    // ========== 加载电机配置 ==========
    XmlRpc::XmlRpcValue motor_list;
    if (nh.getParam(ns + "motors", motor_list)) {
        motor_configs_.clear();
        for (int i = 0; i < motor_list.size(); ++i) {
            MotorConfig config;
            config.name = static_cast<std::string>(motor_list[i]["name"]);
            config.motor_id = static_cast<int>(motor_list[i]["motor_id"]);
            config.channel = static_cast<int>(motor_list[i]["channel"]);
            config.motor_type = static_cast<std::string>(motor_list[i]["motor_type"]);
            config.joint_type = static_cast<std::string>(motor_list[i]["joint_type"]);
            config.direction = static_cast<int>(motor_list[i]["direction"]);
            motor_configs_.push_back(config);
        }
    }

    // ========== 加载关节软限位 ==========
    nh.param(ns + "joint_soft_limits/hip_roll/min", joint_limits_.hip_roll_min, joint_limits_.hip_roll_min);
    nh.param(ns + "joint_soft_limits/hip_roll/max", joint_limits_.hip_roll_max, joint_limits_.hip_roll_max);
    nh.param(ns + "joint_soft_limits/hip_pitch/min", joint_limits_.hip_pitch_min, joint_limits_.hip_pitch_min);
    nh.param(ns + "joint_soft_limits/hip_pitch/max", joint_limits_.hip_pitch_max, joint_limits_.hip_pitch_max);
    nh.param(ns + "joint_soft_limits/knee_pitch/min", joint_limits_.knee_pitch_min, joint_limits_.knee_pitch_min);
    nh.param(ns + "joint_soft_limits/knee_pitch/max", joint_limits_.knee_pitch_max, joint_limits_.knee_pitch_max);
    nh.param(ns + "joint_soft_limits/wheel/min", joint_limits_.wheel_min, joint_limits_.wheel_min);
    nh.param(ns + "joint_soft_limits/wheel/max", joint_limits_.wheel_max, joint_limits_.wheel_max);

    // ========== 加载标零位置 ==========
    nh.param(ns + "joint_home/hip_roll", joint_home_.hip_roll, joint_home_.hip_roll);
    nh.param(ns + "joint_home/hip_pitch", joint_home_.hip_pitch, joint_home_.hip_pitch);
    nh.param(ns + "joint_home/knee_pitch", joint_home_.knee_pitch, joint_home_.knee_pitch);
    nh.param(ns + "joint_home/wheel", joint_home_.wheel, joint_home_.wheel);
    nh.param(ns + "joint_home/hip_roll_offset", joint_home_.hip_roll_offset, joint_home_.hip_roll_offset);
    nh.param(ns + "joint_home/hip_pitch_offset", joint_home_.hip_pitch_offset, joint_home_.hip_pitch_offset);
    nh.param(ns + "joint_home/knee_pitch_offset", joint_home_.knee_pitch_offset, joint_home_.knee_pitch_offset);
    nh.param(ns + "joint_home/wheel_offset", joint_home_.wheel_offset, joint_home_.wheel_offset);

    // ========== 加载控制参数 ==========
    nh.param(ns + "control/control_frequency", control_params_.control_frequency, control_params_.control_frequency);
    nh.param(ns + "control/ethercat/interface", control_params_.ethercat_if, control_params_.ethercat_if);
    int cycle_ns_int;
    nh.param(ns + "control/ethercat/cycle_ns", cycle_ns_int, (int)control_params_.cycle_ns);
    control_params_.cycle_ns = cycle_ns_int;
    nh.param(ns + "control/ethercat/enable_dc", control_params_.enable_dc, control_params_.enable_dc);
    nh.param(ns + "control/default_mode", control_params_.default_mode, control_params_.default_mode);
    nh.param(ns + "control/safety/emergency_stop_threshold", control_params_.emergency_stop_threshold, control_params_.emergency_stop_threshold);

    // ========== 加载PID参数 ==========
    nh.param(ns + "balance/pid/kp_roll", pid_params_.kp_roll, pid_params_.kp_roll);
    nh.param(ns + "balance/pid/kd_roll", pid_params_.kd_roll, pid_params_.kd_roll);
    nh.param(ns + "balance/pid/ki_roll", pid_params_.ki_roll, pid_params_.ki_roll);
    nh.param(ns + "balance/pid/kp_pitch", pid_params_.kp_pitch, pid_params_.kp_pitch);
    nh.param(ns + "balance/pid/kd_pitch", pid_params_.kd_pitch, pid_params_.kd_pitch);
    nh.param(ns + "balance/pid/ki_pitch", pid_params_.ki_pitch, pid_params_.ki_pitch);
    nh.param(ns + "balance/pid/kp_yaw", pid_params_.kp_yaw, pid_params_.kp_yaw);
    nh.param(ns + "balance/pid/kd_yaw", pid_params_.kd_yaw, pid_params_.kd_yaw);
    nh.param(ns + "balance/pid/ki_yaw", pid_params_.ki_yaw, pid_params_.ki_yaw);

    // ========== 加载目标姿态 ==========
    nh.param(ns + "balance/target_pose/roll", target_pose_.roll, target_pose_.roll);
    nh.param(ns + "balance/target_pose/pitch", target_pose_.pitch, target_pose_.pitch);
    nh.param(ns + "balance/target_pose/yaw", target_pose_.yaw, target_pose_.yaw);

    // ========== 加载算法配置 ==========
    nh.param(ns + "balance/algorithm", algorithm_, algorithm_);
    nh.param(ns + "balance/max_torque", max_torque_, max_torque_);
    nh.param(ns + "balance/max_velocity", max_velocity_, max_velocity_);

    ROS_INFO("[HardwareParams] Loaded from parameter server");
    printSummary();
}

void RobotHardwareParams::loadFromYaml(const std::string& file_path) {
    // 使用YAML方式加载
    YAML::Node config = YAML::LoadFile(file_path);

    if (!config) {
        ROS_WARN("[HardwareParams] Cannot load YAML file: %s", file_path.c_str());
        return;
    }

    // 加载机器人基本信息
    if (config["robot"]) {
        robot_name_ = config["robot"]["name"].as<std::string>(robot_name_);
        robot_type_ = config["robot"]["type"].as<std::string>(robot_type_);
        mass_ = config["robot"]["mass"].as<double>(mass_);
        gravity_ = config["robot"]["gravity"].as<double>(gravity_);
    }

    // 加载腿部几何
    if (config["leg"]) {
        leg_geometry_.upper_leg_length = config["leg"]["upper_leg_length"].as<double>(leg_geometry_.upper_leg_length);
        leg_geometry_.lower_leg_length = config["leg"]["lower_leg_length"].as<double>(leg_geometry_.lower_leg_length);
        leg_geometry_.hip_offset_x = config["leg"]["hip_offset_x"].as<double>(leg_geometry_.hip_offset_x);
        leg_geometry_.hip_offset_y = config["leg"]["hip_offset_y"].as<double>(leg_geometry_.hip_offset_y);
        leg_geometry_.hip_offset_z = config["leg"]["hip_offset_z"].as<double>(leg_geometry_.hip_offset_z);
        leg_geometry_.leg_length_min = config["leg"]["leg_length_min"].as<double>(leg_geometry_.leg_length_min);
        leg_geometry_.leg_length_max = config["leg"]["leg_length_max"].as<double>(leg_geometry_.leg_length_max);
    }

    // 加载轮子配置
    if (config["wheel"]) {
        wheel_config_.radius = config["wheel"]["radius"].as<double>(wheel_config_.radius);
        wheel_config_.width = config["wheel"]["width"].as<double>(wheel_config_.width);
        wheel_config_.wheel_base = config["wheel"]["wheel_base"].as<double>(wheel_config_.wheel_base);
        wheel_config_.max_wheel_speed = config["wheel"]["max_wheel_speed"].as<double>(wheel_config_.max_wheel_speed);
    }

    // 加载IMU配置
    if (config["imu"]) {
        imu_config_.position_x = config["imu"]["position_x"].as<double>(imu_config_.position_x);
        imu_config_.position_y = config["imu"]["position_y"].as<double>(imu_config_.position_y);
        imu_config_.position_z = config["imu"]["position_z"].as<double>(imu_config_.position_z);
        if (config["imu"]["neutral_pose"]) {
            imu_config_.neutral_roll = config["imu"]["neutral_pose"]["roll"].as<double>(imu_config_.neutral_roll);
            imu_config_.neutral_pitch = config["imu"]["neutral_pose"]["pitch"].as<double>(imu_config_.neutral_pitch);
            imu_config_.neutral_yaw = config["imu"]["neutral_pose"]["yaw"].as<double>(imu_config_.neutral_yaw);
        }
        if (config["imu"]["balance_range"]) {
            imu_config_.balance_roll_max = config["imu"]["balance_range"]["roll_max"].as<double>(imu_config_.balance_roll_max);
            imu_config_.balance_pitch_max = config["imu"]["balance_range"]["pitch_max"].as<double>(imu_config_.balance_pitch_max);
            imu_config_.balance_yaw_max = config["imu"]["balance_range"]["yaw_max"].as<double>(imu_config_.balance_yaw_max);
        }
    }

    // 加载电机配置
    if (config["motors"]) {
        motor_configs_.clear();
        for (const auto& motor : config["motors"]) {
            MotorConfig cfg;
            cfg.name = motor["name"].as<std::string>();
            cfg.motor_id = motor["motor_id"].as<int>();
            cfg.channel = motor["channel"].as<int>();
            cfg.motor_type = motor["motor_type"].as<std::string>();
            cfg.joint_type = motor["joint_type"].as<std::string>();
            cfg.direction = motor["direction"].as<int>();
            motor_configs_.push_back(cfg);
        }
    }

    // 加载电机限幅
    if (config["motor_limits"]) {
        if (config["motor_limits"]["r86"]) {
            r86_limits_.max_torque = config["motor_limits"]["r86"]["max_torque"].as<double>(r86_limits_.max_torque);
            r86_limits_.max_velocity = config["motor_limits"]["r86"]["max_velocity"].as<double>(r86_limits_.max_velocity);
            r86_limits_.kp_default = config["motor_limits"]["r86"]["kp_default"].as<double>(r86_limits_.kp_default);
            r86_limits_.kd_default = config["motor_limits"]["r86"]["kd_default"].as<double>(r86_limits_.kd_default);
        }
        if (config["motor_limits"]["r52"]) {
            r52_limits_.max_torque = config["motor_limits"]["r52"]["max_torque"].as<double>(r52_limits_.max_torque);
            r52_limits_.max_velocity = config["motor_limits"]["r52"]["max_velocity"].as<double>(r52_limits_.max_velocity);
            r52_limits_.kp_default = config["motor_limits"]["r52"]["kp_default"].as<double>(r52_limits_.kp_default);
            r52_limits_.kd_default = config["motor_limits"]["r52"]["kd_default"].as<double>(r52_limits_.kd_default);
        }
    }

    // 加载PID参数
    if (config["balance"] && config["balance"]["pid"]) {
        pid_params_.kp_roll = config["balance"]["pid"]["kp_roll"].as<double>(pid_params_.kp_roll);
        pid_params_.kd_roll = config["balance"]["pid"]["kd_roll"].as<double>(pid_params_.kd_roll);
        pid_params_.ki_roll = config["balance"]["pid"]["ki_roll"].as<double>(pid_params_.ki_roll);
        pid_params_.kp_pitch = config["balance"]["pid"]["kp_pitch"].as<double>(pid_params_.kp_pitch);
        pid_params_.kd_pitch = config["balance"]["pid"]["kd_pitch"].as<double>(pid_params_.kd_pitch);
        pid_params_.ki_pitch = config["balance"]["pid"]["ki_pitch"].as<double>(pid_params_.ki_pitch);
        pid_params_.kp_yaw = config["balance"]["pid"]["kp_yaw"].as<double>(pid_params_.kp_yaw);
        pid_params_.kd_yaw = config["balance"]["pid"]["kd_yaw"].as<double>(pid_params_.kd_yaw);
        pid_params_.ki_yaw = config["balance"]["pid"]["ki_yaw"].as<double>(pid_params_.ki_yaw);
    }

    // 加载目标姿态
    if (config["balance"] && config["balance"]["target_pose"]) {
        target_pose_.roll = config["balance"]["target_pose"]["roll"].as<double>(target_pose_.roll);
        target_pose_.pitch = config["balance"]["target_pose"]["pitch"].as<double>(target_pose_.pitch);
        target_pose_.yaw = config["balance"]["target_pose"]["yaw"].as<double>(target_pose_.yaw);
    }

    // 加载算法选择
    if (config["balance"]) {
        algorithm_ = config["balance"]["algorithm"].as<std::string>(algorithm_);
        max_torque_ = config["balance"]["max_torque"].as<double>(max_torque_);
        max_velocity_ = config["balance"]["max_velocity"].as<double>(max_velocity_);
    }

    // 加载控制参数
    if (config["control"]) {
        control_params_.control_frequency = config["control"]["control_frequency"].as<int>(control_params_.control_frequency);
        if (config["control"]["ethercat"]) {
            control_params_.ethercat_if = config["control"]["ethercat"]["interface"].as<std::string>(control_params_.ethercat_if);
            control_params_.cycle_ns = config["control"]["ethercat"]["cycle_ns"].as<int>(control_params_.cycle_ns);
            control_params_.enable_dc = config["control"]["ethercat"]["enable_dc"].as<bool>(control_params_.enable_dc);
        }
    }

    ROS_INFO("[HardwareParams] Loaded from YAML: %s", file_path.c_str());
    printSummary();
}

void RobotHardwareParams::printSummary() const {
    ROS_INFO("==========================================");
    ROS_INFO("Robot Hardware Parameters:");
    ROS_INFO("  [Robot]");
    ROS_INFO("    Name: %s, Type: %s, Mass: %.2f kg, Gravity: %.2f m/s^2", 
             robot_name_.c_str(), robot_type_.c_str(), mass_, gravity_);
    
    ROS_INFO("  [Leg Geometry]");
    ROS_INFO("    Upper: %.3fm, Lower: %.3fm", leg_geometry_.upper_leg_length, leg_geometry_.lower_leg_length);
    ROS_INFO("    Hip offset: X=%.3f, Y=%.3f, Z=%.3f", leg_geometry_.hip_offset_x, leg_geometry_.hip_offset_y, leg_geometry_.hip_offset_z);
    ROS_INFO("    Leg length range: %.3f-%.3fm", leg_geometry_.leg_length_min, leg_geometry_.leg_length_max);
    ROS_INFO("    Foot height range: %.3f-%.3fm", leg_geometry_.foot_height_min, leg_geometry_.foot_height_max);
    
    ROS_INFO("  [Wheel]");
    ROS_INFO("    Radius: %.3fm, Width: %.3fm, Wheel base: %.3fm", wheel_config_.radius, wheel_config_.width, wheel_config_.wheel_base);
    ROS_INFO("    Max speed: %.1f rad/s, Driver Kp: %.1f, Kd: %.1f", 
             wheel_config_.max_wheel_speed, wheel_config_.driver_kp, wheel_config_.driver_kd);
    
    ROS_INFO("  [IMU]");
    ROS_INFO("    Position: X=%.3f, Y=%.3f, Z=%.3f", imu_config_.position_x, imu_config_.position_y, imu_config_.position_z);
    ROS_INFO("    Rotation: roll=%.3f, pitch=%.3f, yaw=%.3f", 
             imu_config_.rotation_roll, imu_config_.rotation_pitch, imu_config_.rotation_yaw);
    ROS_INFO("    Neutral pose: roll=%.3f, pitch=%.3f, yaw=%.3f", 
             imu_config_.neutral_roll, imu_config_.neutral_pitch, imu_config_.neutral_yaw);
    ROS_INFO("    Balance range: roll=%.3f, pitch=%.3f, yaw=%.3f", 
             imu_config_.balance_roll_max, imu_config_.balance_pitch_max, imu_config_.balance_yaw_max);
    
    ROS_INFO("  [Motors] (%zu motors)", motor_configs_.size());
    for (size_t i = 0; i < motor_configs_.size(); ++i) {
        const auto& m = motor_configs_[i];
        ROS_INFO("    [%zu] %s: id=%d, ch=%d, type=%s, joint=%s, dir=%d",
                 i, m.name.c_str(), m.motor_id, m.channel, m.motor_type.c_str(), m.joint_type.c_str(), m.direction);
    }
    
    ROS_INFO("  [Motor Limits]");
    ROS_INFO("    R86: max_torque=%.1f, max_vel=%.1f, pos=[%.2f,%.2f], kp=%.1f, kd=%.1f",
             r86_limits_.max_torque, r86_limits_.max_velocity, r86_limits_.position_min, r86_limits_.position_max,
             r86_limits_.kp_default, r86_limits_.kd_default);
    ROS_INFO("    R52: max_torque=%.1f, max_vel=%.1f, pos=[%.2f,%.2f], kp=%.1f, kd=%.1f",
             r52_limits_.max_torque, r52_limits_.max_velocity, r52_limits_.position_min, r52_limits_.position_max,
             r52_limits_.kp_default, r52_limits_.kd_default);
    
    ROS_INFO("  [Joint Soft Limits]");
    ROS_INFO("    Hip roll: [%.3f, %.3f], Hip pitch: [%.3f, %.3f]", 
             joint_limits_.hip_roll_min, joint_limits_.hip_roll_max,
             joint_limits_.hip_pitch_min, joint_limits_.hip_pitch_max);
    ROS_INFO("    Knee pitch: [%.3f, %.3f], Wheel: [%.3f, %.3f]",
             joint_limits_.knee_pitch_min, joint_limits_.knee_pitch_max,
             joint_limits_.wheel_min, joint_limits_.wheel_max);
    
    ROS_INFO("  [Joint Home/Zero]");
    ROS_INFO("    hip_roll=%.3f, hip_pitch=%.3f, knee_pitch=%.3f, wheel=%.3f",
             joint_home_.hip_roll, joint_home_.hip_pitch, joint_home_.knee_pitch, joint_home_.wheel);
    ROS_INFO("    Offsets: hip_roll=%.3f, hip_pitch=%.3f, knee_pitch=%.3f, wheel=%.3f",
             joint_home_.hip_roll_offset, joint_home_.hip_pitch_offset, 
             joint_home_.knee_pitch_offset, joint_home_.wheel_offset);
    
    ROS_INFO("  [Control]");
    ROS_INFO("    Frequency: %d Hz, EtherCAT: %s, cycle_ns=%d, DC=%d",
             control_params_.control_frequency, control_params_.ethercat_if.c_str(),
             (int)control_params_.cycle_ns, control_params_.enable_dc);
    ROS_INFO("    Default mode: %s, Emergency stop: %.1f Nm",
             control_params_.default_mode.c_str(), control_params_.emergency_stop_threshold);
    
    ROS_INFO("  [Balance Control]");
    ROS_INFO("    Algorithm: %s", algorithm_.c_str());
    ROS_INFO("    PID Roll: Kp=%.1f, Kd=%.1f, Ki=%.1f", pid_params_.kp_roll, pid_params_.kd_roll, pid_params_.ki_roll);
    ROS_INFO("    PID Pitch: Kp=%.1f, Kd=%.1f, Ki=%.1f", pid_params_.kp_pitch, pid_params_.kd_pitch, pid_params_.ki_pitch);
    ROS_INFO("    PID Yaw: Kp=%.1f, Kd=%.1f, Ki=%.1f", pid_params_.kp_yaw, pid_params_.kd_yaw, pid_params_.ki_yaw);
    ROS_INFO("    Target pose: roll=%.3f, pitch=%.3f, yaw=%.3f",
             target_pose_.roll, target_pose_.pitch, target_pose_.yaw);
    ROS_INFO("    Max torque: %.1f Nm, Max velocity: %.1f rad/s", max_torque_, max_velocity_);
    
    ROS_INFO("==========================================");
}

void RobotHardwareParams::setTargetPose(double roll, double pitch, double yaw) {
    target_pose_.roll = roll;
    target_pose_.pitch = pitch;
    target_pose_.yaw = yaw;
    ROS_DEBUG("[HardwareParams] Set target pose: roll=%.3f, pitch=%.3f, yaw=%.3f", roll, pitch, yaw);
}

void RobotHardwareParams::setPIDParams(const PIDParams& params) {
    pid_params_ = params;
    ROS_DEBUG("[HardwareParams] Updated PID params");
}

void RobotHardwareParams::setControlFrequency(int freq) {
    if (freq > 0 && freq <= 2000) {
        control_params_.control_frequency = freq;
        ROS_INFO("[HardwareParams] Set control frequency: %d Hz", freq);
    } else {
        ROS_WARN("[HardwareParams] Invalid control frequency: %d (valid range: 1-2000)", freq);
    }
}

const MotorConfig* RobotHardwareParams::findMotorConfig(const std::string& joint_name) const {
    for (const auto& config : motor_configs_) {
        if (config.name == joint_name) {
            return &config;
        }
    }
    return nullptr;
}

const MotorConfig* RobotHardwareParams::findMotorConfigById(uint8_t motor_id, uint8_t channel) const {
    for (const auto& config : motor_configs_) {
        if (config.motor_id == motor_id && config.channel == channel) {
            return &config;
        }
    }
    return nullptr;
}

MotorLimitParams RobotHardwareParams::getMotorLimits(const std::string& motor_type) const {
    if (motor_type == "POWER_FLOW_R86" || motor_type == "R86") {
        return r86_limits_;
    } else if (motor_type == "POWER_FLOW_R52" || motor_type == "R52") {
        return r52_limits_;
    }
    ROS_WARN("[HardwareParams] Unknown motor type: %s, returning R86 defaults", motor_type.c_str());
    return r86_limits_;
}

Eigen::Vector3d RobotHardwareParams::getIMUNeutralOffset() const {
    return Eigen::Vector3d(imu_config_.neutral_roll,
                          imu_config_.neutral_pitch,
                          imu_config_.neutral_yaw);
}

bool RobotHardwareParams::isPoseSafe(double roll, double pitch) const {
    bool safe = std::abs(roll) <= imu_config_.balance_roll_max &&
                std::abs(pitch) <= imu_config_.balance_pitch_max;
    if (!safe) {
        ROS_WARN("[HardwareParams] Pose out of safe range! roll=%.3f(max=%.3f), pitch=%.3f(max=%.3f)",
                 roll, imu_config_.balance_roll_max, pitch, imu_config_.balance_pitch_max);
    }
    return safe;
}

bool RobotHardwareParams::applySoftLimits(const std::string& joint_type, double& value) const {
    double min_val, max_val;

    if (joint_type == "hip_roll") {
        min_val = joint_limits_.hip_roll_min;
        max_val = joint_limits_.hip_roll_max;
    } else if (joint_type == "hip_pitch") {
        min_val = joint_limits_.hip_pitch_min;
        max_val = joint_limits_.hip_pitch_max;
    } else if (joint_type == "knee_pitch") {
        min_val = joint_limits_.knee_pitch_min;
        max_val = joint_limits_.knee_pitch_max;
    } else if (joint_type == "wheel") {
        min_val = joint_limits_.wheel_min;
        max_val = joint_limits_.wheel_max;
    } else {
        return true;
    }

    if (value < min_val) {
        ROS_WARN("[HardwareParams] Joint %s value %.3f below min %.3f, clamped",
                 joint_type.c_str(), value, min_val);
        value = min_val;
        return false;
    }
    if (value > max_val) {
        ROS_WARN("[HardwareParams] Joint %s value %.3f above max %.3f, clamped",
                 joint_type.c_str(), value, max_val);
        value = max_val;
        return false;
    }
    return true;
}

double RobotHardwareParams::applyTorqueLimit(const std::string& motor_type, double torque) const {
    MotorLimitParams limits = getMotorLimits(motor_type);

    if (torque > limits.max_torque) {
        ROS_WARN("[HardwareParams] Torque %.3f exceeds %s max %.3f, clamped",
                 torque, motor_type.c_str(), limits.max_torque);
        return limits.max_torque;
    }
    if (torque < -limits.max_torque) {
        ROS_WARN("[HardwareParams] Torque %.3f below %s min %.3f, clamped",
                 torque, motor_type.c_str(), -limits.max_torque);
        return -limits.max_torque;
    }
    return torque;
}

Eigen::Matrix4d RobotHardwareParams::getHipTransform(uint8_t leg) const {
    Eigen::Matrix4d transform = Eigen::Matrix4d::Identity();

    // 髋关节位置 (根据腿别)
    double x_offset = leg == 0 ? -leg_geometry_.hip_offset_x : leg_geometry_.hip_offset_x;

    transform(0, 3) = x_offset;
    transform(1, 3) = leg_geometry_.hip_offset_y;
    transform(2, 3) = leg_geometry_.hip_offset_z;

    return transform;
}

double RobotHardwareParams::computeLegLength(double hip_pitch, double knee_pitch) const {
    // 使用余弦定理计算腿长
    // L = sqrt(L1^2 + L2^2 - 2*L1*L2*cos(angle_sum))
    double angle_sum = hip_pitch + knee_pitch;
    double L1 = leg_geometry_.upper_leg_length;
    double L2 = leg_geometry_.lower_leg_length;

    double leg_length = std::sqrt(L1 * L1 + L2 * L2 - 2 * L1 * L2 * std::cos(angle_sum));

    return leg_length;
}

} // namespace balance_control