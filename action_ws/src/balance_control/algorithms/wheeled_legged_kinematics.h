/*
 * 轮腿机器人运动学模型
 * ============================
 *
 * 提供双足轮腿机器人的正逆运动学解算接口
 *
 * 坐标系定义 (机体坐标系):
 *   Z (上)
 *   ^   Y (后/前)
 *   |  /
 *   | /
 *   +----> X (右)
 *
 * 腿部关节结构 (每条腿):
 *   髋横滚 (Hip Roll)  - 绕Y轴旋转，控制腿部外展/内收
 *   髋俯仰 (Hip Pitch) - 绕X轴旋转，控制大腿前摆/后摆
 *   膝俯仰 (Knee Pitch) - 绕X轴旋转，控制小腿后摆/前摆
 *   轮子 (Wheel)       - 绕X轴旋转，驱动轮子转动
 *
 * Author: Qi Xiao
Email: 2408128687@qq.com
 * 日期: 2026-05-06
 */

#ifndef WHEELED_LEGGED_KINEMATICS_H
#define WHEELED_LEGGED_KINEMATICS_H

#include <Eigen/Dense>
#include <string>
#include <vector>
#include <iostream>

#ifdef USE_YAML_CPP
#include <yaml-cpp/yaml.h>
#endif

namespace kinematics {

/*
 * 关节索引枚举
 */
enum class JointIndex {
    HIP_ROLL = 0,     // 髋横滚
    HIP_PITCH = 1,   // 髋俯仰
    KNEE_PITCH = 2,   // 膝俯仰
    WHEEL = 3         // 轮子
};

/*
 * 腿侧枚举
 */
enum class LegSide {
    LEFT = 0,   // 左腿
    RIGHT = 1   // 右腿
};

/*
 * 2D向量
 */
struct Vec2 {
    double x;
    double y;
};

/*
 * 3D向量
 */
struct Vec3 {
    double x;
    double y;
    double z;
};

/*
 * 单腿关节角度结构
 * 单位: 弧度 (rad)
 */
struct LegJoints {
    double hip_roll;   // 髋横滚角 (rad), 正值=腿部外展
    double hip_pitch;  // 髋俯仰角 (rad), 正值=大腿前摆
    double knee_pitch; // 膝俯仰角 (rad), 正值=小腿后摆
    double wheel;      // 轮子转角 (rad)

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

/*
 * 足端位姿结构 (相对于机体坐标系)
 */
struct FootPose {
    Vec3 position;     // 足端x,y,z位置 (m)
    Vec3 orientation;  // 足端roll,pitch,yaw角度 (rad) - 轮腿机器人通常不使用

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

/*
 * 机器人状态结构 (包含双腿)
 */
struct RobotState {
    LegJoints left_leg;   // 左腿关节角度
    LegJoints right_leg;  // 右腿关节角度

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

/*
 * 运动学参数结构
 * 从YAML配置文件加载
 */
struct KinematicsParams {
    // ========== 腿部几何参数 ==========
    // 大腿长度 (髋关节到膝关节) [m]
    double L1 = 0.20;

    // 小腿长度 (膝关节到踝关节/足端) [m]
    double L2 = 0.20;

    // 髋关节偏移 (相对于机体中心)
    // 髋关节在机体上的位置偏移
    double hip_offset_x = 0.10;  // 横向偏移 (m) - 左右各一个
    double hip_offset_y = 0.0;   // 纵向偏移 (m)
    double hip_offset_z = 0.0;   // 垂向偏移 (m)

    // 轮子参数
    double wheel_radius = 0.10;   // 轮子半径 [m]
    double wheel_base = 0.40;    // 轮距 (左右轮中心距) [m]

    // 踝关节偏移 (膝关节到踝关节的垂直距离) [m]
    double ankle_offset = 0.05;

