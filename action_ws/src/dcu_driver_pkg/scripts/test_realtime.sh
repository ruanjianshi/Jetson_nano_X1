#!/bin/bash
# ============================================================================
# 系统实时性测试脚本 (基于 cyclictest)
# 功能：
#   1. 短时基准测试（无负载）
#   2. 绑定 CPU1 测试
#   3. 高优先级测试（模拟 EtherCAT 线程）
#   4. 可选：长时间压力测试（需要 stress 工具）
# ============================================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
title() { echo -e "${CYAN}==============================================${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}==============================================${NC}"; }

# 检查 cyclictest 是否安装
if ! command -v cyclictest &> /dev/null; then
    echo "错误：cyclictest 未安装，请先执行: sudo apt-get install rt-tests"
    exit 1
fi

# 检查 stress 是否安装（可选）
HAS_STRESS=false
if command -v stress &> /dev/null; then
    HAS_STRESS=true
fi

# -------------------- 测试1：基准测试（无绑定，默认优先级） --------------------
test_baseline() {
    title "测试1：基准测试（1ms周期，10万次循环，无绑定）"
    info "此测试评估系统在空闲状态下的基本延迟表现。"
    sudo cyclictest -t1 -p 80 -i 1000 -l 100000 -q
}

# -------------------- 测试2：绑定 CPU1 + 高优先级 --------------------
test_bind_cpu() {
    title "测试2：绑定 CPU1 + 优先级 99（模拟 EtherCAT 主站线程）"
    info "此测试模拟 EtherCAT 线程的运行环境。"
    sudo cyclictest -t1 -p 99 -i 1000 -l 100000 -a 1 -q
}

# -------------------- 测试3：内存锁定 + 高精度 --------------------
test_mlock() {
    title "测试3：内存锁定 + 高精度（推荐配置）"
    info "此测试锁定内存，避免缺页异常干扰。"
    sudo cyclictest -t1 -p 99 -i 1000 -l 100000 -a 1 -m -q
}

# -------------------- 测试4：长时间压力测试（需要 stress） --------------------
test_stress() {
    if [ "$HAS_STRESS" = false ]; then
        warn "未安装 stress 工具，跳过压力测试。"
        warn "安装命令: sudo apt-get install stress"
        return
    fi

    title "测试4：压力测试（CPU/IO/内存负载，60秒）"
    info "此测试模拟系统在高负载下的实时性能。"
    info "将在后台启动 stress 负载，同时运行 cyclictest..."

    # 启动 stress（2个CPU满载，2个IO线程，512M内存分配）
    stress -c 2 -i 2 -m 1 --vm-bytes 512M -t 60s &
    STRESS_PID=$!

    sleep 2
    sudo cyclictest -t1 -p 99 -i 1000 -l 60000 -a 1 -m -q

    # 等待 stress 结束
    wait $STRESS_PID 2>/dev/null
}

# -------------------- 结果解读提示 --------------------
show_interpretation() {
    title "结果解读参考"
    echo "最大延迟 (Max Latency) 评估标准（1ms 周期）："
    echo "  < 50 µs    : 优秀，可满足严苛工业级 EtherCAT 应用"
    echo "  50-100 µs  : 良好，通常能稳定支持 1ms 周期"
    echo "  100-500 µs : 及格，偶有丢帧风险，建议优化"
    echo "  > 1 ms     : 不可用，必须优化系统或更换实时内核"
    echo ""
    echo "关键指标："
    echo "  Min : 最小延迟，反映理想状态下的响应时间"
    echo "  Avg : 平均延迟，反映整体响应水平"
    echo "  Max : 最大延迟，决定实时任务的成败"
    echo ""
    echo "如果最大延迟超过 100 µs，建议："
    echo "  1. 锁定 CPU 频率: sudo jetson_clocks"
    echo "  2. 绑定网卡中断到同一 CPU 核心"
    echo "  3. 关闭图形界面和无关服务"
    echo "  4. 考虑安装 PREEMPT_RT 实时内核"
}

# ==================== 主流程 ====================
main() {
    echo ""
    title "系统实时性测试 (cyclictest)"
    echo "测试时间: $(date)"
    echo "内核版本: $(uname -r)"
    echo ""

    test_baseline
    echo ""
    test_bind_cpu
    echo ""
    test_mlock
    echo ""

    read -p "是否进行长时间压力测试？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_stress
        echo ""
    fi

    show_interpretation
}

main