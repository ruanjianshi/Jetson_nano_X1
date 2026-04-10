#!/bin/bash
# Jetson Nano B01 - TensorFlow 2.4.1 安装脚本
# 基于 Q-engineering 官方安装指南
# 最后更新: 2026-03-24

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "TensorFlow 2.4.1 安装脚本"
echo "=========================================="
echo ""

# ===== 函数定义 =====

# 检查TensorFlow是否已安装
check_tensorflow_installed() {
    echo "[检查] TensorFlow是否已安装..."

    # 检查Python包
    if python3 -c "import tensorflow" 2>/dev/null; then
        VERSION=$(python3 -c "import tensorflow; print(tensorflow.__version__)")
        echo -e "${GREEN}✓ TensorFlow已安装${NC}"
        echo "  版本: $VERSION"

        # 检查CUDA支持
        GPU_SUPPORT=$(python3 -c "import tensorflow as tf; print('是' if tf.test.is_gpu_available() else '否')" 2>/dev/null || echo "未知")
        echo "  GPU支持: $GPU_SUPPORT"

        # 询问用户是否重新安装
        echo ""
        echo -e "${YELLOW}是否重新安装TensorFlow?${NC}"
        echo "  [1] 重新安装"
        echo "  [2] 退出"
        read -p "请选择 [1/2]: " choice
        case $choice in
            1) echo "继续安装...";;
            2) echo "安装已取消"; exit 0;;
            *) echo "无效选择，继续安装...";;
        esac
    else
        echo -e "${GREEN}✓ TensorFlow未安装${NC}"
        echo "  准备进行安装..."
    fi
    echo ""
}

# 检查系统环境
check_system_requirements() {
    echo "[检查] 系统环境..."

    # 检查Python版本
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    echo "  Python版本: $PYTHON_VERSION"

    # 检查numpy版本
    if python3 -c "import numpy" 2>/dev/null; then
        NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)")
        echo "  Numpy版本: $NUMPY_VERSION"

        # 检查numpy版本是否需要降级
        if [[ "$NUMPY_VERSION" > "1.18.5" ]]; then
            echo -e "${YELLOW}  ⚠ Numpy版本过高，建议降级到1.18.5${NC}"
            echo "  TensorFlow 2.4可能与numpy $NUMPY_VERSION 不兼容"
        fi
    else
        echo "  Numpy: 未安装"
    fi

    # 检查磁盘空间
    DISK_AVAILABLE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_AVAILABLE" -lt 3 ]; then
        echo -e "${RED}  ✗ 磁盘空间不足 (至少需要3GB)${NC}"
        echo "  可用空间: ${DISK_AVAILABLE}GB"
        exit 1
    else
        echo "  磁盘空间: ${DISK_AVAILABLE}GB (可用)"
    fi

    echo -e "${GREEN}✓ 系统环境检查完成${NC}"
    echo ""
}

# 检查Python版本兼容性
check_python_compatibility() {
    echo "[检查] Python版本兼容性..."

    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    PYTHON_VERSION_CODE="cp${PYTHON_MAJOR}${PYTHON_MINOR}"

    echo "  Python版本编码: $PYTHON_VERSION_CODE"

    # TensorFlow 2.4.1官方wheel是为Python 3.6设计的(cp36)
    # 如果系统是Python 3.8，需要确认是否有对应的wheel
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -eq 8 ]; then
        echo -e "${YELLOW}  ⚠ 警告: TensorFlow 2.4.1官方wheel为Python 3.6设计${NC}"
        echo "  当前系统: Python 3.8"
        echo ""
        echo "  选项:"
        echo "  [1] 尝试安装TensorFlow 2.4.1 (可能不兼容)"
        echo "  [2] 安装TensorFlow 2.7.0 (JetPack 4.6官方版本，推荐)"
        echo "  [3] 退出"
        read -p "请选择 [1/2/3]: " tf_choice
        case $tf_choice in
            2)
                echo "选择安装TensorFlow 2.7.0..."
                INSTALL_TF_2_7=true
                ;;
            3)
                echo "安装已取消"
                exit 0
                ;;
            *)
                echo "继续安装TensorFlow 2.4.1..."
                INSTALL_TF_2_7=false
                ;;
        esac
    else
        INSTALL_TF_2_7=false
    fi

    echo ""
}

# ===== 主安装流程 =====

# 步骤1: 检查TensorFlow是否已安装
check_tensorflow_installed

# 步骤2: 检查系统环境
check_system_requirements

# 步骤3: 检查Python版本兼容性
check_python_compatibility

# 如果选择了TensorFlow 2.7.0
if [ "$INSTALL_TF_2_7" = true ]; then
    echo "=========================================="
    echo "安装 TensorFlow 2.7.0 (JetPack 4.6官方版本)"
    echo "=========================================="
    echo ""

    echo "[步骤 1/2] 安装依赖..."
    sudo apt-get update
    sudo apt-get install -y libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
    echo ""

    echo "[步骤 2/2] 安装TensorFlow 2.7.0..."
    pip3 install --pre --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v461/tensorflow tensorflow==2.7.0
    echo -e "${GREEN}✓ TensorFlow 2.7.0安装完成${NC}"
    echo ""

