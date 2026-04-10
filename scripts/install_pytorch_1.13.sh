#!/bin/bash
# Jetson Nano B01 - PyTorch 1.13.0 + TorchVision 0.14.0 安装脚本
# 基于 Q-engineering 官方安装指南
# 最后更新: 2026-03-24

set -e  # 遇到错误立即退出

echo "=========================================="
echo "PyTorch 1.13.0 + TorchVision 0.14.0 安装"
echo "=========================================="
echo ""

# 步骤1: 安装系统依赖
echo "[步骤 1/10] 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
echo "✓ 系统依赖安装完成"
echo ""

# 步骤2: 安装Python基础包
echo "[步骤 2/10] 安装Python基础包..."
sudo -H pip3 install future
sudo pip3 install -U --user wheel mock pillow
sudo -H pip3 install testresources
sudo -H pip3 install setuptools==58.3.0
sudo -H pip3 install Cython
echo "✓ Python基础包安装完成"
echo ""

# 步骤3: 安装gdown
echo "[步骤 3/10] 安装gdown..."
sudo -H pip3 install gdown
echo "✓ gdown安装完成"
echo ""

# 步骤4: 下载PyTorch 1.13.0
echo "[步骤 4/10] 下载PyTorch 1.13.0..."
gdown https://drive.google.com/uc?id=1e9FDGt2zGS5C5Pms7wzHYRb0HuupngK1
echo "✓ PyTorch下载完成"
echo ""

# 步骤5: 安装PyTorch
echo "[步骤 5/10] 安装PyTorch 1.13.0..."
sudo -H pip3 install torch-1.13.0a0+git7c98e70-cp38-cp38-linux_aarch64.whl
echo "✓ PyTorch安装完成"
echo ""

# 步骤6: 清理PyTorch临时文件
echo "[步骤 6/10] 清理PyTorch临时文件..."
rm -f torch-1.13.0a0+git7c98e70-cp38-cp38-linux_aarch64.whl
echo "✓ 清理完成"
echo ""

# 步骤7: 安装TorchVision依赖
echo "[步骤 7/10] 安装TorchVision依赖..."
sudo apt-get install -y libjpeg-dev zlib1g-dev libpython3-dev libavcodec-dev libavformat-dev libswscale-dev
sudo pip3 install -U pillow
echo "✓ TorchVision依赖安装完成"
echo ""

# 步骤8: 下载TorchVision 0.14.0
echo "[步骤 8/10] 下载TorchVision 0.14.0..."
gdown https://drive.google.com/uc?id=19UbYsKHhKnyeJ12VPUwcSvoxJaX7jQZ2
echo "✓ TorchVision下载完成"
echo ""

# 步骤9: 安装TorchVision
echo "[步骤 9/10] 安装TorchVision 0.14.0..."
sudo -H pip3 install torchvision-0.14.0a0+5ce4506-cp38-cp38-linux_aarch64.whl
echo "✓ TorchVision安装完成"
echo ""

# 步骤10: 清理TorchVision临时文件
echo "[步骤 10/10] 清理TorchVision临时文件..."
rm -f torchvision-0.14.0a0+5ce4506-cp38-cp38-linux_aarch64.whl
echo "✓ 清理完成"
echo ""

# 步骤11: 更新protobuf (Caffe2需要)
echo "[步骤 11/11] 更新protobuf..."
sudo -H pip3 install -U protobuf
echo "✓ protobuf更新完成"
echo ""

# 验证安装
echo "=========================================="
echo "验证安装..."
echo "=========================================="
echo ""

echo "--- PyTorch ---"
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA版本: {torch.version.cuda}')" 2>&1 || echo "⚠ PyTorch验证失败"
echo ""

echo "--- TorchVision ---"
python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')" 2>&1 || echo "⚠ TorchVision验证失败"
echo ""

echo "--- Caffe2 ---"
python3 -c "from caffe2.python import workspace; print('Caffe2可用')" 2>&1 || echo "⚠ Caffe2验证失败"
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "提示: 如果遇到问题，请查看详细安装指南："
echo "/home/jetson/Desktop/Jetson_Nano/README/PyTorch_TensorFlow_安装指南.md"
echo ""