#!/bin/bash
# Jetson Nano B01 - TensorFlow 2.4.1 本地安装脚本
# 从Downloads文件夹安装
# 基于 Q-engineering 官方安装指南
# 最后更新: 2026-03-24

set -e

echo "=========================================="
echo "TensorFlow 2.4.1 本地安装"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 定义文件路径
DOWNLOAD_DIR="/home/jetson/Downloads"
TF_WHEEL="tensorflow-2.4.1-cp38-cp38-manylinux_2_24_aarch64.whl"
TF_PATH="$DOWNLOAD_DIR/$TF_WHEEL"

# 检查文件是否存在
check_files() {
    echo "[检查] 下载文件..."

    if [ ! -f "$TF_PATH" ]; then
        echo -e "${RED}✗ TensorFlow文件不存在: $TF_PATH${NC}"
        exit 1
    else
        SIZE=$(du -h "$TF_PATH" | cut -f1)
        echo -e "${GREEN}✓ TensorFlow文件存在${NC}"
        echo "  路径: $TF_PATH"
        echo "  大小: $SIZE"
    fi

    # 检查Python版本
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_CODE="cp$(python3 -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")"
    echo ""
    echo "  Python版本: $PYTHON_VERSION"
    echo "  Python版本编码: $PYTHON_CODE"
    echo ""

    # 确认wheel版本兼容性
    if [ "$PYTHON_CODE" == "cp38" ]; then
        echo -e "${GREEN}✓ TensorFlow wheel版本与Python版本匹配${NC}"
    else
        echo -e "${YELLOW}⚠ 警告: Python版本不匹配${NC}"
        echo "  当前系统: Python $PYTHON_VERSION ($PYTHON_CODE)"
        echo "  wheel版本: Python 3.8 (cp38)"
        echo "  可能存在兼容性问题"
        echo ""
    fi
}

# 检查TensorFlow是否已安装
check_tensorflow_installed() {
    echo "[检查] TensorFlow是否已安装..."
    if python3 -c "import tensorflow as tf" 2>/dev/null; then
        VERSION=$(python3 -c "import tensorflow as tf; print(tf.__version__)" 2>/dev/null)
        echo -e "${GREEN}✓ TensorFlow已安装${NC}"
        echo "  版本: $VERSION"

        GPU_AVAILABLE=$(python3 -c "import tensorflow as tf; print('是' if tf.test.is_gpu_available() else '否')" 2>/dev/null || echo "未知")
        echo "  GPU可用: $GPU_AVAILABLE"

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
        echo -e "${GREEN}✓ TensorFlow未安装，准备安装${NC}"
    fi
    echo ""
}

# 步骤1: 检查文件
check_files

# 步骤2: 检查已安装版本
check_tensorflow_installed

# 步骤3: 更新系统
echo "[步骤 1/9] 更新系统..."
sudo apt-get update
sudo apt-get upgrade -y
echo -e "${GREEN}✓ 系统更新完成${NC}"
echo ""

# 步骤4: 卸载旧版本
echo "[步骤 2/9] 卸载旧版本..."
pip3 uninstall tensorflow -y 2>/dev/null || true
pip3 uninstall tensorflow-gpu -y 2>/dev/null || true
echo -e "${GREEN}✓ 旧版本已清理${NC}"
echo ""

# 步骤5: 升级pip
echo "[步骤 3/9] 升级pip..."
sudo apt-get install -y python3-pip
pip3 install --upgrade pip
echo -e "${GREEN}✓ pip3升级完成${NC}"
echo ""

# 步骤6: 安装系统依赖
echo "[步骤 4/9] 安装系统依赖..."
sudo apt-get install -y gfortran
sudo apt-get install -y libhdf5-dev libc-ares-dev libeigen3-dev
sudo apt-get install -y libatlas-base-dev libopenblas-dev libblas-dev
sudo apt-get install -y liblapack-dev
echo -e "${GREEN}✓ 系统依赖安装完成${NC}"
echo ""

# 步骤7: 安装Python依赖
echo "[步骤 5/9] 安装Python依赖..."
sudo -H pip3 install Cython==0.29.21
echo -e "${GREEN}✓ Cython 0.29.21安装完成${NC}"
echo ""

