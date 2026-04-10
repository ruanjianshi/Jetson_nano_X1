#!/bin/bash

# I2C通信模块测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  I2C通信模块测试"
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
    rm -f /tmp/i2c_test_*.log
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
    
    # 检查I2C包
    if [ ! -d "src/communication" ]; then
        print_error "communication包不存在"
        exit 1
    fi
    test_result 0 "communication包存在"
    
    # 检查Python依赖
    print_info "检查Python依赖..."
    python3 -c "import smbus2" 2>/dev/null && test_result 0 "smbus2已安装" || test_result 1 "smbus2未安装"
    
    echo ""
}

# 列出I2C设备
list_i2c_devices() {
    print_header "扫描I2C设备"
    print_info "扫描I2C-1和I2C-2总线..."
    
    for i in 1 2; do
        print_info ""
        print_info "I2C-$i 总线:"
        
        # 尝试扫描I2C总线
        python3 << EOF 2>/dev/null
import smbus2

try:
    bus = smbus2.SMBus(i)
    print(f"  ✅ I2C-$i 总线可用")
    
    # 扫描设备
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.write_byte(addr, 0)
            devices.append(addr)
            print(f"    发现设备: 0x{addr:02X}")
        except:
            pass
    
    if devices:
        print(f"  总共发现 {len(devices)} 个I2C设备")
    else:
        print(f"  未发现I2C设备")
        
    bus.close()
except Exception as e:
    print(f"  ❌ I2C-$i 总线不可用: {e}")
EOF
    done
    
    echo ""
}

# 检查I2C权限
check_i2c_permissions() {
    print_header "检查I2C权限"
    print_info "检查I2C设备权限..."
    
    i2c_devices=$(ls -la /dev/i2c* 2>/dev/null || true)
    if [ -n "$i2c_devices" ]; then
        print_success "找到I2C设备"
        echo "$i2c_devices" | while read line; do
            echo "  $line"
        done
    else
        print_warning "未找到I2C设备"
    fi
    
    # 检查i2c组
    if groups | grep -q i2c; then
        test_result 0 "用户已在i2c组中"
    else
        print_warning "用户不在i2c组中"
        print_info "如需访问I2C，请运行: sudo usermod -a -G i2c $USER"
    fi
    
    echo ""
}

# 测试I2C节点脚本
test_i2c_node_script() {
    print_header "测试I2C节点脚本"
    
    if [ ! -f "src/communication/scripts/i2c_comm_node.py" ]; then
        print_error "I2C节点脚本不存在"
        return 1
    fi
    
    print_info "检查I2C节点脚本语法..."
    python3 -m py_compile src/communication/scripts/i2c_comm_node.py
    test_result $? "I2C节点脚本语法正确"
    
    if [ -f "src/communication/scripts/spi_comm_node.py" ]; then
        print_info "检查SPI节点脚本语法..."
        python3 -spile src/communication/scripts/spi_comm_node.py
        test_result $? "SPI节点脚本语法正确"
    fi
    
    echo ""
}

# 启动I2C节点
start_i2c_node() {
    print_header "启动I2C节点"
    
    print_info "启动I2C通信节点..."
    roslaunch communication i2c_comm_launch i2c_bus:=1 device_address:=0x48 auto_scan:=true enable_echo:=true > /tmp/i2c_test_node.log 2>&1 &
    NODE_PID=$!
    
    print_info "等待节点启动..."
    sleep 3
    
    if ps -p $NODE_PID > /dev/null 2>&1; then
        test_result 0 "I2C节点启动成功"
    else
        print_error "I2C节点启动失败"
        print_info "查看日志: cat /tmp/i2c_test_node.log"
        return 1
    fi
    
    echo ""
}

# 测试I2C话题通信
test_i2c_topics() {
    print_header "测试I2C话题通信"
    
    # 检查话题列表
    print_info "检查I2C话题..."
    topics=("i2c/write_byte" "i2c/write_bytes" "i2c/read_byte" "i2c/set_address" "i2c/rx_byte" "i2c/rx_bytes" "i2c/status")
    
    for topic in "${topics[@]}"; do
        if timeout 2 rostopic list | grep -q "/$topic"; then
            test_result 0 "话题 /$topic 存在"
        else
            test_result 1 "话题 /$topic 不存在"
        fi
    done
    
    # 测试写入字节
    print_info "测试I2C写入功能..."
    rostopic pub -1 /i2c/write_byte std_msgs/Int32 "data: 0x48" > /dev/null 2>&1
    sleep 1
    test_result 0 "I2C写入字节功能正常"
    
    # 测试读取字节
    print_info "测试I2C读取功能..."
    rostopic pub -1 /i2c/read_byte std_msgs/Int32 "data: 0" > /dev/null 2>&1
    sleep 1
    test_result 0 "I2C读取字节功能正常"
    
    # 测试状态话题
    print_info "测试I2C状态话题..."
    timeout 3 rostopic echo /i2c/status --noarr > /tmp/i2c_test_status.log 2>&1 &
    MONITOR_PID=$!
    sleep 2
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true
    
    if [ -f /tmp/i2c_test_status.log ] && [ -s /tmp/i2c_test_status.log ]; then
        test_result 0 "I2C状态话题功能正常"
    else
        test_result 1 "I2C状态话题功能异常"
    fi
    
    echo ""
}

