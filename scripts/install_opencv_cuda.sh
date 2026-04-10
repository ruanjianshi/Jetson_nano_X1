#!/bin/bash
# Jetson Nano B01 - OpenCV 4.13.0 with CUDA Support 安装脚本
# 基于 Q-engineering 官方安装指南
# 最后更新: 2026-03-24

set -e

echo "=========================================="
echo "OpenCV 4.13.0 with CUDA Support 安装"
echo "=========================================="
echo ""
echo "⚠️ 重要提醒:"
echo "  - 编译时间: 约2小时"
echo "  - 需要总内存: 至少8.5GB"
echo "  - 磁盘空间: 约3-4GB"
echo "  - 需要增加swap空间"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
        echo "  需要增加swap空间"
        echo ""
        read -p "是否继续? [y/N]: " continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            echo "安装已取消"
            exit 1
        fi
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
        echo "  请清理磁盘空间"
        exit 1
    else
        echo -e "${GREEN}✓ 磁盘空间充足${NC}"
    fi
    echo ""
}

# 安装dphys-swapfile
install_swap() {
    echo "[准备] 安装swap扩展..."
    echo "  这将增加swap空间以支持编译"
    echo ""

    sudo apt-get update
    sudo apt-get install -y nano dphys-swapfile

    # 修改最大边界
    echo "  配置dphys-swapfile..."
    sudo sed -i 's/CONF_SWAPFILE_MAX=2048/CONF_SWAPFILE_MAX=4096/' /sbin/dphys-swapfile

    # 配置swap大小
    sudo bash -c 'cat > /etc/dphys-swapfile << EOF
CONF_SWAPSIZE=4096
CONF_SWAPFILE=/var/swap
EOF'

    echo -e "${GREEN}✓ swap配置完成${NC}"
    echo ""
    echo "⚠️  需要重启以应用swap配置"
    echo ""
    read -p "是否现在重启? [y/N]: " reboot_choice
    if [[ "$reboot_choice" =~ ^[Yy]$ ]]; then
        echo "重启中..."
        sudo reboot
        exit 0
    else
        echo -e "${YELLOW}⚠ 请手动重启后再运行此脚本${NC}"
        echo "  命令: sudo reboot"
        exit 0
    fi
}

# 步骤1: 检查系统资源
check_memory
check_disk

# 步骤2: 检查swap是否已配置
SWAP_TOTAL=$(free -m | awk 'NR==3 {print $2}')
if [ "$SWAP_TOTAL" -lt 4000 ]; then
    echo -e "${YELLOW}⚠ Swap空间不足 (当前: ${SWAP_TOTAL}MB, 需要: 至少4000MB)${NC}"
    echo ""
    read -p "是否配置swap? [y/N]: " install_swap_choice
    if [[ "$install_swap_choice" =~ ^[Yy]$ ]]; then
        install_swap
    else
        echo -e "${RED}✗ Swap空间不足，编译可能会失败${NC}"
        echo "  建议配置swap后再继续"
        exit 1
    fi
fi

# 步骤3: 安装依赖
echo "[步骤 1/6] 安装依赖..."
echo "  这需要一些时间，请耐心等待..."
echo ""

# 配置CUDA路径
sudo sh -c "echo '/usr/local/cuda/lib64' >> /etc/ld.so.conf.d/nvidia-tegra.conf"
sudo ldconfig

# 安装依赖
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

echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

# 询问是否安装Qt5（可选）
echo "=========================================="
echo "Qt5支持（可选）"
echo "=========================================="
echo ""
echo "Qt5可以美化OpenCV的GUI界面（窗口、滑块等）"
echo "但不影响OpenCV的核心功能"
echo ""
echo "优点: 界面更美观"
echo "缺点: 稍微降低性能（约2-3%），占用约500MB空间"
echo ""
read -p "是否安装Qt5支持? [y/N]: " qt5_choice

if [[ "$qt5_choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo "[可选] 安装Qt5..."
    sudo apt-get install -y qt5-default
    echo -e "${GREEN}✓ Qt5安装完成${NC}"
    WITH_QT="ON"
else
    echo -e "${YELLOW}⚠ 跳过Qt5安装${NC}"
    WITH_QT="OFF"
fi
echo ""

# 步骤4: 下载OpenCV（从本地Downloads）
echo "[步骤 2/6] 准备OpenCV 4.13.0..."
echo "  检查Downloads目录中的文件..."
echo ""

DOWNLOAD_DIR="/home/jetson/Downloads"

# 检查opencv.zip
if [ -f "$DOWNLOAD_DIR/opencv.zip" ]; then
    echo "✓ 找到 opencv.zip (22MB)"
    cp "$DOWNLOAD_DIR/opencv.zip" ~/
else
    echo "⚠ opencv.zip不在Downloads目录，尝试下载..."
    cd ~
    wget -O opencv.zip https://github.com/opencv/opencv/archive/4.13.0.zip
fi

# 检查opencv_contrib
if [ -f "$DOWNLOAD_DIR/opencv_contrib-4.13.0.zip" ]; then
    echo "✓ 找到 opencv_contrib-4.13.0.zip (56MB)"
    cp "$DOWNLOAD_DIR/opencv_contrib-4.13.0.zip" ~/
else
    echo "⚠ opencv_contrib-4.13.0.zip不在Downloads目录，尝试下载..."
    cd ~
    wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.13.0.zip
fi

# 解压
echo ""
echo "  解压文件..."
cd ~
if [ ! -d "opencv" ]; then
    unzip -q opencv.zip
    mv opencv-4.13.0 opencv
    rm opencv.zip
    echo "  ✓ OpenCV主仓库解压完成"
else
    echo "  ⚠ opencv目录已存在，跳过解压"
    [ -f opencv.zip ] && rm opencv.zip
fi

if [ ! -d "opencv_contrib" ]; then
    unzip -q opencv_contrib-4.13.0.zip
    mv opencv_contrib-4.13.0 opencv_contrib
    rm opencv_contrib-4.13.0.zip
    echo "  ✓ OpenCV contrib解压完成"
else
    echo "  ⚠ opencv_contrib目录已存在，跳过解压"
    [ -f opencv_contrib-4.13.0.zip ] && rm opencv_contrib-4.13.0.zip
fi

echo -e "${GREEN}✓ OpenCV准备完成${NC}"
echo ""

# 步骤5: 创建build目录并配置CMake
echo "[步骤 3/6] 配置CMake..."
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

# 步骤6: 编译
echo "[步骤 4/6] 编译OpenCV..."
echo "  ⚠️  这是最耗时的步骤，约需2小时"
echo "  请耐心等待，不要中断..."
echo ""

make -j4

echo -e "${GREEN}✓ OpenCV编译完成${NC}"
echo ""

# 步骤7: 安装
echo "[步骤 5/6] 安装OpenCV..."
echo ""

# 删除旧的opencv2头文件
sudo rm -rf /usr/include/opencv4/opencv2

# 安装
sudo make install
sudo ldconfig

echo -e "${GREEN}✓ OpenCV安装完成${NC}"
echo ""

# 步骤8: 清理
echo "[步骤 6/6] 清理..."
echo ""

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
        print("✗ cuDNN支持: 未启用")
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
echo "提示: swap文件可以删除以释放空间："
echo "      sudo /etc/init.d/dphys-swapfile stop"
echo "      sudo apt-get remove --purge dphys-swapfile"
echo ""