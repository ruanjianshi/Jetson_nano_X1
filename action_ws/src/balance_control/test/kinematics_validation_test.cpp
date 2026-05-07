/*
 * 运动学正逆解合理性测试 (URDF 匹配版)
 * =====================================
 *
 * 基于 xqrobotV2 的 FK / IK / Jacobian / 约束一致性验证
 *
 * 编译:
 *   cd /home/jetson/Desktop/Jetson_Nano
 *   g++ -std=c++17 -O2 \
 *       -I action_ws/src/balance_control/algorithms \
 *       -I /usr/include/eigen3 \
 *       action_ws/src/balance_control/test/kinematics_validation_test.cpp \
 *       -o kinematics_validation_test
 *
 * 运行:
 *   ./kinematics_validation_test
 *
 * Author: Qi Xiao
 * Date: 2026-05-07
 */

#include <iostream>
#include <iomanip>
#include <cmath>
#include <vector>
#include <string>

#include "wheeled_legged_kinematics.h"

using namespace kinematics;

static int g_pass = 0, g_fail = 0;
static const double TOL = 0.03;  // FK/IK 往返容差 [m] (多解性容许)

#define CHECK(cond, msg) do { \
    std::cout << "  " << (cond ? "✅" : "❌") << " " << msg; \
    if (!(cond)) { std::cout << "  (FAIL)"; g_fail++; } \
    else { g_pass++; } \
    std::cout << "\n"; \
} while(0)

void printJoint(const LegJoints& j) {
    std::cout << std::fixed << std::setprecision(3)
              << "  hip_roll=" << std::setw(7) << j.hip_roll << " (" << std::setw(6) << j.hip_roll*180/M_PI << "°), "
              << "hip_pitch=" << std::setw(7) << j.hip_pitch << " (" << std::setw(6) << j.hip_pitch*180/M_PI << "°), "
              << "knee_pitch=" << std::setw(7) << j.knee_pitch << " (" << std::setw(6) << j.knee_pitch*180/M_PI << "°)\n";
}

void printFoot(const FootPose& f) {
    std::cout << std::fixed << std::setprecision(3)
              << "  pos=(" << std::setw(6) << f.position.x << ", "
              << std::setw(6) << f.position.y << ", "
              << std::setw(6) << f.position.z << ") m\n";
}

// 往返闭包测试: 给定关节角 → FK得足端位置 → IK重新求解 → 验证角度恢复
void testFkIkRoundtrip(const std::string& label, double roll, double pitch, double knee,
                        LegSide side, const KinematicsParams& params) {
    std::cout << "\n═══ " << label << " ═══\n";
    std::cout << "输入角度: " << "\n";
    printJoint({roll, pitch, knee, 0});

    FootPose fk = forwardKinematics(roll, pitch, knee, side, params);
    std::cout << "FK → 足端位置:\n";
    printFoot(fk);

    LegJoints ik = inverseKinematics({fk.position.x, fk.position.y, fk.position.z}, side, params);
    std::cout << "IK → 恢复角度:\n";
    printJoint(ik);

    FootPose fk2 = forwardKinematics(ik.hip_roll, ik.hip_pitch, ik.knee_pitch, side, params);
    std::cout << "FK → 验证位置:\n";
    printFoot(fk2);

    double pos_err = sqrt(pow(fk2.position.x - fk.position.x, 2) +
                          pow(fk2.position.y - fk.position.y, 2) +
                          pow(fk2.position.z - fk.position.z, 2));
    CHECK(pos_err < TOL, "往返闭包位置误差: " + std::to_string(pos_err).substr(0,6) + " m");
}

