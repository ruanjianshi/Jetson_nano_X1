#!/bin/bash
# 关闭网卡
sudo ifconfig eth0 down
# 禁用硬件卸载
sudo ethtool -K eth0 sg off tso off gso off gro off lro off
# 激活网卡
sudo ifconfig eth0 up
# 绑定中断到 CPU1（假设中断号 406，若重启后变化请用实际值）
echo 2 | sudo tee /proc/irq/406/smp_affinity
# 关闭交换分区
sudo swapoff -a