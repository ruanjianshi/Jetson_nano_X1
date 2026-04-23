#!/bin/bash
# ============================================================================
# EtherCAT 通信稳定性优化脚本 (Jetson Nano)
# 功能：
#   1. 关闭图形界面（可选）
#   2. 锁定 CPU 频率至最高性能
#   3. 禁用 irqbalance 服务
#   4. 优化网卡硬件卸载与中断绑定
#   5. 关闭交换分区
# ============================================================================

set -e

# -------------------- 颜色定义 --------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# -------------------- 1. 关闭图形界面 --------------------
disable_gui() {
    info "正在关闭图形界面..."
    if systemctl is-active --quiet gdm3; then
        sudo systemctl stop gdm3
        info "已停止 gdm3。"
    elif systemctl is-active --quiet lightdm; then
        sudo systemctl stop lightdm
        info "已停止 lightdm。"
    elif systemctl is-active --quiet sddm; then
        sudo systemctl stop sddm
        info "已停止 sddm。"
    else
        warn "未检测到运行中的显示管理器。"
    fi
    sudo systemctl isolate multi-user.target 2>/dev/null || true
    info "已切换到 multi-user.target（纯命令行模式）。"
}

# -------------------- 2. 锁定 CPU 频率 --------------------
lock_cpu_freq() {
    info "正在锁定 CPU 频率..."
    if command -v nvpmodel &>/dev/null; then
        sudo nvpmodel -m 0
        sudo jetson_clocks
        info "Jetson 时钟已锁定（MAXN 模式）。"
    else
        for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            echo performance | sudo tee "$gov" > /dev/null
        done
        info "CPU 调频策略已设为 performance。"
    fi
}

# -------------------- 3. 禁用 irqbalance --------------------
disable_irqbalance() {
    info "正在禁用 irqbalance 服务..."
    if systemctl is-active --quiet irqbalance; then
        sudo systemctl stop irqbalance
        sudo systemctl disable irqbalance
        info "irqbalance 已停止并禁用。"
    else
        warn "irqbalance 未运行，跳过。"
    fi
}

# -------------------- 4. 获取 eth0 中断号 --------------------
get_eth0_irq() {
    IRQ=$(grep -E "eth0|enp" /proc/interrupts | head -1 | awk -F: '{print $1}' | tr -d ' ')
    if [ -z "$IRQ" ]; then
        error "未找到 eth0 网卡中断号，请检查网卡名称。"
        exit 1
    fi
    info "检测到 eth0 中断号: $IRQ"
}

# -------------------- 5. 网卡优化与中断绑定 --------------------
optimize_nic() {
    info "正在优化网卡 eth0..."

    # 关闭网卡
    sudo ip link set eth0 down 2>/dev/null || sudo ifconfig eth0 down
    info "  -> 网卡已关闭。"

    # 禁用硬件卸载
    sudo ethtool -K eth0 sg off tso off gso off gro off lro off 2>/dev/null || true
    info "  -> 硬件卸载已禁用。"

    # 重新激活网卡
    sudo ip link set eth0 up 2>/dev/null || sudo ifconfig eth0 up
    info "  -> 网卡已激活。"

    # 绑定中断到 CPU1（掩码 2）
    if [ -n "$IRQ" ] && [ -d "/proc/irq/$IRQ" ]; then
        echo 2 | sudo tee "/proc/irq/$IRQ/smp_affinity" > /dev/null
        AFFINITY=$(cat "/proc/irq/$IRQ/smp_affinity")
        info "  -> 中断 $IRQ 已绑定到 CPU1（掩码: $AFFINITY）。"
    else
        warn "  -> 中断绑定失败：目录不存在。"
    fi
}

# -------------------- 6. 关闭交换分区 --------------------
disable_swap() {
    info "正在关闭交换分区..."
    sudo swapoff -a
    info "  -> 交换分区已关闭。"
}

# -------------------- 7. 显示优化后状态 --------------------
show_status() {
    echo ""
    info "==================== 优化后系统状态 ===================="
    echo "CPU 调频策略: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo unknown)"
    echo "irqbalance 状态: $(systemctl is-active irqbalance 2>/dev/null || echo inactive)"
    echo "eth0 中断 $IRQ 亲和性: $(cat /proc/irq/$IRQ/smp_affinity 2>/dev/null || echo N/A)"
    echo "Swap 总量: $(free -h | grep Swap | awk '{print $2}')"
    info "========================================================"
}

# -------------------- 恢复提示 --------------------
restore_hint() {
    echo ""
    warn "==================== 恢复提示 ===================="
    echo "如需恢复图形界面: sudo systemctl start gdm3 (或 lightdm)"
    echo "如需恢复中断绑定: echo f | sudo tee /proc/irq/$IRQ/smp_affinity"
    echo "如需重新启用 Swap: sudo swapon -a"
    echo "如需恢复 irqbalance: sudo systemctl enable irqbalance --now"
    echo "重启系统将自动恢复大部分默认设置。"
    warn "=================================================="
}

# ==================== 主流程 ====================
main() {
    echo ""
    info "=============================================="
    info "     EtherCAT 通信稳定性优化脚本"
    info "=============================================="
    echo ""

    read -p "是否关闭图形界面？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        disable_gui
    else
        info "跳过关闭图形界面。"
    fi

    lock_cpu_freq
    disable_irqbalance
    get_eth0_irq
    optimize_nic
    disable_swap
    show_status
    restore_hint

    info "优化完成！请重新启动你的 ROS/EtherCAT 节点。"
}

main