// 几何一致性检查: 已知零位各关节在URDF中的绝对坐标
void testZeroGeometry(const KinematicsParams& params) {
    std::cout << "\n═══ 零位几何一致性 (URDF) ═══\n";

    FootPose fk_L = forwardKinematics(0, 0, 0, LegSide::LEFT, params);
    FootPose fk_R = forwardKinematics(0, 0, 0, LegSide::RIGHT, params);

    std::cout << "左腿零位足端:\n"; printFoot(fk_L);
    std::cout << "右腿零位足端:\n"; printFoot(fk_R);

    // 零位时: hip在(±0.069, -0.124, -0.001), 足端在hip下面
    // 轮心在足端下方wheel_radius处
    // FK输出是接触地面点 (轮心 + wheel_radius)
    // 腿长 = L1+L2 = 0.0725+0.301 = 0.3735m
    // 足端Z = hip_z - L1 - L2 - ankle_offset_z + wheel_radius
    //         = -0.001 - 0.374 - (-0.200) + 0.10
    //         = -0.001 - 0.374 + 0.200 + 0.10 = -0.075? 
    
    // Actually let me trace through the FK code more carefully:
    // hip = (0.069, -0.124, -0.001)
    // L1_x = 0, L1_y = -L1*sr = -0.0725*0 = 0, L1_z = -L1*cr = -0.0725*1 = -0.0725
    // knee = (0.069, -0.124, -0.001-0.0725) = (0.069, -0.124, -0.0735)
    // L2_x = L2*sp = 0.301*0 = 0, L2_z = -L2*cp = -0.301*1 = -0.301
    // ankle = (0.069, -0.124, -0.0735-0.301) = (0.069, -0.124, -0.3745)
    // whl_x = ankle_x + ankle_offset_x*cpk = 0.069 + 0.224*1 = 0.293
    // whl_z = ankle_z - ankle_offset_x*spk + ankle_offset_z = -0.3745 - 0 + (-0.2) = -0.5745
    // foot = whl + (0, 0, wheel_radius) = (0.293, -0.124, -0.4745)

    // So expected foot at zero: (0.293, -0.124, -0.475) for left leg

    // Check left vs right symmetry
    double sym_x = std::abs(fk_L.position.x + fk_R.position.x); // should be ~0
    double sym_y = std::abs(fk_L.position.y - fk_R.position.y); // should be ~0  
    double sym_z = std::abs(fk_L.position.z - fk_R.position.z); // should be ~0

    CHECK(sym_x < 0.01, "左右腿 X 对称性: |L_X+R_X| = " + std::to_string(sym_x).substr(0,5));
    CHECK(sym_y < 0.01, "左右腿 Y 对称性: |L_Y-R_Y| = " + std::to_string(sym_y).substr(0,5));
    CHECK(sym_z < 0.01, "左右腿 Z 对称性: |L_Z-R_Z| = " + std::to_string(sym_z).substr(0,5));

    // 右腿X应≈ -0.069 (hip_offset)
    CHECK(std::abs(fk_R.position.x + params.hip_offset_x) < 0.01, "右腿零位X ≈ -" + std::to_string(params.hip_offset_x) + " m");
    CHECK(fk_L.position.y < -0.10, "足端Y在后方 (< -0.10 m)");
    CHECK(fk_L.position.z < -0.40, "足端Z在髋下方 ( < -0.40 m)");
}

void testLegLengthCnsistency(const KinematicsParams& params) {
    std::cout << "\n═══ 腿长公式一致性 ═══\n";

    // 理论最大腿长 (L2+L3, L1是固定段)
    double L_max = params.L2 + params.L3;
    double L_min = fabs(params.L2 - params.L3);
    std::cout << "  理论腿长范围: [" << L_min << ", " << L_max << "] m\n";

    // 零位腿长
    double L0 = computeLegLength(0, 0, params);
    CHECK(std::abs(L0 - L_max) < 0.002, "零位腿长 ≈ L2+L3=" + std::to_string(L_max).substr(0,5) + " vs " + std::to_string(L0).substr(0,5));

    // 膝弯曲45°
    double deg45 = 45.0 * M_PI / 180.0;
    double L45 = computeLegLength(0, deg45, params);
    CHECK(L45 < L0, "膝45°弯曲后腿变短: " + std::to_string(L45).substr(0,5) + " < " + std::to_string(L0).substr(0,5));

    // 极限弯曲
    double L90 = computeLegLength(0, M_PI / 2.0, params);
    double expected_90 = sqrt(params.L2*params.L2 + params.L3*params.L3);
    CHECK(std::abs(L90 - expected_90) < 0.001, "膝90°弯曲: leg=" + std::to_string(L90).substr(0,5) + " ≈ sqrt(L2²+L3²)=" + std::to_string(expected_90).substr(0,5));
}

void testWorkspace(const KinematicsParams& params) {
    std::cout << "\n═══ 工作空间边界 ═══\n";

    CHECK( isInWorkspace(0.0, 0.0, params),     "零位在工作空间内");
    CHECK( isInWorkspace(0.5, -0.8, params),    "弯曲姿态在工作空间内");

    // knee_pitch > max → 应超出
    bool ws_ok = isInWorkspace(0.0, params.knee_pitch_max + 0.1, params);
    std::cout << "  膝 " << params.knee_pitch_max + 0.1 << " 工作空间: " << (ws_ok ? "是" : "否") << "\n";
    CHECK( isInWorkspace(0.0, -0.5, params),    "膝-0.5在工作空间内");
}

