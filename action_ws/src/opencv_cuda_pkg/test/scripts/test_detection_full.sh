#!/bin/bash

# OpenCV 目标检测测试脚本（完整版）
# 测试所有检测方法：HOG、Haar Cascade、DNN

PACKAGE_DIR="/home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg"
INPUT_DIR="$PACKAGE_DIR/test/img"
SCRIPT_DIR="$PACKAGE_DIR/scripts"
MODELS_DIR="$PACKAGE_DIR/models"

# 确保环境变量正确
export PYTHONNOUSERSITE=1
export PYTHONPATH="/opt/ros/noetic/lib/python3/dist-packages:$PYTHONPATH"
source /home/jetson/Desktop/Jetson_Nano/action_ws/devel/setup.bash

echo "======================================"
echo "🎯 OpenCV 目标检测测试（完整版）"
echo "======================================"
echo "📁 输入目录: $INPUT_DIR"
echo "📁 模型目录: $MODELS_DIR"
echo ""

# 测试 1: HOG 行人检测
echo "🔧 测试 1: HOG 行人检测"
echo "--------------------------------------"
python3 "$SCRIPT_DIR/opencv_detection_client.py" \
    --type image_file \
    --source "$INPUT_DIR/dog.png" \
    --method hog
echo ""

# 测试 2: Haar Cascade 人脸检测
echo "🔧 测试 2: Haar Cascade 人脸检测"
echo "--------------------------------------"
if [ -f "$MODELS_DIR/haarcascade_frontalface_default.xml" ]; then
    python3 "$SCRIPT_DIR/opencv_detection_client.py" \
        --type image_file \
        --source "$INPUT_DIR/dog.png" \
        --method haar_cascade \
        --cascade "$MODELS_DIR/haarcascade_frontalface_default.xml"
else
    echo "⚠️  模型文件不存在: $MODELS_DIR/haarcascade_frontalface_default.xml"
    echo "   运行 ./download_models.sh 下载模型"
fi
echo ""

# 测试 3: Haar Cascade 全身检测
echo "🔧 测试 3: Haar Cascade 全身检测"
echo "--------------------------------------"
if [ -f "$MODELS_DIR/haarcascade_fullbody.xml" ]; then
    python3 "$SCRIPT_DIR/opencv_detection_client.py" \
        --type image_file \
        --source "$INPUT_DIR/dog.png" \
        --method haar_cascade \
        --cascade "$MODELS_DIR/haarcascade_fullbody.xml"
else
    echo "⚠️  模型文件不存在: $MODELS_DIR/haarcascade_fullbody.xml"
fi
echo ""

# 测试 4: Haar Cascade 微笑检测
echo "🔧 测试 4: Haar Cascade 微笑检测"
echo "--------------------------------------"
if [ -f "$MODELS_DIR/haarcascade_smile.xml" ]; then
    python3 "$SCRIPT_DIR/opencv_detection_client.py" \
        --type image_file \
        --source "$INPUT_DIR/dog.png" \
        --method haar_cascade \
        --cascade "$MODELS_DIR/haarcascade_smile.xml"
else
    echo "⚠️  模型文件不存在: $MODELS_DIR/haarcascade_smile.xml"
fi
echo ""

# 测试 5: DNN 人脸检测（如果模型已下载）
echo "🔧 测试 5: DNN 人脸检测（MobileNet-SSD）"
echo "--------------------------------------"
DNN_MODEL="$MODELS_DIR/dnn/res10_300x300_ssd_iter_140000.caffemodel"
if [ -f "$DNN_MODEL" ]; then
    python3 "$SCRIPT_DIR/opencv_detection_client.py" \
        --type image_file \
        --source "$INPUT_DIR/dog.png" \
        --method dnn \
        --model "$DNN_MODEL" \
        --conf 0.7
else
    echo "⚠️  DNN 模型文件不存在"
    echo "   运行 ./download_models.sh 下载 DNN 模型"
fi
echo ""

echo "======================================"
echo "✅ 测试完成！"
echo ""
echo "📝 检测方法说明:"
echo "  - HOG: 传统方法，检测行人（内置，无需模型文件）"
echo "  - Haar Cascade: 传统方法，检测人脸/身体（需要 cascade 文件）"
echo "  - DNN: 深度学习方法，检测人脸（需要预训练模型）"
echo ""
echo "📥 下载模型:"
echo "   cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg"
echo "   ./scripts/download_models.sh"
echo "======================================"