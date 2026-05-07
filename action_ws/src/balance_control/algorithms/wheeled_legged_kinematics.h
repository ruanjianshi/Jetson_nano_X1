/*
 * 轮腿机器人运动学模型 (基于 xqrobotV2 URDF)
 * ===========================================
 *
 * 提供双足轮腿机器人的正逆运动学解算接口
 *
 * URDF 架构:
 *   base_link → joint_1 (X轴) → link_1 → joint_2 (Y轴) → link_2
 *            → joint_3 (Y轴) → link_3 → joint_wheel (Y轴) → wheel
 *
 * 坐标系定义 (机体坐标系 B frame):
 *   Z (上)
 *   ↑   Y (后方)
 *   │  ↗
 *   └──→ X (右)
 *
 * 关节旋转轴 (严格从 URDF 提取):
 *   hip_roll  (joint_1):  绕 ±X 轴 → 腿在 YZ 平面摆动 (前后/上下)
 *   hip_pitch (joint_2):  绕 ±Y 轴 → 腿在 XZ 平面摆动 (左右/上下)
 *   knee_pitch(joint_3):  绕 ±Y 轴 → 小腿在 XZ 平面弯曲
 *   wheel     (joint_w):  绕 ±Y 轴 → 轮子转动
 *
 * URDF 几何参数 (从 robot.urdf 提取):
 *   L1 = 髋→膝距离 ≈ 0.0725 m
 *   L2 = 膝→踝距离 ≈ 0.301 m
 *   髋偏移 X: ±0.069 m, Y: -0.124 m, Z: -0.001 m
 *   轮子半径: 0.10 m (估计,轮质量 2.32kg)
 *   总质量: base=5.41 + 2×(0.174+0.673+0.420+2.323) = 12.59 kg
 *
 * Author: Qi Xiao
 * Email: 2408128687@qq.com
 * 日期: 2026-05-06
 * 修订: 2026-05-07 (基于 URDF 重写)
 */

#ifndef WHEELED_LEGGED_KINEMATICS_H
#define WHEELED_LEGGED_KINEMATICS_H

#include <Eigen/Dense>
#include <string>
#include <vector>
#include <iostream>

namespace kinematics {

enum class JointIndex {
    HIP_ROLL = 0,
    HIP_PITCH = 1,
    KNEE_PITCH = 2,
    WHEEL = 3
};

enum class LegSide {
    LEFT = 0,
    RIGHT = 1
};

struct Vec3 {
    double x, y, z;
};

struct LegJoints {
    double hip_roll;
    double hip_pitch;
    double knee_pitch;
    double wheel;

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

struct FootPose {
    Vec3 position;
    Vec3 orientation;

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

struct RobotState {
    LegJoints left_leg;
    LegJoints right_leg;

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

/*
 * 运动学参数 (URDF 提取)
 *
 * 关键几何:
 *   joint_1 origin: ( ±0.069, -0.124, -0.001 )  → 髋关节
 *   joint_2 in link_1: ( -0.070, -0.020, 0.000 )  → L1 ≈ 0.073
 *   joint_3 in link_2: ( -0.224, +0.015, -0.200 )  → L2 ≈ 0.301
 *   joint_w in link_3: ( +0.224, -0.037, -0.199 )  → L3 ≈ 0.302
 *   (X偏移在j3→wheel段被抵消, net X ≈ 0)
 *
 *   轮半径: ~0.10 m (link_wheel 质量 2.32kg 估算)
 */
struct KinematicsParams {
    double L1 = 0.0725;             // 髋→膝 (URDF: |j1→j2|)
    double L2 = 0.301;              // 膝→踝 (URDF: |j2→j3|)
    double L3 = 0.302;              // 踝→轮心 (URDF: |j3→wheel|)

    double hip_offset_x = 0.069;    // 髋横向偏移 ±X
    double hip_offset_y = -0.124;   // 髋纵向偏移  Y
    double hip_offset_z = -0.001;   // 髋垂向偏移  Z

    double wheel_radius = 0.10;     // 轮半径 [m]
    double wheel_base = 0.40;       // 轮距 [m]

