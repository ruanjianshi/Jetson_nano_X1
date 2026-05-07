/*
 * 平衡控制算法测试程序
 * =======================
 * 输入 6 维状态，输出 8 路电机力矩
 *
 * 编译:
 *   cd /home/jetson/Desktop/Jetson_Nano
 *   g++ -std=c++17 -O2 \
 *       -I action_ws/src/balance_control/algorithms \
 *       -I action_ws/src/balance_control/include \
 *       -I /usr/include/eigen3 \
 *       action_ws/src/balance_control/test/test_balance_control.cpp \
 *       action_ws/src/balance_control/algorithms/lqr_controller.cpp \
 *       action_ws/src/balance_control/algorithms/vmc_controller.cpp \
 *       action_ws/src/balance_control/algorithms/mpc_controller.cpp \
 *       action_ws/src/balance_control/algorithms/adp_controller.cpp \
 *       -o test_balance_control
 *
 * 运行:
 *   ./test_balance_control                    # 交互模式
 *   ./test_balance_control 0 0.1 0 0 0 0      # 命令行: roll pitch yaw wx wy wz
 *   ./test_balance_control --all               # 遍历所有预设测试案例
 *
 * Author: Qi Xiao
 * Date: 2026-05-07
 */

#include <iostream>
#include <iomanip>
#include <cmath>
#include <string>
#include <vector>
#include <sstream>
#include <cstdlib>

#include "balance_algorithm_base.h"
#include "lqr_controller.h"
#include "vmc_controller.h"
#include "mpc_controller.h"
#include "adp_controller.h"

using namespace balance_control;

static const char *JOINT_NAMES[] = {
    "left_joint_1",  "left_joint_2",  "left_joint_3",  "left_joint_wheel",
    "right_joint_1", "right_joint_2", "right_joint_3", "right_joint_wheel"
};

static const char *JOINT_TYPES[] = {
    "hip_roll", "hip_pitch", "knee_pitch", "wheel",
    "hip_roll", "hip_pitch", "knee_pitch", "wheel"
};

struct TestCase {
    std::string name;
    double roll, pitch, yaw;       // 当前姿态 rad
    double wx, wy, wz;             // 角速度 rad/s
    double t_roll, t_pitch, t_yaw; // 目标姿态 rad
};

// 预设测试案例 (覆盖各种平衡场景)
static const TestCase PRESET_CASES[] = {
    {"静止直立",      0.0,  0.0,  0.0,  0.0, 0.0, 0.0,  0.0,  0.0,  0.0},
    {"前倾 5°",       0.0,  0.087,0.0,  0.0, 0.1, 0.0,  0.0,  0.0,  0.0},
    {"前倾 15°",      0.0,  0.262,0.0,  0.0, 0.3, 0.0,  0.0,  0.0,  0.0},
    {"左倾 5°",       0.087,0.0, 0.0,  0.1, 0.0, 0.0,  0.0,  0.0,  0.0},
    {"组合倾斜 5°x5°",0.087,0.087,0.0, 0.1, 0.1, 0.0,  0.0,  0.0,  0.0},
    {"偏航扰动 10°",  0.0,  0.0,  0.175,0.0, 0.0, 0.2,  0.0,  0.0,  0.0},
    {"前倾+角速度",   0.0,  0.15,0.0,  0.0, 0.5, 0.0,  0.0,  0.0,  0.0},
    {"侧倾+角速度",   0.10,0.0, 0.0,  0.5, 0.0, 0.0,  0.0,  0.0,  0.0},
    {"大扰动前倾20°", 0.0,  0.349,0.0,  0.0, 0.8, 0.0,  0.0,  0.0,  0.0},
    {"向目标5°前倾",  0.0,  0.0,  0.0,  0.0, 0.0, 0.0,  0.0,  0.087,0.0},
};

struct AlgoResult {
    std::string name;
    double output[8];
};

class TestRunner {
public:
    TestRunner() {
        // 设置默认PID参数
        AlgorithmParams params;
        params.kp_roll = 10.0;   params.kd_roll = 1.0;
        params.kp_pitch = 10.0;  params.kd_pitch = 1.0;
        params.kp_yaw = 5.0;     params.kd_yaw = 0.5;
        params.max_torque = 50.0;

        lqr_.setParams(params);
        vmc_.setParams(params);
        mpc_.setParams(params);
        adp_.setParams(params);
    }

