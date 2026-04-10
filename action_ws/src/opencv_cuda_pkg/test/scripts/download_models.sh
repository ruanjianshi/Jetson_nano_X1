#!/bin/bash

# OpenCV 模型下载脚本
# 下载常用的目标检测和识别模型

echo "======================================"
echo "📥 OpenCV 模型下载工具"
echo "======================================"

PACKAGES_DIR="/home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/models"
DNN_DIR="$PACKAGES_DIR/dnn"

# 创建 DNN 模型目录
mkdir -p "$DNN_DIR"

echo ""
echo "📁 模型将保存到: $DNN_DIR"
echo ""

# 检查是否已安装必要的工具
if ! command -v wget &> /dev/null; then
    echo "❌ wget 未安装，请先安装: sudo apt install wget"
    exit 1
fi

# ========================================
# 1. MobileNet-SSD 人脸检测模型
# ========================================
echo "🔧 下载 MobileNet-SSD 人脸检测模型..."
echo "  - 模型文件: res10_300x300_ssd_iter_140000.caffemodel"
echo "  - 配置文件: deploy.prototxt"

MODEL_URL="https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
PROTO_URL="https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"

if [ ! -f "$DNN_DIR/res10_300x300_ssd_iter_140000.caffemodel" ]; then
    echo "  正在下载模型文件 (约 10MB)..."
    wget -q --show-progress -O "$DNN_DIR/res10_300x300_ssd_iter_140000.caffemodel" "$MODEL_URL"
else
    echo "  ✅ 模型文件已存在"
fi

if [ ! -f "$DNN_DIR/deploy.prototxt" ]; then
    echo "  正在下载配置文件..."
    wget -q -O "$DNN_DIR/deploy.prototxt" "$PROTO_URL"
else
    echo "  ✅ 配置文件已存在"
fi

# ========================================
# 2. 更多 DNN 模型下载链接（手动下载）
# ========================================
echo ""
echo "======================================"
echo "📝 更多模型下载说明"
echo "======================================"
echo ""
echo "以下模型需要手动下载（文件较大）："
echo ""
echo "1. MobileNet-SSD COCO 目标检测"
echo "   - 模型: http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz"
echo "   - 配置: https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
echo ""
echo "2. YOLOv4 目标检测"
echo "   - 模型: https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights"
echo "   - 配置: https://github.com/AlexeyAB/darknet/blob/master/cfg/yolov4.cfg"
echo ""
echo "3. OpenPose 姿态估计"
echo "   - 模型: https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/models/"
echo ""
echo "======================================"
echo ""

# ========================================
# 3. Haar Cascade 模型（已从系统复制）
# ========================================
echo "✅ Haar Cascade 模型已从系统安装:"
ls -lh "$PACKAGES_DIR"/*.xml 2>/dev/null || echo "  无 Haarcascade 模型"

echo ""
echo "======================================"
echo "📊 下载完成"
echo "======================================"
echo ""
echo "可用的模型:"
echo ""

if [ -d "$DNN_DIR" ]; then
    echo "📁 DNN 模型:"
    ls -lh "$DNN_DIR" | grep -E "\.(caffemodel|prototxt|weights|pb)$" | tail -n +2
    echo ""
fi

echo "📁 Haar Cascade 模型:"
ls -lh "$PACKAGES_DIR"/*.xml 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

echo "======================================"