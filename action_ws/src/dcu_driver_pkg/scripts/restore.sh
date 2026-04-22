#!/bin/bash
# ============================================================
# 复原 EtherCAT 优化设置
# 功能：将网卡中断亲和性、硬件卸载、swap 恢复为系统默认状态
# 注意：重启系统后所有设置也会自动恢复，此脚本用于手动即时复原
# ============================================================

set -e  # 遇到错误立即退出

echo "=============================================="
echo "开始恢复 EtherCAT 相关系统设置..."
echo "=============================================="

# -------------------- 1. 恢复网卡中断亲和性 --------------------
# 动态获取 eth0 的当前中断号
IRQ=$(grep eth0 /proc/interrupts | awk -F: '{print $1}' | head -1)

if [ -n "$IRQ" ] && [ -d "/proc/irq/$IRQ" ]; then
    echo "检测到 eth0 中断号: $IRQ"
    echo "恢复中断亲和性为默认值 (所有 CPU)..."
    echo f | sudo tee /proc/irq/$IRQ/smp_affinity > /dev/null
    NEW_AFFINITY=$(cat /proc/irq/$IRQ/smp_affinity)
    echo "当前中断 $IRQ 亲和性: $NEW_AFFINITY"
else
    echo "警告: 未找到 eth0 的中断号，跳过中断恢复步骤。"
fi

# -------------------- 2. 恢复网卡硬件卸载功能 --------------------
echo ""
echo "重新启用网卡硬件卸载功能 (sg, tso, gso, gro, lro)..."
sudo ethtool -K eth0 sg on tso on gso on gro on lro on 2>/dev/null || {
    echo "警告: 部分硬件卸载功能可能不支持，继续执行..."
}

echo "当前 eth0 卸载状态:"
ethtool -k eth0 | grep -E "scatter-gather|tcp-segmentation|generic-segmentation|generic-receive-offload|large-receive-offload" || true

# -------------------- 3. 重新启用交换分区 (Swap) --------------------
echo ""
echo "重新启用交换分区..."
sudo swapon -a

echo "当前 Swap 状态:"
free -h | grep -E "Swap|交换"

# -------------------- 4. 确认网卡处于 UP 状态 --------------------
echo ""
if ! ip link show eth0 | grep -q "UP"; then
    echo "eth0 处于 DOWN 状态，正在激活..."
    sudo ifconfig eth0 up
    echo "eth0 已激活。"
else
    echo "eth0 已处于 UP 状态。"
fi

echo ""
echo "=============================================="
echo "所有设置已恢复。"
echo "=============================================="