#!/bin/bash

# OpenCV 图像处理测试脚本
# 用于测试图像处理并将结果保存到 result 目录

PACKAGE_DIR="/home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg"
INPUT_DIR="$PACKAGE_DIR/test/img"
RESULT_DIR="$PACKAGE_DIR/test/result"
SCRIPT_DIR="$PACKAGE_DIR/test/scripts"

# 创建 result 目录（如果不存在）
mkdir -p "$RESULT_DIR"

# 确保环境变量正确
export PYTHONNOUSERSITE=1
export PYTHONPATH="/opt/ros/noetic/lib/python3/dist-packages:$PYTHONPATH"
source /home/jetson/Desktop/Jetson_Nano/action_ws/devel/setup.bash

echo "======================================"
echo "📷 OpenCV 图像处理测试"
echo "======================================"
echo "📁 输入目录: $INPUT_DIR"
echo "📁 结果目录: $RESULT_DIR"
echo ""

# 测试 resize 操作
echo "🔧 测试 1: Resize (640x480)"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/test_processing.py" \
    --source "$INPUT_DIR/dog.png" \
    --operation resize \
    --params '{"width": 640, "height": 480}' \
    --save "$RESULT_DIR/dog_resize.jpg"
echo ""

# 测试高斯模糊
echo "🔧 测试 2: Gaussian Blur (ksize=15)"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/test_processing.py" \
    --source "$INPUT_DIR/dog.png" \
    --operation gaussian_blur \
    --params '{"ksize": 15, "sigma": 0}' \
    --save "$RESULT_DIR/dog_blur.jpg"
echo ""

# 测试 Canny 边缘检测
echo "🔧 测试 3: Canny Edge Detection"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/test_processing.py" \
    --source "$INPUT_DIR/dog.png" \
    --operation canny \
    --params '{"threshold1": 50, "threshold2": 150}' \
    --save "$RESULT_DIR/dog_canny.jpg"
echo ""

# 测试颜色转换 (BGR2GRAY)
echo "🔧 测试 4: Color Convert (BGR to Gray)"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/test_processing.py" \
    --source "$INPUT_DIR/dog.png" \
    --operation color_convert \
    --params '{"conversion": "BGR2GRAY"}' \
    --save "$RESULT_DIR/dog_gray.jpg"
echo ""

echo "======================================"
echo "✅ 测试完成！"
echo "📁 查看结果: $RESULT_DIR"
echo "======================================"