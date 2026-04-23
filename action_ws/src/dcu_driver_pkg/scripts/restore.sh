#!/bin/bash
# ============================================================================
# EtherCAT 优化复原脚本
# 功能：将系统设置恢复至优化前状态（图形界面、中断、Swap、irqbalance 等）
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

# -------------------- 1. 恢复图形界面 --------------------
restore_gui() {
    info "正在恢复图形界面..."
    # 尝试启动显示管理器
    sudo systemctl start gdm3 2>/dev/null || sudo systemctl start lightdm 2>/dev/null || sudo systemctl start sddm 2>/dev/null || true
    sudo systemctl isolate graphical.target 2>/dev/null || true
    info "已切换到 graphical.target。"
}

# -------------------- 2. 恢复 CPU 调频策略（默认 ondemand） --------------------
restore_cpu_freq() {
    info "正在恢复 CPU 调频策略为 ondemand..."
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo ondemand | sudo tee "$gov" > /dev/null 2>&1 || true
    done
    # Jetson 特殊处理（解锁时钟）
    if command -v jetson_clocks &>/dev/null; then
        sudo jetson_clocks --restore 2>/dev/null || warn "Jetson 时钟恢复需要重启生效。"
    fi
    info "CPU 调频策略已恢复。"
}

# -------------------- 3. 恢复 irqbalance --------------------
restore_irqbalance() {
    info "正在恢复 irqbalance 服务..."
    sudo systemctl enable irqbalance 2>/dev/null || true
    sudo systemctl start irqbalance 2>/dev/null || true
    info "irqbalance 已启用。"
}

# -------------------- 4. 获取中断号并恢复中断绑定 --------------------
restore_irq_affinity() {
    IRQ=$(grep -E "eth0|enp" /proc/interrupts | head -1 | awk -F: '{print $1}' | tr -d ' ')
    if [ -n "$IRQ" ] && [ -d "/proc/irq/$IRQ" ]; then
        info "恢复中断 $IRQ 的默认亲和性（所有 CPU）..."
        echo f | sudo tee "/proc/irq/$IRQ/smp_affinity" > /dev/null
        info "中断 $IRQ 亲和性已重置为 $(cat /proc/irq/$IRQ/smp_affinity)。"
    else
        warn "未找到 eth0 中断，跳过。"
    fi
}

# -------------------- 5. 恢复网卡硬件卸载 --------------------
restore_nic_offload() {
    info "正在恢复网卡硬件卸载功能..."
    sudo ethtool -K eth0 sg on tso on gso on gro on lro on 2>/dev/null || warn "部分卸载功能不支持，继续。"
    info "网卡硬件卸载已恢复。"
}

# -------------------- 6. 恢复交换分区 --------------------
restore_swap() {
    info "正在重新启用交换分区..."
    sudo swapon -a
    info "Swap 已启用，当前总量: $(free -h | grep Swap | awk '{print $2}')"
}

# -------------------- 主流程 --------------------
main() {
    echo ""
    info "=============================================="
    info "     EtherCAT 优化复原脚本"
    info "=============================================="
    echo ""

    restore_gui
    restore_cpu_freq
    restore_irqbalance
    restore_irq_affinity
    restore_nic_offload
    restore_swap

    echo ""
    info "所有设置已恢复。重启系统亦可达到同样效果。"
}

main