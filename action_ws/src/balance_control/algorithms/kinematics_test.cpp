/*
 * 运动学库测试程序
 * ================
 *
 * 演示 wheeled_legged_kinematics.h 的使用方法
 *
 * 编译:
 *   cd /home/jetson/Desktop/Jetson_Nano
 *   g++ -std=c++17 -DUSE_YAML_CPP \
 *       -Iaction_ws/src/balance_control/algorithms \
 *       -I/usr/include/eigen3 \
 *       -I/opt/ros/noetic/include \
 *       action_ws/src/balance_control/algorithms/kinematics_test.cpp \
 *       -lyaml-cpp -o kinematics_test
 *
 * 运行:
 *   ./kinematics_test
 *   或者指定YAML文件:
 *   ./kinematics_test /path/to/wheeled_legged_kinematics.yaml
 *
 * Author: Qi Xiao
Email: 2408128687@qq.com
 * 日期: 2026-05-06
 */

#include <iostream>
#include <cmath>
#include <string>
#include <cstdlib>
#include "wheeled_legged_kinematics.h"

using namespace kinematics;

// 打印关节角度
void printLegJoints(const LegJoints& joints) {
    std::cout << "  髋横滚:  " << joints.hip_roll << " rad (" << joints.hip_roll * 180.0 / M_PI << " deg)\n";
    std::cout << "  髋俯仰:  " << joints.hip_pitch << " rad (" << joints.hip_pitch * 180.0 / M_PI << " deg)\n";
    std::cout << "  膝俯仰:  " << joints.knee_pitch << " rad (" << joints.knee_pitch * 180.0 / M_PI << " deg)\n";
    std::cout << "  轮子:    " << joints.wheel << " rad\n";
}

// 打印足端位姿
void printFootPose(const FootPose& pose) {
    std::cout << "  位置: (" << pose.position.x << ", " 
              << pose.position.y << ", " << pose.position.z << ") m\n";
}

