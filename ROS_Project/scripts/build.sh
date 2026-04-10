#!/bin/bash

# 项目构建脚本

echo "开始构建Jetson Nano ROS项目..."

# 进入项目目录
cd "$(dirname "$0")/.."

# 检查catkin是否可用
if ! command -v catkin_make &> /dev/null; then
    echo "错误: catkin_make未找到，请确保ROS已正确安装"
    exit 1
fi

# 创建必要的目录
mkdir -p build devel

# 执行catkin构建
echo "执行catkin_make..."
catkin_make

if [ $? -eq 0 ]; then
    echo "构建成功！"
    echo "运行以下命令激活工作空间:"
    echo "  source devel/setup.bash"
else
    echo "构建失败！"
    exit 1
fi