    // ========== 关节限位 [rad] ==========
    double hip_roll_min = -1.57;    // 髋横滚最小角度 (~-90度)
    double hip_roll_max = 1.57;     // 髋横滚最大角度 (~+90度)
    double hip_pitch_min = -1.57;    // 髋俯仰最小角度
    double hip_pitch_max = 1.57;     // 髋俯仰最大角度
    double knee_pitch_min = -2.35;   // 膝俯仰最小角度 (~-135度)
    double knee_pitch_max = 0.0;     // 膝俯仰最大角度 (只能向后弯曲)

    // ========== 默认零位/起始位置 [rad] ==========
    double home_hip_roll = 0.0;     // 髋横滚起始角度
    double home_hip_pitch = 0.0;    // 髋俯仰起始角度
    double home_knee_pitch = 0.0;    // 膝俯仰起始角度
    double home_wheel = 0.0;         // 轮子起始角度

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

/*
 * 正向运动学 (Forward Kinematics)
 * ================================
 *
 * 功能: 根据关节角度计算足端在机体坐标系中的位置
 *
 * 输入参数:
 *   @param hip_roll   髋横滚角度 (rad), 正值=腿外展
 *   @param hip_pitch  髋俯仰角度 (rad), 正值=大腿前摆
 *   @param knee_pitch 膝俯仰角度 (rad), 正值=小腿后摆
 *   @param leg_side   腿侧 (LEFT或RIGHT, 影响横滚方向)
 *   @param params     运动学参数
 *
 * 输出:
 *   @return FootPose 包含足端x,y,z位置
 *
 * 算法说明:
 *   1. 根据髋关节偏移计算髋关节位置
 *   2. 根据髋俯仰角度计算膝关节位置 (大腿向量)
 *   3. 根据膝俯仰角度计算足端位置 (小腿向量)
 *   4. 加上轮子半径得到实际足端位置
 */
inline FootPose forwardKinematics(double hip_roll, double hip_pitch, double knee_pitch,
                                   LegSide leg_side, const KinematicsParams& params) {
    FootPose foot;

    // 左右腿的符号因子
    double side_sign = (leg_side == LegSide::LEFT) ? 1.0 : -1.0;

    // 有效髋横滚角度 (符号取决于腿侧)
    double theta_roll = hip_roll * side_sign;

    // 计算髋关节在机体坐标系中的位置
    // 髋关节相对于机体中心的偏移
    double hip_x = side_sign * params.hip_offset_x;  // 左右对称分布
    double hip_y = params.hip_offset_y;              // 前后偏移
    double hip_z = params.hip_offset_z;              // 垂直偏移

    // 计算膝关节位置 (考虑髋俯仰角度)
    // 髋俯仰绕X轴旋转,影响大腿在Y-Z平面的位置
    double knee_x = hip_x;
    double knee_y = hip_y + params.L1 * cos(hip_pitch);  // Y方向分量
    double knee_z = hip_z + params.L1 * sin(hip_pitch);  // Z方向分量

    // 计算足端位置 (考虑膝俯仰角度)
    // 总腿部长度 = L1 + L2
    // 膝俯仰影响小腿相对于大腿的角度
    double total_pitch = hip_pitch + knee_pitch;
    double foot_x = hip_x;  // 膝俯仰不影响足端横向位置
    double foot_y = knee_y + params.L2 * cos(total_pitch);
    double foot_z = knee_z + params.L2 * sin(total_pitch);

    // 减去踝关节偏移
    foot_z -= params.ankle_offset;

    // 加上轮子半径得到足端实际位置 (轮子接触地面)
    // 对于轮腿机器人,"足端"实际上是轮子中心
    foot.position.x = foot_x;
    foot.position.y = foot_y;
    foot.position.z = foot_z + params.wheel_radius;

    return foot;
}

/*
 * 简化的正向运动学 (2D俯视图)
 * ============================
 *
 * 功能: 计算足端在矢状面的x-y位置 (假设侧向运动为0)
 *
 * 输入参数:
 *   @param hip_pitch  髋俯仰角度 (rad)
 *   @param knee_pitch 膝俯仰角度 (rad)
 *   @param params     运动学参数
 *
 * 输出:
 *   @return Vec2 足端x,y位置
 */
inline Vec2 forwardKinematics2D(double hip_pitch, double knee_pitch, const KinematicsParams& params) {
    Vec2 pos;

    // 总腿部长度角
    double total_angle = hip_pitch + knee_pitch;

    // 髋关节位置
    double hip_y = params.hip_offset_y;

    // 膝关节位置
    double knee_y = hip_y + params.L1 * cos(hip_pitch);
    double knee_z = params.hip_offset_z + params.L1 * sin(hip_pitch);

    // 足端位置
    pos.x = 0.0;  // 足端在矢状面上位于中心线
    pos.y = knee_y + params.L2 * cos(total_angle);

    return pos;
}

/*
 * 逆向运动学 (Inverse Kinematics) - 解析解
 * ==========================================
 *
 * 功能: 根据期望的足端位置计算各关节角度
 *
 * 输入参数:
 *   @param foot_pos  期望的足端位置 (相对于髋关节)
 *   @param leg_side  腿侧 (LEFT或RIGHT)
 *   @param params    运动学参数
 *
 * 输出:
 *   @return LegJoints 计算得到的关节角度
 *
 * 算法说明 (余弦定理):
 *   1. 计算髋关节到足端的距离 L_total
 *   2. 用余弦定理计算髋俯仰角度:
 *      L2^2 = L1^2 + L_total^2 - 2*L1*L_total*cos(alpha)
 *      其中alpha是股骨和髋-足连线的夹角
 *   3. 髋俯仰 = gamma - alpha
 *      其中gamma是髋-足连线与水平面的夹角
 *   4. 膝俯仰同理计算
 */
inline LegJoints inverseKinematics(const Vec3& foot_pos, LegSide leg_side, const KinematicsParams& params) {
    LegJoints joints;

    // 符号因子
    double side_sign = (leg_side == LegSide::LEFT) ? 1.0 : -1.0;

    // 计算足端相对于髋关节的偏移
    double dx = foot_pos.x;
    double dy = foot_pos.y;
    double dz = foot_pos.z - params.hip_offset_z;

    // 髋关节到足端的距离 (在矢状面上)
    double L_total = sqrt(dx * dx + dy * dy + dz * dz);

    // 限幅到有效范围 (避免数值不稳定)
    double L_min = params.L1 + params.L2 - 0.01;
    double L_max = 0.50;  // 一些合理的最大值
    L_total = std::max(L_min, std::min(L_max, L_total));

    // ========== 计算髋俯仰角度 (余弦定理) ==========
    // L2^2 = L1^2 + L_total^2 - 2*L1*L_total*cos(alpha)
    double cos_alpha = (params.L1 * params.L1 + L_total * L_total - params.L2 * params.L2) 
                       / (2 * params.L1 * L_total);
    cos_alpha = std::max(-1.0, std::min(1.0, cos_alpha));  // 限幅避免NaN
    double alpha = acos(cos_alpha);

    // 髋-足连线与垂直方向的夹角
    double gamma = atan2(dz, dy);

    // 髋俯仰角度 = gamma - alpha
    joints.hip_pitch = gamma - alpha;

    // ========== 计算膝俯仰角度 (余弦定理) ==========
    // L1^2 = L2^2 + L_total^2 - 2*L2*L_total*cos(beta)
    double cos_beta = (params.L2 * params.L2 + L_total * L_total - params.L1 * params.L1)
                      / (2 * params.L2 * L_total);
    cos_beta = std::max(-1.0, std::min(1.0, cos_beta));
    double beta = acos(cos_beta);

    // 膝俯仰角度 = PI - beta
    joints.knee_pitch = M_PI - beta;

    // ========== 计算髋横滚角度 ==========
    // 髋横滚与足端侧向偏移成正比
    joints.hip_roll = atan2(dx, sqrt(dy * dy + dz * dz)) * side_sign;

    // 轮子角度 (保持与地面接触,通常设为0)
    joints.wheel = 0.0;

    // 应用关节限位
    joints.hip_roll = std::max(params.hip_roll_min, std::min(params.hip_roll_max, joints.hip_roll));
    joints.hip_pitch = std::max(params.hip_pitch_min, std::min(params.hip_pitch_max, joints.hip_pitch));
    joints.knee_pitch = std::max(params.knee_pitch_min, std::min(params.knee_pitch_max, joints.knee_pitch));

    return joints;
}

/*
 * 基于高度的逆向运动学
 * ====================
 *
 * 功能: 根据期望的机体高度和俯仰角计算腿部关节角度
 *       常用于保持机体水平行走时的姿态解算
 *
 * 输入参数:
 *   @param body_height 期望的机体高度 (相对于地面) [m]
 *   @param body_pitch 期望的机体俯仰角 [rad]
 *   @param leg_side   腿侧 (LEFT或RIGHT)
 *   @param params     运动学参数
 *
 * 输出:
 *   @return LegJoints 计算得到的关节角度
 */
inline LegJoints inverseKinematicsForHeight(double body_height, double body_pitch,
                                              LegSide leg_side, const KinematicsParams& params) {
    // 足端目标位置
    Vec3 foot_pos;

    // 在机体坐标系中,足端位于髋关节下方
    // 考虑机体俯仰角时,足端位置会前后偏移
    double hip_height = body_height - params.hip_offset_z;

    // 足端位置计算
    foot_pos.x = 0.0;
    foot_pos.y = -params.hip_offset_y + 0.5 * sin(body_pitch) * params.wheel_base;
    foot_pos.z = hip_height - params.wheel_radius;

    return inverseKinematics(foot_pos, leg_side, params);
}

/*
 * 雅可比矩阵 (Jacobian Matrix)
 * ==========================
 *
 * 功能: 计算关节角速度到足端速度的映射矩阵
 *
 * 数学表达式:
 *   d_foot = J * d_joints
 *
 * 其中:
 *   d_foot = [dx, dy, dz]^T  足端速度
 *   d_joints = [d_hip_pitch, d_knee_pitch]^T  关节角速度
 *
 * 返回:
 *   3x3 雅可比矩阵 (用于完整3D情况,实际只使用y,z两行)
 */
inline Eigen::Matrix3d computeJacobian(double hip_pitch, double knee_pitch, const KinematicsParams& params) {
    Eigen::Matrix3d J;

    double total_angle = hip_pitch + knee_pitch;
    double L1 = params.L1;
    double L2 = params.L2;

    // 足端位置对关节角度的偏导数
    // x = 0 (足端在矢状面上x方向不变)
    // y = L1*cos(hip) + L2*cos(total)
    // z = L1*sin(hip) + L2*sin(total)

    // X分量
    J(0, 0) = 0;  // dx/d_hip_roll = 0
    J(0, 1) = 0;  // dx/d_hip_pitch = 0
    J(0, 2) = 0;  // dx/d_knee_pitch = 0

    // Y分量
    J(1, 0) = 0;  // dy/d_hip_roll = 0
    J(1, 1) = -L1 * sin(hip_pitch) - L2 * sin(total_angle);  // dy/d_hip_pitch
    J(1, 2) = -L2 * sin(total_angle);                          // dy/d_knee_pitch

    // Z分量
    J(2, 0) = 0;  // dz/d_hip_roll = 0
    J(2, 1) = L1 * cos(hip_pitch) + L2 * cos(total_angle);   // dz/d_hip_pitch
    J(2, 2) = L2 * cos(total_angle);                          // dz/d_knee_pitch

    return J;
}

/*
 * 逆雅可比矩阵 (用于关节速度控制)
 * ==============================
 *
 * 功能: 根据期望的足端速度计算所需的关节角速度
 *
 * 输入参数:
 *   @param foot_vel   期望的足端速度 [dx, dy, dz]^T
 *   @param hip_pitch  当前髋俯仰角
 *   @param knee_pitch 当前膝俯仰角
 *   @param params     运动学参数
 *
 * 输出:
 *   @return Eigen::Vector2d [d_hip_pitch, d_knee_pitch]^T
 *
 * 注意: 这是一个欠驱动问题 (3个输出,2个输入)
 *       使用伪逆求解 (最小二乘解)
 */
inline Eigen::Vector2d inverseJacobian(const Eigen::Vector3d& foot_vel,
                                       double hip_pitch, double knee_pitch,
                                       const KinematicsParams& params) {
    Eigen::Matrix3d J = computeJacobian(hip_pitch, knee_pitch, params);

    // 只使用y,z两行 (欠驱动情况)
    Eigen::Matrix2d J_reduced;
    J_reduced << J(1, 1), J(1, 2),
                 J(2, 1), J(2, 2);

    Eigen::Vector2d foot_vel_reduced;
    foot_vel_reduced << foot_vel(1), foot_vel(2);

    // 使用QR分解求解 (比伪逆更稳定)
    return J_reduced.colPivHouseholderQr().solve(foot_vel_reduced);
}

/*
 * 计算腿部长度
 * ===========
 *
 * 功能: 计算当前关节角度下的腿部长度
 *
 * 输入参数:
 *   @param hip_pitch  髋俯仰角 [rad]
 *   @param knee_pitch 膝俯仰角 [rad]
 *   @param params     运动学参数
 *
 * 输出:
 *   @return double 腿部长度 [m]
 */
inline double computeLegLength(double hip_pitch, double knee_pitch, const KinematicsParams& params) {
    double total_angle = hip_pitch + knee_pitch;
    return params.L1 * cos(hip_pitch) + params.L2 * cos(total_angle);
}

/*
 * 计算足端速度
 * ===========
 *
 * 功能: 根据关节角速度计算足端速度
 *
 * 输入参数:
 *   @param joint_vels [d_hip_pitch, d_knee_pitch]^T
 *   @param hip_pitch  当前髋俯仰角
 *   @param knee_pitch 当前膝俯仰角
 *   @param params     运动学参数
 *
 * 输出:
 *   @return Eigen::Vector3d 足端速度 [dx, dy, dz]^T
 */
inline Eigen::Vector3d computeFootVelocity(const Eigen::Vector2d& joint_vels,
                                            double hip_pitch, double knee_pitch,
                                            const KinematicsParams& params) {
    Eigen::Matrix3d J = computeJacobian(hip_pitch, knee_pitch, params);
    Eigen::Vector3d foot_vel;

    // 只使用y,z两行
    foot_vel(1) = J(1, 1) * joint_vels(0) + J(1, 2) * joint_vels(1);
    foot_vel(2) = J(2, 1) * joint_vels(0) + J(2, 2) * joint_vels(1);

    return foot_vel;
}

/*
 * 检查构型是否在工作空间内
 * =======================
 *
 * 功能: 判断给定的关节角度是否在腿部的有效工作空间内
 *
 * 输入参数:
 *   @param hip_pitch  髋俯仰角 [rad]
 *   @param knee_pitch 膝俯仰角 [rad]
 *   @param params     运动学参数
 *
 * 输出:
 *   @return bool true=在工作空间内, false=超出工作空间
 */
inline bool isInWorkspace(double hip_pitch, double knee_pitch, const KinematicsParams& params) {
    double leg_length = computeLegLength(hip_pitch, knee_pitch, params);
    double L_max = params.L1 + params.L2 - 0.001;           // 最大伸长
    double L_min = std::abs(params.L1 - params.L2) + 0.001;  // 最小收缩

    return (leg_length >= L_min && leg_length <= L_max);
}

/*
 * 关节角度插值
 * ===========
 *
 * 功能: 在两个关节构型之间进行线性插值
 *       用于平滑的姿态过渡
 *
 * 输入参数:
 *   @param a      起始关节构型
 *   @param b      目标关节构型
 *   @param t      插值参数 [0, 1], t=0返回a, t=1返回b
 *   @param params 运动学参数
 *
 * 输出:
 *   @return LegJoints 插值后的关节构型
 */
inline LegJoints interpolateJoints(const LegJoints& a, const LegJoints& b, double t,
                                    const KinematicsParams& params) {
    LegJoints result;

    // 限幅到[0,1]
    t = std::max(0.0, std::min(1.0, t));

    // 线性插值
    result.hip_roll = a.hip_roll + t * (b.hip_roll - a.hip_roll);
    result.hip_pitch = a.hip_pitch + t * (b.hip_pitch - a.hip_pitch);
    result.knee_pitch = a.knee_pitch + t * (b.knee_pitch - a.knee_pitch);
    result.wheel = a.wheel + t * (b.wheel - a.wheel);

    return result;
}

/*
 * 从参数结构体加载运动学参数
 * =========================
 *
 * 功能: 便捷函数,用于初始化运动学参数
 *
 * 输入参数:
 *   @param params          目标参数结构体引用
 *   @param L1              大腿长度 [m]
 *   @param L2              小腿长度 [m]
 *   @param hip_offset_x    髋横向偏移 [m]
 *   @param hip_offset_y    髋纵向偏移 [m]
 *   @param hip_offset_z    髋垂向偏移 [m]
 *   @param wheel_radius    轮子半径 [m]
 */
inline void loadParams(KinematicsParams& params, double L1, double L2,
                       double hip_offset_x, double hip_offset_y, double hip_offset_z,
                       double wheel_radius) {
    params.L1 = L1;
    params.L2 = L2;
    params.hip_offset_x = hip_offset_x;
    params.hip_offset_y = hip_offset_y;
    params.hip_offset_z = hip_offset_z;
    params.wheel_radius = wheel_radius;
}

/*
 * 从YAML文件加载运动学参数
 * ========================
 *
 * 功能: 从YAML配置文件加载完整的运动学参数
 *
 * 输入参数:
 *   @param file_path YAML文件路径
 *   @param params    目标参数结构体引用
 *
 * 输出:
 *   @return bool true=加载成功, false=加载失败
 *
 * YAML文件格式:
 *   leg:
 *     upper_leg_length: 0.20
 *     lower_leg_length: 0.20
 *     hip_offset:
 *       x: 0.10
 *       y: 0.0
 *       z: 0.0
 *   wheel:
 *     radius: 0.10
 *     wheel_base: 0.40
 */
inline bool loadFromYaml(const std::string& file_path, KinematicsParams& params) {
#ifdef USE_YAML_CPP
    try {
        YAML::Node config = YAML::LoadFile(file_path);
        if (!config) {
            std::cerr << "[Kinematics] 无法加载YAML文件: " << file_path << std::endl;
            return false;
        }

        // 加载腿部几何参数
        if (config["leg"]) {
            const auto& leg = config["leg"];
            params.L1 = leg["upper_leg_length"].as<double>(params.L1);
            params.L2 = leg["lower_leg_length"].as<double>(params.L2);
            params.ankle_offset = leg["ankle_offset"].as<double>(params.ankle_offset);

            if (leg["hip_offset"]) {
                params.hip_offset_x = leg["hip_offset"]["x"].as<double>(params.hip_offset_x);
                params.hip_offset_y = leg["hip_offset"]["y"].as<double>(params.hip_offset_y);
                params.hip_offset_z = leg["hip_offset"]["z"].as<double>(params.hip_offset_z);
            }

            if (leg["workspace"]) {
                // 可以加载工作空间限制
            }
        }

        // 加载轮子参数
        if (config["wheel"]) {
            const auto& wheel = config["wheel"];
            params.wheel_radius = wheel["radius"].as<double>(params.wheel_radius);
            params.wheel_base = wheel["wheel_base"].as<double>(params.wheel_base);
        }

        // 加载关节限位
        if (config["joint_limits"]) {
            const auto& limits = config["joint_limits"];

            if (limits["hip_roll"]) {
                params.hip_roll_min = limits["hip_roll"]["min"].as<double>(params.hip_roll_min);
                params.hip_roll_max = limits["hip_roll"]["max"].as<double>(params.hip_roll_max);
            }

            if (limits["hip_pitch"]) {
                params.hip_pitch_min = limits["hip_pitch"]["min"].as<double>(params.hip_pitch_min);
                params.hip_pitch_max = limits["hip_pitch"]["max"].as<double>(params.hip_pitch_max);
            }

            if (limits["knee_pitch"]) {
                params.knee_pitch_min = limits["knee_pitch"]["min"].as<double>(params.knee_pitch_min);
                params.knee_pitch_max = limits["knee_pitch"]["max"].as<double>(params.knee_pitch_max);
            }
        }

        // 加载默认零位
        if (config["home_position"]) {
            const auto& home = config["home_position"];
            params.home_hip_roll = home["hip_roll"].as<double>(params.home_hip_roll);
            params.home_hip_pitch = home["hip_pitch"].as<double>(params.home_hip_pitch);
            params.home_knee_pitch = home["knee_pitch"].as<double>(params.home_knee_pitch);
            params.home_wheel = home["wheel"].as<double>(params.home_wheel);
        }

        std::cout << "[Kinematics] 从YAML加载参数: " << file_path << std::endl;
        return true;

    } catch (const std::exception& e) {
        std::cerr << "[Kinematics] YAML解析错误: " << e.what() << std::endl;
        return false;
    }
#else
    std::cerr << "[Kinematics] 未启用yaml-cpp支持" << std::endl;
    return false;
#endif
}

/*
 * 打印运动学参数概要
 * ================
 *
 * 功能: 打印当前加载的运动学参数
 */
inline void printParams(const KinematicsParams& params) {
    std::cout << "==========================================" << std::endl;
    std::cout << "运动学参数:" << std::endl;
    std::cout << "  [腿部几何]" << std::endl;
    std::cout << "    大腿长度 L1: " << params.L1 << " m" << std::endl;
    std::cout << "    小腿长度 L2: " << params.L2 << " m" << std::endl;
    std::cout << "    髋关节偏移: X=" << params.hip_offset_x 
              << ", Y=" << params.hip_offset_y 
              << ", Z=" << params.hip_offset_z << " m" << std::endl;
    std::cout << "    踝关节偏移: " << params.ankle_offset << " m" << std::endl;
    std::cout << "  [轮子]" << std::endl;
    std::cout << "    轮子半径: " << params.wheel_radius << " m" << std::endl;
    std::cout << "    轮距: " << params.wheel_base << " m" << std::endl;
    std::cout << "  [关节限位]" << std::endl;
    std::cout << "    髋横滚: [" << params.hip_roll_min << ", " << params.hip_roll_max << "] rad" << std::endl;
    std::cout << "    髋俯仰: [" << params.hip_pitch_min << ", " << params.hip_pitch_max << "] rad" << std::endl;
    std::cout << "    膝俯仰: [" << params.knee_pitch_min << ", " << params.knee_pitch_max << "] rad" << std::endl;
    std::cout << "==========================================" << std::endl;
}

} // namespace kinematics

#endif // WHEELED_LEGGED_KINEMATICS_H