    // 踝→轮净偏移 (URDF: j3(-0.224,+0.015,-0.200) → jw(+0.224,-0.037,-0.199))
    // Net X=0, Y=-0.022, Z=-0.399
    double wheel_offset_y = -0.022; // 轮心Y偏移
    double wheel_offset_z = -0.399; // 膝→轮心总Z偏移

    double hip_roll_min = -1.57;
    double hip_roll_max = 1.57;
    double hip_pitch_min = -1.047;  // URDF: lower=-1.047
    double hip_pitch_max = 2.094;   // URDF: upper=2.094
    double knee_pitch_min = -0.873; // URDF: lower=-0.873
    double knee_pitch_max = 0.873;  // URDF: upper=0.873

    EIGEN_MAKE_ALIGNED_OPERATOR_NEW
};

/*
 * 正向运动学 (关节角度 → 轮/足位姿)
 *
 * 3段链路: hip→knee(L1) → ankle(L2) → wheel(L3) → foot_contact(+wheel_radius)
 * 旋转轴: hip_roll=±X, hip_pitch=±Y, knee_pitch=±Y
 */
inline FootPose forwardKinematics(double hip_roll, double hip_pitch, double knee_pitch,
                                   LegSide leg_side, const KinematicsParams& params) {
    FootPose foot;
    double side_sign = (leg_side == LegSide::LEFT) ? 1.0 : -1.0;

    double cr = cos(hip_roll), sr = sin(hip_roll);
    double cp = cos(hip_pitch), sp = sin(hip_pitch);
    double cpt = cos(hip_pitch + knee_pitch), spt = sin(hip_pitch + knee_pitch);

    // 髋在机体坐标系中的位置
    double hx = side_sign * params.hip_offset_x;
    double hy = params.hip_offset_y;
    double hz = params.hip_offset_z;

    // L1 (hip→knee): 初始沿-Z, 绕X(hip_roll)旋转
    double kx = hx;
    double ky = hy - params.L1 * sr;
    double kz = hz - params.L1 * cr;

    // L2 (knee→ankle): 初始沿-Z, 绕Y(hip_pitch)旋转
    double ax = kx + params.L2 * sp;
    double ay = ky;
    double az = kz - params.L2 * cp;

    // L3 (ankle→wheel): 初始沿-Z, 绕Y(hip_pitch+knee_pitch)旋转
    double wx = ax + params.L3 * spt;
    double wy = ay + params.wheel_offset_y;
    double wz = az - params.L3 * cpt + params.wheel_offset_z;

    foot.position.x = wx;
    foot.position.y = wy;
    foot.position.z = wz + params.wheel_radius;

    return foot;
}

/*
 * 正向运动学 2D (矢状面 Y-Z)
 */
inline Vec3 forwardKinematics2D(double hip_roll, double hip_pitch, double knee_pitch,
                                 const KinematicsParams& params) {
    Vec3 pos;
    double cr = cos(hip_roll), sr = sin(hip_roll);
    double cpt = cos(hip_pitch + knee_pitch), spt = sin(hip_pitch + knee_pitch);

    pos.x = params.L2 * sin(hip_pitch) + params.L3 * spt;
    pos.y = params.hip_offset_y - params.L1 * sr + params.wheel_offset_y;
    pos.z = params.hip_offset_z - params.L1 * cr - params.L2 * cos(hip_pitch)
            - params.L3 * cpt + params.wheel_offset_z + params.wheel_radius;
    return pos;
}

/*
 * 逆向运动学 (解析解)
 * 给定期望轮心位置 → 计算各关节角度
 *
 * 模型: 3段链路 (L1固定, L2+L3按knee_pitch弯曲)
 */
inline LegJoints inverseKinematics(const Vec3& foot_pos, LegSide leg_side,
                                    const KinematicsParams& params) {
    LegJoints joints;

    double side_sign = (leg_side == LegSide::LEFT) ? 1.0 : -1.0;

    // 轮心位置 = 足端 - wheel_radius
    double wx = foot_pos.x - side_sign * params.hip_offset_x;
    double wy = foot_pos.y - params.hip_offset_y - params.wheel_offset_y;
    double wz = foot_pos.z - params.hip_offset_z - params.wheel_radius - params.wheel_offset_z;

    // hip_roll: 绕X旋转 → atan2(-wy, -wz)
    joints.hip_roll = atan2(-wy, -wz);
    joints.hip_roll = std::max(params.hip_roll_min,
                      std::min(params.hip_roll_max, joints.hip_roll));

    double cr = cos(joints.hip_roll), sr = sin(joints.hip_roll);

    // 在hip_roll旋转后的YZ坐标
    double yr = wy * cr - wz * sr;   // Y在旋转后 → 对应L1在YZ平面的投影
    double zr = wy * sr + wz * cr;   // Z在旋转后

    // L1固定, 解L2+L3
    double L_total = sqrt(wx * wx + yr * yr + zr * zr);
    L_total = std::max(params.L1 - params.L2 + 0.01, std::min(params.L1 + params.L2 + params.L3, L_total));

    // knee→wheel有效距离 = L_total - L1 (均为沿Z方向)
    double L23_eff = L_total - params.L1;
    L23_eff = std::max(fabs(params.L2 - params.L3),
               std::min(params.L2 + params.L3, L23_eff));

    // 余弦定理 L3² = L2² + L_eff² - 2·L2·L_eff·cos(phi)
    double cos_phi = (params.L2 * params.L2 + L23_eff * L23_eff - params.L3 * params.L3)
                     / (2.0 * params.L2 * L23_eff);
    cos_phi = std::max(-1.0, std::min(1.0, cos_phi));
    double phi = acos(cos_phi);

    // L_eff与垂直方向的夹角
    double gamma = atan2(wx, -zr);

    joints.hip_pitch = gamma - phi;
    joints.hip_pitch = std::max(params.hip_pitch_min,
                       std::min(params.hip_pitch_max, joints.hip_pitch));

    // 膝盖角度
    double cos_beta = (params.L2 * params.L2 + params.L3 * params.L3 - L23_eff * L23_eff)
                      / (2.0 * params.L2 * params.L3);
    cos_beta = std::max(-1.0, std::min(1.0, cos_beta));
    joints.knee_pitch = M_PI - acos(cos_beta);
    joints.knee_pitch = std::max(params.knee_pitch_min,
                        std::min(params.knee_pitch_max, joints.knee_pitch));

    joints.wheel = 0.0;

    return joints;
}

/*
 * 基于高度的逆向运动学
 * body_height: 机体离地高度 [m], body_pitch: 俯仰角 [rad]
 * 
 * 目标足端位置: 正下方 body_height 处, 稍偏后(Y方向)
 */
inline LegJoints inverseKinematicsForHeight(double body_height, double body_pitch,
                                             LegSide leg_side, const KinematicsParams& params) {
    Vec3 foot_pos;
    double side_sign = (leg_side == LegSide::LEFT) ? 1.0 : -1.0;

    foot_pos.x = side_sign * params.hip_offset_x;
    foot_pos.y = params.hip_offset_y - body_pitch * body_height * 0.3;
    foot_pos.z = params.hip_offset_z - body_height;   // foot = wheel_contact = hip_height - body_height

    return inverseKinematics(foot_pos, leg_side, params);
}

/*
 * 雅可比矩阵 (3x3): d(position)/d(hip_roll, hip_pitch, knee_pitch)
 */
inline Eigen::Matrix3d computeJacobian(double hip_roll, double hip_pitch, double knee_pitch,
                                        const KinematicsParams& params) {
    Eigen::Matrix3d J;
    double cr = cos(hip_roll), sr = sin(hip_roll);
    double sp = sin(hip_pitch), cp = cos(hip_pitch);
    double st = sin(hip_pitch + knee_pitch), ct = cos(hip_pitch + knee_pitch);
    double L1 = params.L1, L2 = params.L2, L3 = params.L3;

    // d/d_hip_roll: 绕X
    J(0, 0) = 0.0;
    J(1, 0) = -L1 * cr;
    J(2, 0) = L1 * sr;

    // d/d_hip_pitch: 绕Y
    J(0, 1) = L2 * cp + L3 * ct;
    J(1, 1) = 0.0;
    J(2, 1) = L2 * sp + L3 * st;

    // d/d_knee_pitch: 绕Y
    J(0, 2) = L3 * ct;
    J(1, 2) = 0.0;
    J(2, 2) = L3 * st;

    return J;
}

inline Eigen::Vector2d inverseJacobian(const Eigen::Vector2d& foot_vel,
                                        double hip_pitch, double knee_pitch,
                                        const KinematicsParams& params) {
    double L2 = params.L2;
    double sp = sin(hip_pitch), cp = cos(hip_pitch);
    double sk = sin(knee_pitch), ck = cos(knee_pitch);

    Eigen::Matrix2d J;
    J << L2 * cp, L2 * ck,
         L2 * sp, L2 * sk;

    return J.inverse() * foot_vel;
}

inline double computeLegLength(double hip_pitch, double knee_pitch, const KinematicsParams& params) {
    double angle_sum = hip_pitch + knee_pitch;
    double L2 = params.L2, L3 = params.L3;
    return sqrt(L2 * L2 + L3 * L3 - 2.0 * L2 * L3 * cos(M_PI - knee_pitch));
}

inline bool isInWorkspace(double hip_pitch, double knee_pitch, const KinematicsParams& params) {
    double leg_len = computeLegLength(hip_pitch, knee_pitch, params);
    double L_max = params.L2 + params.L3;
    double L_min = fabs(params.L2 - params.L3);
    return (leg_len >= L_min - 0.001 && leg_len <= L_max + 0.001);
}

inline LegJoints interpolateJoints(const LegJoints& a, const LegJoints& b, double t,
                                    const KinematicsParams& params) {
    t = std::max(0.0, std::min(1.0, t));
    LegJoints r;
    r.hip_roll = a.hip_roll + t * (b.hip_roll - a.hip_roll);
    r.hip_pitch = a.hip_pitch + t * (b.hip_pitch - a.hip_pitch);
    r.knee_pitch = a.knee_pitch + t * (b.knee_pitch - a.knee_pitch);
    r.wheel = a.wheel + t * (b.wheel - a.wheel);
    return r;
}

inline void loadParams(KinematicsParams& params, double L1, double L2, double L3,
                       double hip_offset_x, double hip_offset_y, double hip_offset_z,
                       double wheel_radius) {
    params.L1 = L1;
    params.L2 = L2;
    params.L3 = L3;
    params.hip_offset_x = hip_offset_x;
    params.hip_offset_y = hip_offset_y;
    params.hip_offset_z = hip_offset_z;
    params.wheel_radius = wheel_radius;
}

inline void printParams(const KinematicsParams& params) {
    std::cout << "==========================================" << std::endl;
    std::cout << "运动学参数 (URDF 提取):" << std::endl;
    std::cout << "  L1 (髋→膝): " << params.L1 << " m" << std::endl;
    std::cout << "  L2 (膝→踝): " << params.L2 << " m" << std::endl;
    std::cout << "  L3 (踝→轮): " << params.L3 << " m" << std::endl;
    std::cout << "  髋偏移: X=±" << params.hip_offset_x
              << ", Y=" << params.hip_offset_y
              << ", Z=" << params.hip_offset_z << " m" << std::endl;
    std::cout << "  轮偏移: Y=" << params.wheel_offset_y
              << ", Z=" << params.wheel_offset_z << " m" << std::endl;
    std::cout << "  轮半径: " << params.wheel_radius << " m" << std::endl;
    std::cout << "  轮距: " << params.wheel_base << " m" << std::endl;
    std::cout << "  总可达: " << params.L1 + params.L2 + params.L3 << " m" << std::endl;
    std::cout << "  关节限位:" << std::endl;
    std::cout << "    hip_roll:  [" << params.hip_roll_min << ", " << params.hip_roll_max << "]" << std::endl;
    std::cout << "    hip_pitch: [" << params.hip_pitch_min << ", " << params.hip_pitch_max << "]" << std::endl;
    std::cout << "    knee_pitch:[" << params.knee_pitch_min << ", " << params.knee_pitch_max << "]" << std::endl;
    std::cout << "==========================================" << std::endl;
}

} // namespace kinematics

#endif // WHEELED_LEGGED_KINEMATICS_H