    void runOneCase(const TestCase &tc) {
        Eigen::VectorXd state(6);
        state << tc.roll, tc.pitch, tc.yaw, tc.wx, tc.wy, tc.wz;

        Eigen::VectorXd target(6);
        target << tc.t_roll, tc.t_pitch, tc.t_yaw, 0.0, 0.0, 0.0;

        std::vector<AlgoResult> results;

        // LQR
        {
            Eigen::VectorXd out(8);
            lqr_.computeControl(state, target, out);
            results.push_back({"LQR", {out(0),out(1),out(2),out(3),out(4),out(5),out(6),out(7)}});
        }

        // VMC
        {
            Eigen::VectorXd out(8);
            vmc_.computeControl(state, target, out);
            results.push_back({"VMC", {out(0),out(1),out(2),out(3),out(4),out(5),out(6),out(7)}});
        }

        // MPC
        {
            Eigen::VectorXd out(8);
            mpc_.computeControl(state, target, out);
            results.push_back({"MPC", {out(0),out(1),out(2),out(3),out(4),out(5),out(6),out(7)}});
        }

        // ADP
        {
            Eigen::VectorXd out(8);
            adp_.computeControl(state, target, out);
            results.push_back({"ADP", {out(0),out(1),out(2),out(3),out(4),out(5),out(6),out(7)}});
        }

        // 打印表头
        std::cout << "\n==========================================================\n";
        std::cout << " 测试案例: " << tc.name << "\n";
        std::cout << "----------------------------------------------------------\n";
        std::cout << " 当前状态:  roll=" << std::setw(6) << tc.roll
                  << "  pitch=" << std::setw(6) << tc.pitch
                  << "  yaw="   << std::setw(6) << tc.yaw << " rad\n";
        std::cout << " 角速度:    wx="   << std::setw(6) << tc.wx
                  << "   wy="   << std::setw(6) << tc.wy
                  << "   wz="  << std::setw(6) << tc.wz << " rad/s\n";
        std::cout << " 目标姿态:  t_roll=" << std::setw(6) << tc.t_roll
                  << " t_pitch=" << std::setw(6) << tc.t_pitch
                  << " t_yaw="  << std::setw(6) << tc.t_yaw << " rad\n";

        // 计算误差
        double err_roll = tc.t_roll - tc.roll;
        double err_pitch = tc.t_pitch - tc.pitch;
        double err_yaw = tc.t_yaw - tc.yaw;
        std::cout << " 姿态误差:  e_roll=" << std::setw(6) << err_roll
                  << " e_pitch=" << std::setw(6) << err_pitch
                  << " e_yaw="  << std::setw(6) << err_yaw << " rad\n";

        std::cout << "----------------------------------------------------------\n";

        // 打印表头 (四列算法)
        printHeader();

        // 8行电机输出
        for (int i = 0; i < 8; ++i) {
            printMotorRow(i, results);
        }

        // 汇总行 (各算法总力矩)
        printSummary(results);

        std::cout << "==========================================================\n";

        // 简单合理性检查
        checkRationality(tc, results);
    }

    void runAllPresets() {
        for (const auto &tc : PRESET_CASES) {
            runOneCase(tc);
        }
    }

private:
    void printHeader() {
        std::cout << " " << std::left << std::setw(20) << "电机/关节"
                  << std::right;
        for (const auto &algo : {" LQR", " VMC", " MPC", " ADP"})
            std::cout << std::setw(10) << algo;
        std::cout << std::setw(10) << " 单位" << "\n";
        std::cout << " " << std::setfill('-') << std::setw(20 + 4*10 + 10) << ""
                  << std::setfill(' ') << "\n";
    }

    void printMotorRow(int idx, const std::vector<AlgoResult> &results) {
        std::cout << " " << std::left << std::setw(20)
                  << (std::string(JOINT_NAMES[idx]) + "[" + JOINT_TYPES[idx] + "]")
                  << std::right;
        for (const auto &r : results) {
            double val = r.output[idx];
            // 彩色标记: 数值越大越醒目
            const char *mark = "";
            if (std::abs(val) > 10.0) mark = "⚠";
            else if (std::abs(val) > 5.0) mark = "•";
            std::cout << std::setw(8) << std::fixed << std::setprecision(2)
                      << val << std::setw(2) << mark;
        }
        std::cout << "  Nm\n";
    }

    void printSummary(const std::vector<AlgoResult> &results) {
        std::cout << " " << std::setfill('-') << std::setw(20 + 4*10 + 10) << ""
                  << std::setfill(' ') << "\n";
        std::cout << " " << std::left << std::setw(20) << "总力矩 Σ|τ|" << std::right;
        for (const auto &r : results) {
            double sum = 0;
            for (int i = 0; i < 8; ++i) sum += std::abs(r.output[i]);
            std::cout << std::setw(10) << std::fixed << std::setprecision(2) << sum;
        }
        std::cout << "  Nm\n";

        // 最大力矩
        std::cout << " " << std::left << std::setw(20) << "最大力矩 max|τ|" << std::right;
        for (const auto &r : results) {
            double maks = 0;
            for (int i = 0; i < 8; ++i) maks = std::max(maks, std::abs(r.output[i]));
            std::cout << std::setw(10) << std::fixed << std::setprecision(2) << maks;
        }
        std::cout << "  Nm\n";
    }

    void checkRationality(const TestCase &tc, const std::vector<AlgoResult> &results) {
        std::cout << "\n [合理性检查]\n";

        double err_roll = tc.t_roll - tc.roll;
        double err_pitch = tc.t_pitch - tc.pitch;
        double err_yaw = tc.t_yaw - tc.yaw;

        for (const auto &r : results) {
            bool ok = true;
            std::string issues;

            // 前倾(pitch误差<0) → 左轮右轮应正力矩(加速前转,反力推回)
            if (err_pitch < -0.01) {
                if (r.output[3] < 0.1) { issues += " 前倾左轮无补偿"; ok = false; }
                if (r.output[7] < 0.1) { issues += " 前倾右轮无补偿"; ok = false; }
            }
            // 后仰(pitch误差>0) → 轮应负力矩(减速/后退)
            if (err_pitch > 0.01) {
                if (r.output[3] > -0.1) { issues += " 后仰左轮无补偿"; ok = false; }
                if (r.output[7] > -0.1) { issues += " 后仰右轮无补偿"; ok = false; }
            }

            // 左倾 (roll>0, 误差<0) → 左hip_roll应正, 右hip_roll应负
            if (err_roll < -0.01) {
                if (r.output[0] < 0.1) { issues += " 左倾左髋无补偿"; ok = false; }
                if (r.output[4] > -0.1) { issues += " 左倾右髋无补偿"; ok = false; }
            }
            if (err_roll > 0.01) {
                if (r.output[0] > -0.1) { issues += " 右倾左髋反向异常"; ok = false; }
                if (r.output[4] < 0.1) { issues += " 右倾右髋反向异常"; ok = false; }
            }

            // 偏航误差 → 两轮应有差动
            if (std::abs(err_yaw) > 0.01) {
                double whl_err = r.output[3] - r.output[7];  // 左轮-右轮
                if (std::abs(whl_err) < 1e-3) {
                    issues += " 偏航无轮差动补偿";
                    ok = false;
                }
            }
            // 输出在合理范围?
            for (int i = 0; i < 8; ++i) {
                if (std::abs(r.output[i]) > 100.0) {
                    issues += " 力矩过大(>" + std::to_string((int)std::abs(r.output[i])) + "Nm)";
                    ok = false;
                    break;
                }
            }

            // 接近零误差时不应输出过大
            if (std::abs(err_roll) < 0.005 && std::abs(err_pitch) < 0.005) {
                double sum = 0;
                for (int i = 0; i < 8; ++i) sum += std::abs(r.output[i]);
                if (sum > 5.0) {
                    issues += " 零误差输出偏大";
                    ok = false;
                }
            }

            // 左右对称性
            double roll_asym = std::abs(r.output[0] + r.output[4]);
            double wheel_sym = std::abs(r.output[3] - r.output[7]);  // 轮差动(来自yaw)
            if (std::abs(err_roll) > 0.01 && roll_asym > 1.5) {
                issues += " roll反对称异常(Σ=" + std::to_string((int)roll_asym) + ")";
                ok = false;
            }
            if (std::abs(err_pitch) > 0.01 && r.output[3] < 0.1 && r.output[7] < 0.1) {
                // 已在上面检查过
            }

            std::cout << "   " << std::left << std::setw(5) << r.name
                      << " " << (ok ? "✅ 合理" : "⚠️ " + issues) << "\n";
        }
    }

