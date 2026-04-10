#!/bin/bash
# Jetson Nano B01 - PyTorch 1.10.0 安装脚本（使用NVIDIA官方源）
# 适用于无法访问Google Drive的情况
# 最后更新: 2026-03-24

set -e

echo "=========================================="
echo "PyTorch 1.10.0 安装 (NVIDIA官方源)"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查PyTorch是否已安装
echo "[检查] PyTorch是否已安装..."
if python3 -c "import torch" 2>/dev/null; then
    VERSION=$(python3 -c "import torch; print(torch.__version__)")
    echo -e "${GREEN}✓ PyTorch已安装${NC}"
    echo "  版本: $VERSION"

    python3 -c "import torch; print(f'  CUDA可用: {torch.cuda.is_available()}')" 2>/dev/null || echo "  CUDA: 未知"

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
    echo -e "${GREEN}✓ PyTorch未安装${NC}"
fi
echo ""

# 步骤1: 安装系统依赖
echo "[步骤 1/7] 安装系统依赖..."
sudo apt-get update
sudo apt-get install -y python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
echo -e "${GREEN}✓ 系统依赖安装完成${NC}"
echo ""

# 步骤2: 安装Python基础包
echo "[步骤 2/7] 安装Python基础包..."
sudo -H pip3 install future
sudo pip3 install -U --user wheel mock pillow
sudo -H pip3 install testresources
sudo -H pip3 install setuptools==58.3.0
sudo -H pip3 install Cython
echo -e "${GREEN}✓ Python基础包安装完成${NC}"
echo ""

# 步骤3: 从NVIDIA官方源安装PyTorch 1.10.0
echo "[步骤 3/7] 从NVIDIA官方源安装PyTorch 1.10.0..."
echo "  来源: https://developer.download.nvidia.com/compute/redist/jp/v461/torch_archive/"
echo ""
echo "  如果下载失败，请手动下载wheel文件："
echo "  wget https://nvidia.box.com/shared/static/p57jwntv436lfrd78inwl7iml6p13fzh.whl"
echo ""

# 尝试从NVIDIA官方源安装
if pip3 install --pre --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v461/torch_archive/ torch==1.10.0; then
    echo -e "${GREEN}✓ PyTorch 1.10.0安装成功${NC}"
else
    echo -e "${YELLOW}⚠ NVIDIA官方源安装失败，尝试备用方案...${NC}"
    echo ""
    echo "  备用方案1: 使用pip默认源"
    if pip3 install torch==1.10.0 --index-url https://download.pytorch.org/whl/cpu; then
        echo -e "${GREEN}✓ PyTorch 1.10.0 (CPU版本) 安装成功${NC}"
        echo -e "${YELLOW}⚠ 注意: 这是CPU版本，不支持GPU加速${NC}"
    else
        echo -e "${YELLOW}⚠ 所有安装方案失败${NC}"
        echo ""
        echo "  手动安装方法："
        echo "  1. 从其他设备下载wheel文件"
        echo "  2. 使用U盘传输到Jetson Nano"
        echo "  3. 运行: sudo -H pip3 install torch-1.10.0-cp36-cp36m-linux_aarch64.whl"
        exit 1
    fi
fi
echo ""

# 步骤4: 安装TorchVision依赖
echo "[步骤 4/7] 安装TorchVision依赖..."
sudo apt-get install -y libjpeg-dev zlib1g-dev libpython3-dev libavcodec-dev libavformat-dev libswscale-dev
sudo pip3 install -U pillow
echo -e "${GREEN}✓ TorchVision依赖安装完成${NC}"
echo ""

# 步骤5: 安装TorchVision 0.11.0
echo "[步骤 5/7] 安装TorchVision 0.11.0..."
echo "  来源: GitHub + 本地编译"
echo ""

# 尝试安装TorchVision
if pip3 install torchvision==0.11.0; then
    echo -e "${GREEN}✓ TorchVision 0.11.0安装成功${NC}"
else
    echo -e "${YELLOW}⚠ TorchVision安装失败，尝试从源码安装...${NC}"
    echo ""
    echo "  注意: 从源码编译TorchVision需要很长时间(约30-60分钟)"
    echo ""
    read -p "是否继续? [y/N]: " compile_choice
    if [[ "$compile_choice" =~ ^[Yy]$ ]]; then
        echo "开始编译TorchVision..."
        sudo apt-get install -y ninja-build
        git clone --branch v0.11.1 --depth=1 https://github.com/pytorch/vision torchvision
        cd torchvision
        python3 setup.py install
        cd ..
        sudo rm -rf torchvision
        echo -e "${GREEN}✓ TorchVision编译安装完成${NC}"
    else
        echo -e "${YELLOW}⚠ TorchVision安装跳过${NC}"
    fi
fi
echo ""

# 步骤6: 更新protobuf
echo "[步骤 6/7] 更新protobuf..."
sudo -H pip3 install -U protobuf
echo -e "${GREEN}✓ protobuf更新完成${NC}"
echo ""

# 验证安装
echo "[步骤 7/7] 验证安装..."
echo ""

echo "--- PyTorch ---"
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA版本: {torch.version.cuda}')" 2>&1 || echo -e "${YELLOW}⚠ PyTorch验证失败${NC}"
echo ""

if python3 -c "import torchvision" 2>/dev/null; then
    echo "--- TorchVision ---"
    python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')"
    echo ""
fi

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "提示: 如果PyTorch版本不是1.10.0或CUDA不可用，"
echo "      请检查网络连接或手动下载wheel文件"
echo ""
echo "下载链接:"
echo "PyTorch 1.10.0:"
echo "https://nvidia.box.com/shared/static/p57jwntv436lfrd78inwl7iml6p13fzh.whl"
echo ""