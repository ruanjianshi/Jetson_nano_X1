#!/bin/bash
# ===========================================
# 平衡控制算法测试 - 编译与运行脚本
# ===========================================
#
# 用法:
#   ./run_tests.sh              # 编译并运行所有预设案例
#   ./run_tests.sh --interactive # 构建后进入交互模式
#   ./run_tests.sh --list        # 列出预设案例
#   ./run_tests.sh 0 0.2 0 0 0 0 # 自定义状态输入
#
# 输出: 8路电机力矩 (LQR vs VMC vs MPC vs ADP) + 合理性检查
# ===========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
WS_DIR="/home/jetson/Desktop/Jetson_Nano"
BIN_NAME="test_balance_control"

echo "=========================================="
echo " 平衡控制算法测试"
echo "=========================================="

# 编译
echo "[1/2] 编译测试程序..."
g++ -std=c++17 -O2 \
    -I"${PKG_DIR}/algorithms" \
    -I"${PKG_DIR}/include" \
    -I/usr/include/eigen3 \
    "${SCRIPT_DIR}/test_balance_control.cpp" \
    "${PKG_DIR}/algorithms/lqr_controller.cpp" \
    "${PKG_DIR}/algorithms/vmc_controller.cpp" \
    "${PKG_DIR}/algorithms/mpc_controller.cpp" \
    "${PKG_DIR}/algorithms/adp_controller.cpp" \
    -o "${WS_DIR}/${BIN_NAME}"

echo " 编译成功 -> ${WS_DIR}/${BIN_NAME}"
echo ""

# 运行
echo "[2/2] 运行测试..."
echo ""

if [ $# -eq 0 ]; then
    "${WS_DIR}/${BIN_NAME}" --all
elif [ "$1" = "--interactive" ]; then
    "${WS_DIR}/${BIN_NAME}"
elif [ "$1" = "--list" ]; then
    "${WS_DIR}/${BIN_NAME}" --list
else
    "${WS_DIR}/${BIN_NAME}" "$@"
fi
