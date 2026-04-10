#!/bin/bash

echo "========================================"
echo "  通用GPIO控制 - 快速启动指南"
echo "========================================"
echo ""

cd /home/jetson/Desktop/Jetson_Nano/ROS_Project
source devel/setup.bash

echo "🚀 启动GPIO控制节点..."
roslaunch gpio_control universal_gpio_launch &
GPIO_PID=$!

echo "   ✅ GPIO节点已启动 (PID: $GPIO_PID)"
echo ""

# 等待节点启动
sleep 4

echo "📋 可用GPIO控制命令:"
echo ""
echo "【1. 基础GPIO控制】"
echo "   控制GPIO18 -> HIGH:    rostopic pub -1 /gpio/write std_msgs/Int32 \"data: 0\""
echo "   控制GPIO19 -> HIGH:    rostopic pub -1 /gpio/write std_msgs/Int32 \"data: 1\""
echo "   控制GPIO31 -> HIGH:    rostopic pub -1 /gpio/write std_msgs/Int32 \"data: 2\""
echo ""
echo "【2. GPIO切换功能】"
echo "   切换GPIO33:            rostopic pub -1 /gpio/toggle std_msgs/Int32 \"data: 4\""
echo ""
echo "【3. GPIO方向切换】"
echo "   设置GPIO35为输入:      rostopic pub -1 /gpio/set_input std_msgs/Int32 \"data: 5\""
echo "   设置GPIO35为输出:      rostopic pub -1 /gpio/set_output std_msgs/Int32 \"data: 5\""
echo ""
echo "【4. 批量操作】"
echo "   所有GPIO设为输入:      rostopic pub -1 /gpio/set_all_direction std_msgs/String \"data: 'in'\""
echo "   所有GPIO设为输出:      rostopic pub -1 /gpio/set_all_direction std_msgs/String \"data: 'out'\""
echo ""
echo "【5. 状态监控】"
echo "   监听GPIO状态:         rostopic echo /gpio/state"
echo ""

echo "📍 GPIO引脚对照表:"
echo "   [0] GPIO 18 - PWM支持"
echo "   [1] GPIO 19 - PWM支持"  
echo "   [2] GPIO 31 - 纯通用IO"
echo "   [3] GPIO 32 - 纯通用IO"
echo "   [4] GPIO 33 - 纯通用IO"
echo "   [5] GPIO 35 - 纯通用IO"
echo "   [6] GPIO 36 - 纯通用IO"
echo "   [7] GPIO 37 - 纯通用IO"
echo "   [8] GPIO 38 - 纯通用IO"
echo "   [9] GPIO 40 - 纯通用IO"
echo ""

echo "⚠️  重要提示:"
echo "   1. GPIO节点必须先启动才能使用话题控制"
echo "   2. 使用前必须激活ROS环境: source devel/setup.bash"
echo "   3. 控制是通过索引方式，不是直接的GPIO编号"
echo "   4. 推荐使用话题接口，服务接口可能不稳定"
echo ""

echo "🎯 快速测试示例:"
echo "   测试GPIO18 -> HIGH:"
echo "   rostopic pub -1 /gpio/write std_msgs/Int32 \"data: 0\""
echo ""
echo "   测试GPIO切换:"
echo "   rostopic pub -1 /gpio/toggle std_msgs/Int32 \"data: 4\""
echo ""

echo "   监听GPIO状态:"
echo "   rostopic echo /gpio/state"
echo ""

echo "💡 退出GPIO控制:"
echo "   按 Ctrl+C 停止当前命令"
echo "   关闭GPIO节点: pkill -f universal_gpio_control_node"
echo ""

echo "========================================" 
echo "  GPIO控制已准备就绪！"
echo "========================================"