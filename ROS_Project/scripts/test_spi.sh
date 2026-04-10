#!/bin/bash

# SPI通信模块测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  SPI通信模块测试"
echo "=========================================="
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试计数器
TEST_PASSED=0
TEST_FAILED=0
TEST_TOTAL=0

print_header() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

test_result() {
    TEST_TOTAL=$((TEST_TOTAL + 1))
    if [ $1 -eq 0 ]; then
        print_success "$2"
        TEST_PASSED=$((TEST_PASSED + 1))
    else
        print_error "$2"
        TEST_FAILED=$((TEST_FAILED + 1))
    fi
}

# 清理函数
cleanup() {
    echo ""
    echo "----------------------------------------"
    print_info "清理测试环境..."
    rm -f /tmp/spi_test_*.log
    print_success "清理临时文件"
    echo ""
}

# 设置退出陷阱
trap cleanup EXIT INT TERM

# 检查环境
check_environment() {
    print_header "检查测试环境"
    
    # 检查ROS环境
    if [ -z "$ROS_DISTRO" ]; then
        print_error "ROS环境未激活"
        print_info "请运行: source /opt/ros/noetic/setup.bash"
        exit 1
    fi
    test_result 0 "ROS环境已激活 (ROS $ROS_DISTRO)"
    
    # 检查工作空间
    if [ ! -f "devel/setup.bash" ]; then
        print_error "未找到devel/setup.bash"
        print_info "请先运行: catkin_make"
        exit 1
    fi
    
    source devel/setup.bash
    test_result 0 "工作空间环境已激活"
    
    # 检查通信包
    if [ ! -d "src/communication" ]; then
        print_error "communication包不存在"
        exit 1
    fi
    test_result 0 "communication包存在"
    
    # 检查Python依赖
    print_info "检查Python依赖..."
    python3 -c "import spidev" 2>/dev/null && test_result 0 "spidev已安装" || test_result 1 "spidev未安装"
    
    echo ""
}

# 列出SPI设备
list_spi_devices() {
    print_header "扫描SPI设备"
    print_info "扫描SPI设备..."
    
    spi_devices=$(ls -la /dev/spi* 2>/dev/null || true)
    if [ -n "$spi_devices" ]; then
        print_success "找到SPI设备"
        echo "$spi_devices" | while read line; do
            echo "  $line"
        done
    else
        print_warning "未找到SPI设备"
    fi
    
    # 检查SPI设备状态
    print_info "检查SPI内核模块..."
    if lsmod | grep -q spidev; then
        test_result 0 "spidev内核模块已加载"
    else
        print_warning "spidev内核模块未加载"
        print_info "运行: sudo modprobe spidev"
    fi
    
    echo ""
}

# 检查SPI权限
check_spi_permissions() {
    print_header "检查SPI权限"
    print_info "检查SPI设备权限..."
    
    if groups | grep -q spi; then
        test_result 0 "用户已在spi组中"
    else
        print_warning "用户不在spi组中"
        print_info "如需访问SPI，请运行: sudo usermod -a -G spi $USER"
    fi
    
    echo ""
}

# 测试SPI节点脚本
test_spi_node_script() {
    print_header "测试SPI节点脚本"
    
    if [ ! -f "src/communication/scripts/spi_comm_node.py" ]; then
        print_error "SPI节点脚本不存在"
        return 1
    fi
    
    print_info "检查SPI节点脚本语法..."
    python3 -m py_compile src/communication/scripts/spi_comm_node.py
    test_result $? "SPI节点脚本语法正确"
    
    echo ""
}

# 测试SPI硬件
test_spi_hardware() {
    print_header "测试SPI硬件"
    
    print_info "测试SPI硬件连接..."
    
    python3 << 'EOF' 2>/dev/null
import sys

try:
    import spidev
    
    # 测试/dev/spidev0.0
    try:
        spi = spidev.SpiDev()
        spi.open('/dev/spidev0.0')
        print("  ✅ SPI设备 /dev/spidev0.0 已打开")
        
        # 设置SPI参数
        spi.max_speed_hz = 1000000
        spi.mode = 0
        spi.bits_per_word = 8
        print("  ✅ SPI参数设置成功")
        print(f"     速度: 1000000Hz")
        print(f"     模式: 0")
        print(f"     位数: 8")
        
        # 测试回环（如果有硬件支持）
        test_data = [0x41, 0x42, 0x43]  # "ABC"
        print(f"  发送测试数据: {' '.join(f'0x{b:02X}' for b in test_data)}")
        
        response = spi.xfer2(test_data)
        print(f"  接收数据: {' '.join(f'0x{b:02X}' for b in response)}")
        
        spi.close()
        print("  ✅ SPI硬件测试完成")
        
    except FileNotFoundError:
        print("  ⚠️  未找到SPI设备")
        print("  这可能是因为：")
        print("    1. Jetson Nano的SPI引脚未被启用")
        print("    2. 需要配置设备树来启用SPI")
        print("    3. 可以使用sudo运行测试")
        
    except PermissionError:
        print("  ❌ 权限不足")
        print("    解决方案:")
        print("      sudo usermod -a -G spi \$USER")
        print("      然后重新登录")
        
    except Exception as e:
        print(f"  ❌ SPI硬件测试失败: {e}")

except ImportError:
    print("  ❌ spidev库未安装")
    print("    解决方案:")
    print("      pip3 install spidev")

EOF
    
    echo ""
}

# 显示SPI信息
show_spi_info() {
    print_header "SPI配置信息"
    
    echo "Jetson Nano SPI引脚映射:"
    echo "  SPI0 (MOSI/MISO/SCLK/CS):"
    echo "    19号引脚 (MOSI) - GPIO10 / SPI_MOSI"
    echo "    21号引脚 (MISO) - GPIO9 / SPI_MISO"
    echo("    23号引脚 (SCLK) - GPIO11 / SPI_SCLK")
    echo("    24号引脚 (CS0)  - GPIO8  / SPI_CS0_N")
    echo("    26号引脚 (CS1)  - GPIO7  / SPI_CS1_N")
    echo ""
    echo "  SPI1 (MOSI/MISO/SCLK):"
    echo("    38号引脚 (MOSI) - GPIO20 / SPI1_MOSI")
    echo("    40号引脚 (MISO) - GPIO19 / SPI1_MISO")
    echo("    缺少SCLK和CS引脚")
    echo ""
    
    echo "可用ROS话题接口:"
    echo "  /spi/transfer - SPI数据传输（发送和接收）"
    echo "  /spi/write     - SPI写入数据"
    echo "  /spi/read      - SPI读取数据"
    echo "  /spi/rx        - 接收SPI数据"
    echo "  /spi/status     - SPI状态信息"
    echo ""
    
    echo "SPI配置参数:"
    echo "  spi_device      - SPI设备路径 (默认 /dev/spidev0.0)"
    echo "  spi_mode        - SPI模式 (0-3，默认0)"
    echo "  max_speed      - 最大速度 (Hz，默认1000000)"
    echo "  bits_per_word   - 每字位数 (默认8)"
    echo "  enable_echo     - 数据回显 (默认false)"
    echo ""
    
    echo "SPI模式说明:"
    echo "  0 - CPOL=0, CPHA=0"
    echo "  1 - CPOL=0, CPHA=1"
    echo "   2 - CPOL=1, CPHA=0"
    echo "   - CPOL=1, CPHA=1"
    echo ""
    
    echo "常用SPI设备:"
    echo "  模数转换器 (ADC/DAC)"
    "  显示屏 (OLED, TFT LCD)"
    "  传感器 (加速度计, 陀螺仪)"
    "  存储器 (Flash, SD卡)"
    echo ""
}

# 显示测试报告
show_test_report() {
    print_header "测试报告"
    echo ""
    echo "测试统计:"
    echo "  通过: ${GREEN}${TEST_PASSED}${NC}"
    echo "  失败: ${RED}${TEST_FAILED}${NC}"
    echo "  总计: ${TEST_TOTAL}"
    echo ""
    
    if [ $TEST_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 所有测试通过！${NC}"
        return 0
    else
        echo -e "${RED}⚠️  有 ${TEST_FAILED} 个测试失败${NC}"
        return 1
    fi
}

# 主函数
main() {
    # 检查环境
    check_environment
    
    # 列出SPI设备
    list_spi_devices
    
    # 检查权限
    check_spi_permissions
    
    # 测试脚本
    test_spi_node_script
    
    # 测试硬件
    test_spi_hardware
    
    # 显示信息
    show_spi_info
    
    # 显示报告
    show_test_report
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  all   - 完整测试（默认）"
    echo "  quick - 快速测试（仅语法检查）"
    echo "  help  - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0          # 完整测试"
    echo "  $0 quick    # 快速测试"
}

# 参数处理
case "$1" in
    help|--help|-h)
        show_help
        exit 0
        ;;
    quick)
        print_header "快速测试模式"
        check_environment
        test_spi_node_script
        show_test_report
        ;;
    all)
        main
        ;;
    *)
        main
        ;;
esac