int main(int argc, char** argv) {
    std::cout << "==========================================\n";
    std::cout << "轮腿机器人运动学测试\n";
    std::cout << "==========================================\n\n";

    // 初始化运动学参数
    KinematicsParams params;

    // 尝试从YAML文件加载参数
    std::string yaml_path;
    if (argc > 1) {
        yaml_path = argv[1];
    } else {
        // 默认路径
        yaml_path = "/home/jetson/Desktop/Jetson_Nano/action_ws/src/balance_control/config/wheeled_legged_kinematics.yaml";
    }

    std::cout << "尝试加载YAML配置: " << yaml_path << "\n\n";

    bool loaded = loadFromYaml(yaml_path, params);
    if (loaded) {
        std::cout << "YAML加载成功!\n\n";
        printParams(params);
    } else {
        std::cout << "YAML加载失败,使用默认URDF参数!\n\n";
        params.L1 = 0.0725;
        params.L2 = 0.301;
        params.hip_offset_x = 0.069;
        params.hip_offset_y = -0.124;
        params.hip_offset_z = -0.001;
        params.wheel_radius = 0.10;
        params.wheel_base = 0.40;
        params.ankle_offset_x = 0.224;
        params.ankle_offset_z = -0.200;

        params.hip_roll_min = -3.1416;
        params.hip_roll_max = 3.1416;
        params.hip_pitch_min = -2.0944;
        params.hip_pitch_max = 2.0944;
        params.knee_pitch_min = -0.8727;
        params.knee_pitch_max = 0.8727;
    }

    std::cout << "\n";

    // ===========================================
    // 测试1: 正向运动学
    // 输入关节角度 -> 输出足端位置
    // ===========================================
    std::cout << "==========================================\n";
    std::cout << "测试1: 正向运动学\n";
    std::cout << "----------------------------\n";

    // 站立姿态 (所有角度为0)
    LegJoints standing;
    standing.hip_roll = 0.0;
    standing.hip_pitch = 0.0;
    standing.knee_pitch = 0.0;
    standing.wheel = 0.0;

    FootPose foot = forwardKinematics(standing.hip_roll, standing.hip_pitch, 
                                      standing.knee_pitch, LegSide::LEFT, params);
    std::cout << "站立姿态 (全0):\n";
    printFootPose(foot);

    // 前倾姿态 (髋俯仰=0.3 rad)
    standing.hip_pitch = 0.3;
    foot = forwardKinematics(standing.hip_roll, standing.hip_pitch, 
                            standing.knee_pitch, LegSide::LEFT, params);
    std::cout << "\n前倾姿态 (髋俯仰=0.3 rad):\n";
    printFootPose(foot);

    // ===========================================
    // 测试2: 逆向运动学
    // 输入足端位置 -> 输出关节角度
    // ===========================================
    std::cout << "\n==========================================\n";
    std::cout << "测试2: 逆向运动学\n";
    std::cout << "----------------------------\n";

    // 给定一个期望的足端位置
    Vec3 target_pos;
    target_pos.x = 0.0;
    target_pos.y = -0.30; // 足端在髋关节后方0.30m
    target_pos.z = 0.25;   // 足端在髋关节下方0.25m

    std::cout << "目标足端位置: (" << target_pos.x << ", " 
              << target_pos.y << ", " << target_pos.z << ") m\n";

    // 计算逆解
    LegJoints ik_result = inverseKinematics(target_pos, LegSide::LEFT, params);
    std::cout << "\n计算的关节角度:\n";
    printLegJoints(ik_result);

    // 验证: 用FK验算
    FootPose verified = forwardKinematics(ik_result.hip_roll, ik_result.hip_pitch, 
                                         ik_result.knee_pitch, LegSide::LEFT, params);
    std::cout << "\n验证足端位置 (FK验算IK结果):\n";
    printFootPose(verified);

    // ===========================================
    // 测试3: 基于高度的反向运动学
    // 根据机体高度计算关节角度
    // ===========================================
    std::cout << "\n==========================================\n";
    std::cout << "测试3: 基于高度的反向运动学\n";
    std::cout << "----------------------------\n";

    double body_height = 0.35; // 机体高度0.35m
    double body_pitch = 0.0;   // 机体俯仰0度

    ik_result = inverseKinematicsForHeight(body_height, body_pitch, LegSide::LEFT, params);
    std::cout << "机体高度: " << body_height << " m, 俯仰角: " << body_pitch << " rad\n";
    std::cout << "计算的关节角度:\n";
    printLegJoints(ik_result);

    // ===========================================
    // 测试4: 雅可比矩阵
    // 关节速度到末端速度的映射
    // ===========================================
    std::cout << "\n==========================================\n";
    std::cout << "测试4: 雅可比矩阵\n";
    std::cout << "----------------------------\n";

    Eigen::Matrix3d J = computeJacobian(0.3, -0.3, params);
    std::cout << "髋俯仰=0.3, 膝俯仰=-0.3时的雅可比矩阵:\n";
    std::cout << J << "\n";

    // ===========================================
    // 测试5: 腿长计算
    // ===========================================
    std::cout << "\n==========================================\n";
    std::cout << "测试5: 腿长计算\n";
    std::cout << "----------------------------\n";

    standing.hip_pitch = 0.0;
    standing.knee_pitch = 0.0;
    std::cout << "腿长 (完全伸展): " << computeLegLength(standing.hip_pitch, standing.knee_pitch, params) << " m\n";

    standing.hip_pitch = 0.5;
    standing.knee_pitch = -0.5;
    std::cout << "腿长 (弯曲状态): " << computeLegLength(standing.hip_pitch, standing.knee_pitch, params) << " m\n";

    // ===========================================
    // 测试6: 工作空间检查
    // ===========================================
    std::cout << "\n==========================================\n";
    std::cout << "测试6: 工作空间检查\n";
    std::cout << "----------------------------\n";

    standing.hip_pitch = 0.0;
    standing.knee_pitch = 0.0;
    std::cout << "完全伸展姿态 在工作空间内: " 
              << (isInWorkspace(standing.hip_pitch, standing.knee_pitch, params) ? "是" : "否") << "\n";

    standing.hip_pitch = 1.5;
    standing.knee_pitch = -1.5;
    std::cout << "高度弯曲姿态 在工作空间内: " 
              << (isInWorkspace(standing.hip_pitch, standing.knee_pitch, params) ? "是" : "否") << "\n";

    // ===========================================
    // 测试7: 关节角度插值
    // 用于平滑的姿态过渡
    // ===========================================
    std::cout << "\n==========================================\n";
    std::cout << "测试7: 关节角度插值\n";
    std::cout << "----------------------------\n";

    // 姿态A (起始)
    LegJoints pose_a;
    pose_a.hip_roll = 0.0;
    pose_a.hip_pitch = 0.0;
    pose_a.knee_pitch = 0.0;
    pose_a.wheel = 0.0;

    // 姿态B (目标)
    LegJoints pose_b;
    pose_b.hip_roll = 0.5;
    pose_b.hip_pitch = 0.3;
    pose_b.knee_pitch = -0.4;
    pose_b.wheel = 1.0;

    std::cout << "姿态A (t=0.0):\n";
    printLegJoints(pose_a);

    std::cout << "\n姿态B (t=1.0):\n";
    printLegJoints(pose_b);

    // 50%插值
    LegJoints interp_50 = interpolateJoints(pose_a, pose_b, 0.5, params);
    std::cout << "\n插值姿态 (t=0.5):\n";
    printLegJoints(interp_50);

    std::cout << "\n==========================================\n";
    std::cout << "所有测试完成!\n";
    std::cout << "==========================================\n";

    return 0;
}