else
    # 继续安装TensorFlow 2.4.1
    echo "=========================================="
    echo "安装 TensorFlow 2.4.1"
    echo "=========================================="
    echo ""

    # 步骤1: 卸载旧版本
    echo "[步骤 1/12] 卸载旧版本..."
    sudo pip uninstall tensorflow -y 2>/dev/null || true
    sudo pip3 uninstall tensorflow -y 2>/dev/null || true
    echo -e "${GREEN}✓ 旧版本已清理${NC}"
    echo ""

    # 步骤2: 更新系统
    echo "[步骤 2/12] 更新系统..."
    sudo apt-get update
    sudo apt-get upgrade -y
    echo -e "${GREEN}✓ 系统更新完成${NC}"
    echo ""

    # 步骤3: 安装pip
    echo "[步骤 3/12] 安装pip..."
    sudo apt-get install -y python-pip python3-pip
    echo -e "${GREEN}✓ pip安装完成${NC}"
    echo ""

    # 步骤4: 安装系统依赖
    echo "[步骤 4/12] 安装系统依赖..."
    sudo apt-get install -y gfortran
    sudo apt-get install -y libhdf5-dev libc-ares-dev libeigen3-dev
    sudo apt-get install -y libatlas-base-dev libopenblas-dev libblas-dev
    sudo apt-get install -y liblapack-dev
    echo -e "${GREEN}✓ 系统依赖安装完成${NC}"
    echo ""

    # 步骤5: 安装Python依赖
    echo "[步骤 5/12] 安装Python依赖..."
    sudo -H pip3 install Cython==0.29.21
    echo -e "${GREEN}✓ Cython安装完成${NC}"

    # 步骤6: 安装h5py
    echo "[步骤 6/12] 安装h5py (可能需要6-10分钟)..."
    sudo -H pip3 install h5py==2.10.0
    echo -e "${GREEN}✓ h5py安装完成${NC}"

    # 步骤7: 升级其他Python包
    echo "[步骤 7/12] 升级Python包..."
    sudo -H pip3 install -U testresources numpy
    sudo -H pip3 install --upgrade setuptools
    sudo -H pip3 install pybind11 protobuf google-pasta
    sudo -H pip3 install -U six mock wheel requests gast
    sudo -H pip3 install keras_applications --no-deps
    sudo -H pip3 install keras_preprocessing --no-deps
    echo -e "${GREEN}✓ Python包升级完成${NC}"
    echo ""

    # 步骤8: 安装gdown
    echo "[步骤 8/12] 安装gdown..."
    sudo -H pip3 install gdown
    echo -e "${GREEN}✓ gdown安装完成${NC}"
    echo ""

    # 步骤9: 下载TensorFlow 2.4.1
    echo "[步骤 9/12] 下载TensorFlow 2.4.1 (约1.8GB)..."
    gdown https://drive.google.com/uc?id=1DLk4Tjs8Mjg919NkDnYg02zEnbbCAzOz
    echo -e "${GREEN}✓ TensorFlow下载完成${NC}"
    echo ""

    # 步骤10: 安装TensorFlow
    echo "[步骤 10/12] 安装TensorFlow 2.4.1 (可能需要10-15分钟)..."
    sudo -H pip3 install tensorflow-2.4.1-cp36-cp36m-linux_aarch64.whl
    echo -e "${GREEN}✓ TensorFlow安装完成${NC}"
    echo ""

    # 步骤11: 清理临时文件
    echo "[步骤 11/12] 清理临时文件..."
    rm -f tensorflow-2.4.1-cp36-cp36m-linux_aarch64.whl
    echo -e "${GREEN}✓ 清理完成${NC}"
    echo ""

    # 步骤12: 降级numpy (如果需要)
    echo "[步骤 12/12] 检查numpy版本..."
    if python3 -c "import numpy" 2>/dev/null; then
        NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)")
        if [[ "$NUMPY_VERSION" > "1.18.5" ]]; then
            echo -e "${YELLOW}⚠ Numpy版本过高: $NUMPY_VERSION${NC}"
            echo "降级到numpy 1.18.5..."
            sudo -H pip3 uninstall numpy -y
            sudo -H pip3 install numpy==1.18.5
            echo -e "${GREEN}✓ Numpy已降级到1.18.5${NC}"
        else
            echo -e "${GREEN}✓ Numpy版本正常: $NUMPY_VERSION${NC}"
        fi
    fi
    echo ""
fi

# 验证安装
echo "=========================================="
echo "验证安装..."
echo "=========================================="
echo ""

echo "--- TensorFlow ---"
python3 -c "import tensorflow as tf; print(f'TensorFlow版本: {tf.__version__}'); print(f'GPU可用: {tf.test.is_gpu_available()}')" 2>&1 || echo -e "${RED}✗ TensorFlow验证失败${NC}"
echo ""

echo "--- TensorFlow详细信息 ---"
python3 << 'EOF'
try:
    import tensorflow as tf
    print(f"版本: {tf.__version__}")
    print(f"GPU设备: {tf.config.list_physical_devices('GPU')}")
    print(f"CUDA可用: {tf.test.is_built_with_cuda()}")
    print(f"GPU可用: {tf.test.is_gpu_available()}")
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "提示: 如果遇到问题，请查看详细安装指南："
echo "/home/jetson/Desktop/Jetson_Nano/README/PyTorch_TensorFlow_安装指南.md"
echo ""
echo "注意: TensorFlow 2.4.1需要numpy 1.18.5，其他包可能会自动升级numpy"
echo "      如果出现兼容性问题，请手动降级numpy"
echo ""