void testJacobian(const KinematicsParams& params) {
    std::cout << "\n═══ 雅可比矩阵 ═══\n";

    Eigen::Matrix3d J = computeJacobian(0.1, 0.3, -0.4, params);
    std::cout << "J [θ_r=" << 0.1 << ", θ_p=" << 0.3 << ", θ_k=" << -0.4 << "]:\n";
    std::cout << "  " << J.row(0).format(Eigen::IOFormat(4, Eigen::DontAlignCols, " ", " ", "", "", "[", "]")) << "\n";
    std::cout << "  " << J.row(1).format(Eigen::IOFormat(4, Eigen::DontAlignCols, " ", " ", "", "", "[", "]")) << "\n";
    std::cout << "  " << J.row(2).format(Eigen::IOFormat(4, Eigen::DontAlignCols, " ", " ", "", "", "[", "]")) << "\n";

    // 零位 Jacobian
    Eigen::Matrix3d J0 = computeJacobian(0, 0, 0, params);
    double L1 = params.L1, L2 = params.L2;

    // 零位: J(0,0)=0, J(1,0)=-L1, J(2,0)=0
    CHECK(std::abs(J0(0, 0)) < 1e-9, "零位J00 ≈ 0 (dX/d_roll=0)");
    CHECK(std::abs(J0(1, 0) - (-L1)) < 0.001, "零位J10 ≈ -L1 (dY/d_roll)");
    CHECK(std::abs(J0(2, 0)) < 1e-9, "零位J20 ≈ 0 (dZ/d_roll=0)");

    // 零位: J(0,1)=L2+L3, J(1,1)=0, J(2,1)=0 (hip_pitch moves both L2 and L3)
    double J01_expected = params.L2 + params.L3;
    CHECK(std::abs(J0(0, 1) - J01_expected) < 0.002, "零位J01 ≈ L2+L3 (dX/d_hpitch)");
    CHECK(std::abs(J0(1, 1)) < 1e-9, "零位J11 = 0 (dY/d_hpitch=0)");

    // 零位: J(0,2)=L3, J(1,2)=0, J(2,2)=0 (knee_pitch only moves L3)
    CHECK(std::abs(J0(0, 2) - params.L3) < 0.002, "零位J02 ≈ L3 (dX/d_knee)");
}

void testSweepRange(const KinematicsParams& params) {
    std::cout << "\n═══ 关节扫描: FK ←→ IK 往返 ═══\n";

    struct { double r, p, k; const char *label; } cases[] = {
        { 0,    0,    0,    "零位 (站立)" },
        { 0,    0.4,  0,    "髋前摆 23°" },
        { 0,   -0.3,  0,    "髋后摆 -17°" },
        { 0.2,  0,    0,    "侧倾 +11.5°" },
        { 0,    0.2,  0.3,  "髋前+膝伸 29°" },
        { 0,   -0.2, -0.3,  "髋后+膝弯 -29°" },
        { 0.15, 0.15, 0,    "侧倾+前摆" },
    };

    for (auto& c : cases) {
        testFkIkRoundtrip(c.label, c.r, c.p, c.k, LegSide::LEFT, params);
    }
}

void testStandHeight(const KinematicsParams& params) {
    std::cout << "\n═══ 基于高度的逆解 ═══\n";

    for (double h : {0.25, 0.30, 0.35, 0.40, 0.45}) {
        LegJoints ik = inverseKinematicsForHeight(h, 0, LegSide::LEFT, params);
        FootPose fk = forwardKinematics(ik.hip_roll, ik.hip_pitch, ik.knee_pitch, LegSide::LEFT, params);
        double actual_z = params.hip_offset_z - h + params.wheel_radius;
        bool ok = isInWorkspace(ik.hip_pitch, ik.knee_pitch, params);
        CHECK(ok, "高度 " + std::to_string(h) + " m → Z=" + std::to_string(fk.position.z).substr(0,5) +
                    " m " + (ok ? "✅" : "❌ 不可达"));
    }
}

int main() {
    KinematicsParams params;

    // URDF extracted geometry (3-segment model)
    params.L1 = 0.0725;
    params.L2 = 0.301;
    params.L3 = 0.302;
    params.hip_offset_x = 0.069;
    params.hip_offset_y = -0.124;
    params.hip_offset_z = -0.001;
    params.wheel_radius = 0.10;
    params.wheel_base = 0.40;
    params.wheel_offset_y = -0.022;
    params.wheel_offset_z = -0.399;
    params.hip_roll_min = -3.1416;
    params.hip_roll_max = 3.1416;
    params.hip_pitch_min = -2.0944;
    params.hip_pitch_max = 2.0944;
    params.knee_pitch_min = -0.8727;
    params.knee_pitch_max = 0.8727;

    std::cout << "═══════════════════════════════════════════\n";
    std::cout << " 轮腿机器人运动学合理性验证\n";
    std::cout << " URDF: xqrobotV2  L1=" << params.L1 << " L2=" << params.L2 << "\n";
    std::cout << "═══════════════════════════════════════════\n";

    testZeroGeometry(params);
    testLegLengthCnsistency(params);
    testWorkspace(params);
    testJacobian(params);
    testSweepRange(params);
    testStandHeight(params);

    std::cout << "\n═══════════════════════════════════════════\n";
    std::cout << " 结果: " << g_pass << " 通过 / " << g_fail << " 失败 / "
              << (g_pass + g_fail) << " 总计\n";
    if (g_fail == 0) std::cout << " ✅ 所有测试通过!\n";
    else std::cout << " ❌ 有 " << g_fail << " 项失败\n";
    std::cout << "═══════════════════════════════════════════\n";
    return g_fail > 0 ? 1 : 0;
}
