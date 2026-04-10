#!/bin/bash
# Jetson Nano B01 - OpenCV 4.13.0 with CUDA Support 安装脚本
# 跳过下载步骤，直接编译
# 基于 Q-engineering 官方安装指南
# 最后更新: 2026-03-25

set -e

echo "=========================================="
echo "OpenCV 4.13.0 with CUDA Support 安装（跳过下载）"
echo "=========================================="
echo ""
echo "⚠️ 重要提醒:"
echo "  - 编译时间: 约2小时"
echo "  - 需要总内存: 至少8.5GB"
echo "  - 磁盘空间: 约3-4GB"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查OpenCV目录
check_opencv() {
    echo "[检查] OpenCV目录..."

    if [ -d "~/opencv" ]; then
        echo "✓ ~/opencv 存在"
    else
        echo -e "${RED}✗ ~/opencv 不存在${NC}"
        exit 1
    fi

    if [ -d "~/opencv_contrib" ]; then
        echo "✓ ~/opencv_contrib 存在"
    else
        echo -e "${RED}✗ ~/opencv_contrib 不存在${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ OpenCV目录检查通过${NC}"
    echo ""
}

# 检查内存
check_memory() {
    echo "[检查] 系统内存..."
    TOTAL_MEM=$(free -m | awk 'NR==2 {print $2}')
    SWAP_MEM=$(free -m | awk 'NR==3 {print $2}')
    TOTAL=$((TOTAL_MEM + SWAP_MEM))

    echo "  物理内存: ${TOTAL_MEM}MB"
    echo "  Swap空间: ${SWAP_MEM}MB"
    echo "  总内存: ${TOTAL}MB"
    echo ""

    if [ $TOTAL -lt 8500 ]; then
        echo -e "${RED}✗ 总内存不足8.5GB${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ 内存满足要求${NC}"
    fi
    echo ""
}

# 检查磁盘空间
check_disk() {
    echo "[检查] 磁盘空间..."
    DISK_AVAILABLE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    echo "  可用空间: ${DISK_AVAILABLE}GB"
    echo ""

    if [ "$DISK_AVAILABLE" -lt 10 ]; then
        echo -e "${RED}✗ 磁盘空间不足 (至少需要10GB)${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ 磁盘空间充足${NC}"
    fi
    echo ""
}

# 步骤1: 检查
check_opencv
check_memory
check_disk

# 步骤2: 安装依赖
echo "[步骤 1/4] 检查依赖..."
echo ""

# 配置CUDA路径
sudo sh -c "echo '/usr/local/cuda/lib64' >> /etc/ld.so.conf.d/nvidia-tegra.conf"
sudo ldconfig

# 安装依赖（如果需要）
echo "  检查并安装缺失的依赖..."
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake git unzip pkg-config zlib1g-dev \
    libjpeg-dev libjpeg8-dev libjpeg-turbo8-dev \
    libpng-dev libtiff-dev libglew-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libgtk2.0-dev libgtk-3-dev libcanberra-gtk* \
    python3-dev python3-numpy python3-pip \
    libxvidcore-dev libx264-dev libgtk-3-dev \
    libtbb2 libtbb-dev libdc1394-22-dev libxine2-dev \
    gstreamer1.0-tools libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-good1.0-dev \
    libv4l-dev v4l-utils qv4l2 \
    libtesseract-dev libxine2-dev libpostproc-dev \
    libavresample-dev libvorbis-dev \
    libfaac-dev libmp3lame-dev libtheora-dev \
    libopencore-amrnb-dev libopencore-amrwb-dev \
    libopenblas-dev libatlas-base-dev libblas-dev \
    liblapack-dev liblapacke-dev libeigen3-dev gfortran \
    libhdf5-dev libprotobuf-dev protobuf-compiler \
    libgoogle-glog-dev libgflags-dev

echo -e "${GREEN}✓ 依赖检查完成${NC}"
echo ""

# 步骤3: 创建build目录并配置CMake
echo "[步骤 2/4] 配置CMake..."
echo "  启用CUDA, cuDNN等加速功能"
echo ""

cd ~/opencv
mkdir -p build
cd build

cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D EIGEN_INCLUDE_PATH=/usr/include/eigen3 \
    -D WITH_OPENCL=OFF \
    -D WITH_CUDA=ON \
    -D CUDA_ARCH_BIN=5.3 \
    -D CUDA_ARCH_PTX="" \
    -D WITH_CUDNN=ON \
    -D WITH_CUBLAS=ON \
    -D ENABLE_FAST_MATH=ON \
    -D CUDA_FAST_MATH=ON \
    -D OPENCV_DNN_CUDA=ON \
    -D ENABLE_NEON=ON \
    -D WITH_QT=OFF \
    -D WITH_OPENMP=ON \
    -D BUILD_TIFF=ON \
    -D WITH_FFMPEG=ON \
    -D WITH_GSTREAMER=ON \
    -D WITH_TBB=ON \
    -D BUILD_TBB=ON \
    -D BUILD_TESTS=OFF \
    -D WITH_EIGEN=ON \
    -D WITH_V4L=ON \
    -D WITH_LIBV4L=ON \
    -D WITH_PROTOBUF=ON \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D PYTHON3_PACKAGES_PATH=/usr/lib/python3/dist-packages \
    -D OPENCV_GENERATE_PKGCONFIG=ON \
    -D BUILD_EXAMPLES=OFF ..

echo -e "${GREEN}✓ CMake配置完成${NC}"
echo ""

# 步骤4: 编译
echo "[步骤 3/4] 编译OpenCV..."
echo "  ⚠️  这是最耗时的步骤，约需2小时"
echo "  请耐心等待，不要中断..."
echo ""

make -j4

echo -e "${GREEN}✓ OpenCV编译完成${NC}"
echo ""

# 步骤5: 安装
echo "[步骤 4/4] 安装OpenCV..."
echo ""

# 删除旧的opencv2头文件
sudo rm -rf /usr/include/opencv4/opencv2

# 安装
sudo make install
sudo ldconfig

echo -e "${GREEN}✓ OpenCV安装完成${NC}"
echo ""

# 清理
echo "[清理] 清理编译缓存..."
make clean
sudo apt-get update

echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

# 验证安装
echo "=========================================="
echo "验证安装..."
echo "=========================================="
echo ""

echo "--- OpenCV Python版本 ---"
python3 << 'EOF'
try:
    import cv2
    print(f"OpenCV版本: {cv2.__version__}")
    print(f"构建信息: {cv2.getBuildInformation()[:200]}...")
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "--- CUDA支持检查 ---"
python3 << 'EOF'
try:
    import cv2
    info = cv2.getBuildInformation()
    if "CUDA" in info:
        print("✓ CUDA支持: 已启用")
    else:
        print("✗ CUDA支持: 未启用")

    if "cuDNN" in info:
        print("✓ cuDNN支持: 已启用")
    else:
        print("✗ cuDNN支持: 未启用"
except Exception as e:
    print(f"错误: {e}")
EOF
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "提示: 编译的源码文件仍在 ~/opencv 和 ~/opencv_contrib"
echo "      可以删除以释放约1.5GB空间："
echo "      sudo rm -rf ~/opencv ~/opencv_contrib"
echo ""
echo "建议: 在编译完成后，可以考虑删除swap文件以释放空间"
echo ""