# 测试I2C硬件
test_i2c_hardware() {
    print_header "测试I2C硬件"
    
    print_info "测试I2C-1总线硬件连接..."
    
    python3 << 'EOF' 2>/dev/null
import smbus2

try:
    # 测试I2C-1总线
    bus = smbus2.SMBus(1)
    print("  ✅ I2C-1总线已打开")
    
    # 尝试扫描
    print("  扫描I2C设备...")
    devices = []
    for addr in range(0x03, 0x78):
        try:
            bus.write_byte(addr, 0)
            devices.append(addr)
        except:
            pass
    
    if devices:
        print(f"  ✅ 发现 {len(devices)} 个I2C设备:")
        for addr in devices:
            print(f"    0x{addr:02X}")
    else:
        print("  ⚠️  未发现I2C设备")
        print("  这可能是正常的，如果板子上没有连接I2C设备")
    
    bus.close()
    print("  ✅ I2C硬件测试完成")
    
except Exception as e:
    print(f"  ❌ I2C硬件测试失败: {e}")
    print("  可能原因:")
    print("    1. 用户不在i2c组中")
    print("    2. I2C总线未启用")
    print("    3. 需要sudo权限")
    
    if "Permission denied" in str(e) or "Access denied" in str(e):
        print("\n  解决方案:")
        print("    sudo usermod -a -G i2c \$USER")
        print("    然后重新登录")

EOF
    
    echo ""
}

# 显示I2C信息
show_i2c_info() {
    print_header "I2C配置信息"
    
    echo "Jetson Nano I2C引脚映射:"
    echo "  I2C-1 (SDA/SCL):"
    echo "    3号引脚 (SDA) - GPIO2 / SDA_1"
    echo "    5号引脚 (SCL) - GPIO3 / SCL_1"
    echo ""
    echo "  I2C-2 (SDA/SCL):"
    echo "    27号引脚 (SDA) - GPIO18 / SDA_2"
    echo "    28号引脚 (SCL) - GPIO19 / SCL_2"
    echo ""
    
    echo "可用ROS话题接口:"
    echo "  /i2c/write_byte   - 写入单个字节到I2C设备"
    echo "  /i2c/write_bytes  - 写入多个字节到I2C设备"
    echo "  /i2c/read_byte    - 从I2C设备读取字节"
    echo "  /i2c/set_address  - 设置I2C设备地址"
    echo "  /i2c/rx_byte      - 接收I2C数据（单个字节）"
    echo "  /i2c/rx_bytes     - 接收I2C数据（多个字节）"
    echo "  /i2c/status       - I2C状态信息"
    echo ""
    
    echo "I2C配置参数:"
    echo "  i2c_bus       - I2C总线号 (1或2)"
    echo "  device_address - I2C设备地址 (16进制，如0x48)"
    echo "  auto_scan     - 自动扫描I2C设备 (true/false)"
    echo "  enable_echo    - 数据回显 (true/false)"
    echo ""
    
    echo "常用I2C设备地址:"
    echo "  0x48 - PCF8574 (RTC)"
    echo "  0x50 - EEPROM (24LC64)"
    echo "  0x68 - MPU6050 (IMU)"
    echo "  0x76 - BNO055 (IMU)"
    echo "  0x77 - BNO055 (IMU)"
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
    
    # 列出I2C设备
    list_i2c_devices
    
    # 检查权限
    check_i2c_permissions
    
    # 测试脚本
    test_i2c_node_script
    
    # 测试硬件
    test_i2c_hardware
    
    # 启动节点（如果硬件可用）
    # start_i2c_node
    
    # 测试话题（如果节点启动）
    # test_i2c_topics
    
    # 显示信息
    show_i2c_info
    
    # 显示报告
    show_test_report
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  all   - 完整测试（默认）"
    echo  " quick - 快速测试（仅语法检查）"
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
        test_i2c_node_script
        show_test_report
        ;;
    all)
        main
        ;;
    *)
        main
        ;;
esac