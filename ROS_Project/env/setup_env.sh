#!/bin/bash

# Jetson Nano ROS项目环境配置脚本

echo "正在设置ROS Noetic项目环境..."

# 检查ROS是否安装
if [ -f /opt/ros/noetic/setup.bash ]; then
    echo "检测到ROS Noetic已安装"
    source /opt/ros/noetic/setup.bash
else
    echo "警告: 未检测到ROS Noetic安装"
    echo "请先安装ROS Noetic: sudo apt install ros-noetic-desktop-full"
fi

# 设置项目路径
export ROS_PROJECT_PATH=$(pwd)

# 创建工作空间
if [ ! -d "build" ] || [ ! -d "devel" ]; then
    echo "创建ROS工作空间..."
    catkin_make
else
    echo "工作空间已存在，跳过创建"
fi

# 检查C++依赖
echo "检查C++依赖..."
if ! dpkg -l | grep -q libboost-all-dev; then
    echo "需要安装Boost库: sudo apt install libboost-all-dev"
fi

# 检查Python依赖
echo "检查Python依赖..."
python3 -c "import rospy" 2>/dev/null || echo "需要安装rospy"
python3 -c "import cv2" 2>/dev/null || echo "需要安装opencv-python"
python3 -c "import PyQt5" 2>/dev/null || echo "需要安装PyQt5"
python3 -c "import numpy" 2>/dev/null || echo "需要安装numpy"
python3 -c "import yaml" 2>/dev/null || echo "需要安装pyyaml"

# 设置环境变量
export PYTHONPATH=$ROS_PROJECT_PATH/src:$PYTHONPATH

echo "环境设置完成！"
echo "使用以下命令激活环境:"
echo "  source devel/setup.bash"
echo ""
echo "构建项目:"
echo "  catkin_make"