    LQRController lqr_;
    VMCController vmc_;
    MPCController mpc_;
    ADPController adp_;
};

void printUsage(const char *prog) {
    std::cout << "用法:\n"
              << "  " << prog << "                   交互模式\n"
              << "  " << prog << " --all              遍历所有预设测试案例\n"
              << "  " << prog << " roll pitch yaw wx wy wz [t_roll t_pitch t_yaw]\n"
              << "  " << prog << " --list             列出预设案例\n"
              << "\n参数:\n"
              << "  roll, pitch, yaw  - 当前姿态角 (rad)\n"
              << "  wx, wy, wz        - 角速度 (rad/s)\n"
              << "  t_roll, t_pitch, t_yaw - 目标姿态角 (默认 0)\n";
}

int main(int argc, char **argv) {
    TestRunner runner;

    if (argc < 2) {
        // 交互模式
        printUsage(argv[0]);
        std::cout << "\n进入交互模式...\n";

        while (true) {
            std::cout << "\n输入状态 (roll pitch yaw wx wy wz) 或 q 退出:\n> ";
            std::string line;
            std::getline(std::cin, line);
            if (line.empty() || line == "q" || line == "quit") break;

            TestCase tc = {"交互输入", 0, 0, 0, 0, 0, 0, 0, 0, 0};
            std::istringstream iss(line);
            iss >> tc.roll >> tc.pitch >> tc.yaw >> tc.wx >> tc.wy >> tc.wz;
            if (!iss.fail()) {
                // 可选目标姿态
                iss >> tc.t_roll >> tc.t_pitch >> tc.t_yaw;
            }
            runner.runOneCase(tc);
        }
        return 0;
    }

    std::string arg1 = argv[1];

    if (arg1 == "--all") {
        runner.runAllPresets();
    } else if (arg1 == "--list") {
        std::cout << "预设测试案例:\n";
        for (size_t i = 0; i < sizeof(PRESET_CASES)/sizeof(PRESET_CASES[0]); ++i) {
            const auto &tc = PRESET_CASES[i];
            std::cout << "  [" << i << "] " << std::left << std::setw(20) << tc.name
                      << " roll=" << std::setw(5) << tc.roll
                      << " pitch=" << std::setw(5) << tc.pitch
                      << " yaw=" << std::setw(5) << tc.yaw
                      << " | wx=" << std::setw(4) << tc.wx
                      << " wy=" << std::setw(4) << tc.wy
                      << " wz=" << std::setw(4) << tc.wz
                      << " | t_roll=" << tc.t_roll
                      << " t_pitch=" << tc.t_pitch
                      << " t_yaw=" << tc.t_yaw << "\n";
        }
    } else if (argc >= 7) {
        TestCase tc = {"命令行输入", 0, 0, 0, 0, 0, 0, 0, 0, 0};
        tc.roll = std::atof(argv[1]);
        tc.pitch = std::atof(argv[2]);
        tc.yaw = std::atof(argv[3]);
        tc.wx = std::atof(argv[4]);
        tc.wy = std::atof(argv[5]);
        tc.wz = std::atof(argv[6]);
        if (argc >= 10) {
            tc.t_roll = std::atof(argv[7]);
            tc.t_pitch = std::atof(argv[8]);
            tc.t_yaw = std::atof(argv[9]);
        }
        runner.runOneCase(tc);
    } else {
        printUsage(argv[0]);
    }

    return 0;
}