# 步骤8: 安装h5py
echo "[步骤 6/9] 安装h5py (可能需要5-10分钟)..."
sudo -H pip3 install h5py==2.10.0
echo -e "${GREEN}✓ h5py 2.10.0安装完成${NC}"
echo ""

# 步骤9: 升级其他Python包
echo "[步骤 7/9] 升级Python包..."
sudo -H pip3 install -U testresources numpy
sudo -H pip3 install --upgrade setuptools
sudo -H pip3 install pybind11 protobuf google-pasta
sudo -H pip3 install -U six mock wheel requests gast
sudo -H pip3 install keras_applications --no-deps
sudo -H pip3 install keras_preprocessing --no-deps
echo -e "${GREEN}✓ Python包升级完成${NC}"
echo ""

# 步骤10: 检查numpy版本（跳过降级，Python 3.8兼容更高版本）
echo "[步骤 8/9] 检查numpy版本..."
if python3 -c "import numpy" 2>/dev/null; then
    NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)")
    echo "  当前numpy版本: $NUMPY_VERSION"
    echo -e "${GREEN}✓ Numpy已安装，跳过降级${NC}"
    echo "  注意: Python 3.8可以使用numpy 1.17+版本"
    echo "  如果遇到兼容性问题，可以手动调整"
else
    echo "  Numpy未安装，安装兼容版本..."
    sudo -H pip3 install numpy==1.19.5
    echo -e "${GREEN}✓ Numpy 1.19.5安装完成${NC}"
fi
echo ""

# 步骤11: 安装TensorFlow
echo "[步骤 9/9] 安装TensorFlow 2.4.1..."
echo "  文件: $TF_PATH"
echo "  注意: 可能需要10-15分钟"
echo ""

# 使用系统自带的numpy版本（JetPack优化）
echo "  检查numpy版本..."
if python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null; then
    echo -e "${GREEN}✓ 使用系统numpy${NC}"
else
    echo "  安装系统numpy..."
    pip3 install --force-reinstall --no-deps numpy==1.17.4
fi

# 重命名wheel文件以兼容pip
TF_RENAMED="$DOWNLOAD_DIR/tensorflow-2.4.1-cp38-cp38-linux_aarch64.whl"
if [ "$TF_PATH" != "$TF_RENAMED" ]; then
    echo "  重命名wheel文件..."
    cp "$TF_PATH" "$TF_RENAMED"
    TF_PATH="$TF_RENAMED"
fi

# 跳过依赖检查安装TensorFlow
pip3 install --no-deps "$TF_PATH"
echo -e "${GREEN}✓ TensorFlow 2.4.1安装完成${NC}"
echo ""

# 验证安装
echo "=========================================="
echo "验证安装..."
echo "=========================================="
echo ""

echo "--- TensorFlow ---"
python3 << 'EOF'
try:
    import tensorflow as tf
    print(f"TensorFlow版本: {tf.__version__}")
    print(f"CUDA可用: {tf.test.is_built_with_cuda()}")
    print(f"GPU可用: {tf.test.is_gpu_available()}")
    gpu_devices = tf.config.list_physical_devices('GPU')
    print(f"GPU设备数量: {len(gpu_devices)}")
    if gpu_devices:
        print(f"GPU设备: {gpu_devices}")
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "--- Numpy版本 ---"
python3 << 'EOF'
try:
    import numpy
    print(f"Numpy版本: {numpy.__version__}")
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "提示: 安装的wheel文件仍保留在Downloads文件夹中"
echo "      可以安全删除以释放空间："
echo "      rm $TF_PATH"
echo ""
echo "预计释放空间: 约326MB"
echo ""
echo "注意: "
echo "  1. TensorFlow 2.4.1 wheel专为Python 3.8编译"
echo "  2. numpy版本：Python 3.8支持1.17+，建议使用1.19.5"
echo "  3. 如果遇到问题，可以尝试："
echo "     - pip3 show tensorflow 查看已安装版本"
echo "     - pip3 install --upgrade protobuf"
echo ""