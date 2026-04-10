#!/bin/bash
# 脉塔智能 USBCAN-II CAN 通信快速启动脚本

echo "========================================="
echo "脉塔智能 USBCAN-II CAN 通信"
echo "========================================="
echo ""

# 检查是否在正确的目录
if [ ! -f "README.md" ]; then
    echo "错误: 请在 /home/jetson/Desktop/Jetson_Nano/action_ws 目录下运行此脚本"
    exit 1
fi

# 1. 检查库文件
echo "1. 检查驱动库..."
if [ ! -f "/lib/libusbcan.so" ]; then
    echo "❌ libusbcan.so 未安装"
    echo ""
    echo "请先安装驱动库:"
    echo "  sudo cp src/maita_can_comm/usbcan_ii_libusb_aarch64/libusbcan.so /lib/"
    echo "  sudo chmod 644 /lib/libusbcan.so"
    echo ""
    read -p "是否现在安装? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo cp src/maita_can_comm/usbcan_ii_libusb_aarch64/libusbcan.so /lib/
        sudo chmod 644 /lib/libusbcan.so
        echo "✅ 驱动库已安装"
    else
        exit 1
    fi
else
    echo "✅ libusbcan.so 已安装"
fi
echo ""

# 2. 检查 USB 设备
echo "2. 检查 USB 设备..."
if lsusb | grep -q "0471:1200"; then
    echo "✅ USBCAN-II 设备已连接"
else
    echo "⚠️  未检测到 USBCAN-II 设备"
    echo "   请检查设备是否正确连接"
    exit 1
fi
echo ""

# 3. Source ROS 环境
echo "3. 配置 ROS 环境..."
source devel/setup.bash
echo "✅ ROS 环境已配置"
echo ""

# 4. 询问用户操作
echo "========================================="
echo "请选择操作:"
echo "========================================="
echo ""
echo "1. 启动 CAN Server"
echo "2. 发送 CAN 帧"
echo "3. 测试官方驱动"
echo "4. 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "启动 CAN Server..."
        echo "按 Ctrl+C 停止"
        echo ""
        sudo roslaunch maita_can_comm can_comm_maita.launch
        ;;
    2)
        echo ""
        echo "发送 CAN 帧..."
        python3 src/maita_can_comm/scripts/can_comm_client.py \
            _can_id:=0x123 \
            _data:="[0x01, 0x02, 0x03]" \
            _dlc:=3
        ;;
    3)
        echo ""
        echo "测试官方驱动..."
        cd src/maita_can_comm/usbcan_ii_libusb_aarch64
        sudo ./test
        ;;
    4)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac