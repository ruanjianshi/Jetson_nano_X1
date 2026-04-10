#!/bin/bash

# OpenCV 目标检测测试脚本
# 用于测试不同的检测方法

PACKAGE_DIR="/home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg"
INPUT_DIR="$PACKAGE_DIR/test/img"
SCRIPT_DIR="$PACKAGE_DIR/scripts"

# 确保环境变量正确
export PYTHONNOUSERSITE=1
export PYTHONPATH="/opt/ros/noetic/lib/python3/dist-packages:$PYTHONPATH"
source /home/jetson/Desktop/Jetson_Nano/action_ws/devel/setup.bash

echo "======================================"
echo "🎯 OpenCV 目标检测测试"
echo "======================================"
echo "📁 输入目录: $INPUT_DIR"
echo ""

# 测试 1: HOG 行人检测
echo "🔧 测试 1: HOG 行人检测"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/opencv_detection_client.py" \
    --type image_file \
    --source "$INPUT_DIR/dog.png" \
    --method hog \
    --no-cuda
echo ""

# 测试 2: Haar Cascade 人脸检测（需要人脸图片）
echo "🔧 测试 2: Haar Cascade 人脸检测"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/opencv_detection_client.py" \
    --type image_file \
    --source "$INPUT_DIR/dog.png" \
    --method haar_cascade \
    --cascade "$PACKAGE_DIR/models/haarcascade_frontalface_default.xml" \
    --no-cuda
echo ""

echo "======================================"
echo "✅ 测试完成！"
echo ""
echo "📝 说明:"
echo "  - HOG 方法: 检测行人"
echo "  - Haar Cascade: 检测人脸"
echo "  - DNN 方法: 需要预训练模型文件"
echo "======================================"