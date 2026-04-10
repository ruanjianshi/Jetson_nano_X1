#!/bin/bash
# Jetson Nano B01 - PyTorch 1.13.0 + TorchVision 0.14.0 本地安装脚本
# 从Downloads文件夹安装
# 最后更新: 2026-03-24

set -e

echo "=========================================="
echo "PyTorch 1.13.0 + TorchVision 0.14.0 本地安装"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 定义文件路径
DOWNLOAD_DIR="/home/jetson/Downloads"
PYTORCH_WHEEL="torch-1.13.0a0+git7c98e70-cp38-cp38-linux_aarch64.whl"
TORCHVISION_WHEEL="torchvision-0.14.0a0+5ce4506-cp38-cp38-linux_aarch64.whl"

PYTORCH_PATH="$DOWNLOAD_DIR/$PYTORCH_WHEEL"
TORCHVISION_PATH="$DOWNLOAD_DIR/$TORCHVISION_WHEEL"

# 检查文件是否存在
check_files() {
    echo "[检查] 下载文件..."

    if [ ! -f "$PYTORCH_PATH" ]; then
        echo -e "${RED}✗ PyTorch文件不存在: $PYTORCH_PATH${NC}"
        exit 1
    else
        SIZE=$(du -h "$PYTORCH_PATH" | cut -f1)
        echo -e "${GREEN}✓ PyTorch文件存在${NC}"
        echo "  路径: $PYTORCH_PATH"
        echo "  大小: $SIZE"
    fi

    if [ ! -f "$TORCHVISION_PATH" ]; then
        echo -e "${RED}✗ TorchVision文件不存在: $TORCHVISION_PATH${NC}"
        exit 1
    else
        SIZE=$(du -h "$TORCHVISION_PATH" | cut -f1)
        echo -e "${GREEN}✓ TorchVision文件存在${NC}"
        echo "  路径: $TORCHVISION_PATH"
        echo "  大小: $SIZE"
    fi
    echo ""
}

# 检查PyTorch是否已安装
check_pytorch_installed() {
    echo "[检查] PyTorch是否已安装..."
    if python3 -c "import torch" 2>/dev/null; then
        VERSION=$(python3 -c "import torch; print(torch.__version__)")
        echo -e "${GREEN}✓ PyTorch已安装${NC}"
        echo "  版本: $VERSION"

        CUDA_AVAILABLE=$(python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null || echo "False")
        echo "  CUDA可用: $CUDA_AVAILABLE"

        echo ""
        echo -e "${YELLOW}是否重新安装?${NC}"
        echo "  [1] 重新安装"
        echo "  [2] 退出"
        read -p "请选择 [1/2]: " choice
        case $choice in
            2) echo "安装已取消"; exit 0;;
            *) echo "继续安装...";;
        esac
    else
        echo -e "${GREEN}✓ PyTorch未安装，准备安装${NC}"
    fi
    echo ""
}

# 步骤1: 检查文件
check_files

# 步骤2: 检查已安装版本
check_pytorch_installed

# 步骤3: 安装系统依赖
echo "[步骤 1/6] 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
echo -e "${GREEN}✓ 系统依赖安装完成${NC}"
echo ""

# 步骤4: 安装Python基础包
echo "[步骤 2/6] 安装Python基础包..."
sudo -H pip3 install future
sudo pip3 install -U --user wheel mock pillow
sudo -H pip3 install testresources
sudo -H pip3 install setuptools==58.3.0
sudo -H pip3 install Cython
echo -e "${GREEN}✓ Python基础包安装完成${NC}"
echo ""

# 步骤5: 卸载旧版本（如果有）
echo "[步骤 3/6] 清理旧版本..."
sudo pip3 uninstall torch -y 2>/dev/null || true
sudo pip3 uninstall torchvision -y 2>/dev/null || true
echo -e "${GREEN}✓ 旧版本已清理${NC}"
echo ""

# 步骤6: 安装PyTorch
echo "[步骤 4/6] 安装PyTorch 1.13.0..."
echo "  文件: $PYTORCH_PATH"
sudo -H pip3 install "$PYTORCH_PATH"
echo -e "${GREEN}✓ PyTorch 1.13.0安装完成${NC}"
echo ""

# 步骤7: 安装TorchVision依赖
echo "[步骤 5/6] 安装TorchVision依赖..."
sudo apt-get install -y libjpeg-dev zlib1g-dev libpython3-dev libavcodec-dev libavformat-dev libswscale-dev
sudo pip3 install -U pillow
echo -e "${GREEN}✓ TorchVision依赖安装完成${NC}"
echo ""

# 步骤8: 安装TorchVision
echo "[步骤 6/6] 安装TorchVision 0.14.0..."
echo "  文件: $TORCHVISION_PATH"
sudo -H pip3 install "$TORCHVISION_PATH"
echo -e "${GREEN}✓ TorchVision 0.14.0安装完成${NC}"
echo ""

# 步骤9: 更新protobuf
echo "[步骤 7/7] 更新protobuf..."
sudo -H pip3 install -U protobuf
echo -e "${GREEN}✓ protobuf更新完成${NC}"
echo ""

# 验证安装
echo "=========================================="
echo "验证安装..."
echo "=========================================="
echo ""

echo "--- PyTorch ---"
python3 << 'EOF'
try:
    import torch
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"GPU数量: {torch.cuda.device_count()}")
    if torch.cuda.is_available():
        print(f"GPU型号: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "--- TorchVision ---"
python3 << 'EOF'
try:
    import torchvision
    print(f"TorchVision版本: {torchvision.__version__}")
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "--- Caffe2 ---"
python3 << 'EOF'
try:
    from caffe2.python import workspace
    print("Caffe2: 可用")
except Exception as e:
    print(f"Caffe2错误: {e}")
EOF
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "提示: 安装的wheel文件仍保留在Downloads文件夹中"
echo "      可以安全删除以释放空间："
echo "      rm $PYTORCH_PATH"
echo "      rm $TORCHVISION_PATH"
echo ""
echo "预计释放空间: 约226MB"
echo ""