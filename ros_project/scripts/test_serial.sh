#!/bin/bash

# 串口通信模块测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  串口通信模块测试"
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

SERIAL_NODE_PID=""

# 清理函数
cleanup() {
    echo ""
    echo "----------------------------------------"
    print_info "清理测试环境..."
    
    # 停止串口节点
    if [ ! -z "$SERIAL_NODE_PID" ]; then
        kill $SERIAL_NODE_PID 2>/dev/null || true
        print_success "已停止串口节点"
    fi
    
    # 清理临时文件
    rm -f /tmp/serial_test_*.log
    print_success "清理临时文件"
    
    echo ""
}

# 设置退出陷阱
trap cleanup EXIT INT TERM

# 检查环境
check_environment() {
    print_header "检查测试环境"
    echo ""
    
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
    python3 -c "import serial" 2>/dev/null && test_result 0 "pyserial已安装" || test_result 1 "pyserial未安装"
    
    echo ""
}

# 列出可用串口
list_serial_ports() {
    print_header "可用串口列表"
    echo ""
    
    print_info "扫描可用的串口设备..."
    
    # 查找USB串口
    if ls /dev/ttyUSB* 2>/dev/null; then
        print_success "找到USB串口设备"
    else
        print_warning "未找到USB串口设备"
    fi
    
    # 查找ACM串口
    if ls /dev/ttyACM* 2>/dev/null; then
        print_success "找到ACM串口设备"
    else
        print_warning "未找到ACM串口设备"
    fi
    
    # 查找THS串口
    if ls /dev/ttyTHS* 2>/dev/null; then
        print_success "找到THS串口设备"
    else
        print_warning "未找到THS串口设备"
    fi
    
    echo ""
}

# 检查串口权限
check_serial_permissions() {
    print_header "检查串口权限"
    echo ""
    
    print_info "检查用户是否在dialout组中..."
    if groups | grep -q dialout; then
        test_result 0 "用户已在dialout组中"
    else
        print_warning "用户不在dialout组中"
        print_info "如需访问串口，请运行: sudo usermod -a -G dialout $USER"
    fi
    
    echo ""
}

# 测试串口节点脚本
test_serial_node_script() {
    print_header "测试串口节点脚本"
    echo ""
    
    # 检查串口节点脚本
    if [ ! -f "src/communication/scripts/serial_comm_node.py" ]; then
        print_error "串口节点脚本不存在"
        return 1
    fi
    
    print_info "检查串口节点脚本语法..."
    python3 -m py_compile src/communication/scripts/serial_comm_node.py
    test_result $? "串口节点脚本语法正确"
    
    # 检查测试脚本
    if [ -f "src/communication/scripts/serial_comm_tester.py" ]; then
        print_info "检查测试脚本语法..."
        python3 -m py_compile src/communication/scripts/serial_comm_tester.py
        test_result $? "测试脚本语法正确"
    fi
    
    echo ""
}

# 启动串口节点（虚拟模式）
start_serial_node_virtual() {
    print_header "启动串口节点（虚拟模式）"
    echo ""
    
    print_info "使用虚拟串口模式启动节点..."
    
    # 使用PTY模拟串口
    print_info "创建虚拟串口对..."
    if ! command -v socat &> /dev/null; then
        print_warning "socat未安装，跳过虚拟串口测试"
        return 1
    fi
    
    # 创建虚拟串口对
    SOCAT_PIDS=$(pgrep -f "socat -d -d pty,raw,echo=0 pty,raw,echo=0")
    if [ -z "$SOCAT_PIDS" ]; then
        socat -d -d pty,raw,echo=0,link=/tmp/ttyVIRTUAL0 pty,raw,echo=0,link=/tmp/ttyVIRTUAL1 &
        sleep 1
        print_info "虚拟串口已创建: /tmp/ttyVIRTUAL0 <-> /tmp/ttyVIRTUAL1"
    else
        print_info "虚拟串口已存在"
    fi
    
    # 启动串口节点
    print_info "启动串口通信节点..."
    roslaunch communication serial_comm.launch serial_port:=/tmp/ttyVIRTUAL0 enable_echo:=true > /tmp/serial_test_node.log 2>&1 &
    SERIAL_NODE_PID=$!
    
    print_info "等待节点启动..."
    sleep 3
    
    if ps -p $SERIAL_NODE_PID > /dev/null 2>&1; then
        test_result 0 "串口节点启动成功"
    else
        print_error "串口节点启动失败"
        print_info "查看日志: cat /tmp/serial_test_node.log"
        return 1
    fi
    
    echo ""
}

# 测试串口话题通信
test_serial_topics() {
    print_header "测试串口话题通信"
    echo ""
    
    # 检查话题列表
    print_info "检查串口话题..."
    topics=("serial/tx" "serial/rx" "serial/status")
    
    for topic in "${topics[@]}"; do
        if timeout 2 rostopic list | grep -q "/$topic"; then
            test_result 0 "话题 /$topic 存在"
        else
            test_result 1 "话题 /$topic 不存在"
        fi
    done
    
    # 测试话题发布
    print_info "测试话题发布..."
    for i in {1..3}; do
        rostopic pub -1 /serial/tx std_msgs/String "data: 'Test message $i'" > /dev/null 2>&1
    done
    sleep 1
    test_result 0 "话题发布功能正常"
    
    # 测试状态话题
    print_info "测试状态话题..."
    timeout 3 rostopic echo /serial/status --noarr > /tmp/serial_test_status.log 2>&1 &
    MONITOR_PID=$!
    sleep 2
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true
    
    if [ -f /tmp/serial_test_status.log ] && [ -s /tmp/serial_test_status.log ]; then
        test_result 0 "状态话题功能正常"
    else
        test_result 1 "状态话题功能异常"
    fi
    
    echo ""
}

# 测试串口回环（需要硬件）
test_serial_loopback() {
    print_header "串口回环测试"
    echo ""
    
    print_warning "回环测试需要硬件支持（TX-RX短接）"
    print_info "如需测试，请手动短接串口的TX和RX引脚"
    print_info "然后运行: python3 src/communication/scripts/serial_comm_tester.py loop"
    
    echo ""
}

# 显示串口信息
show_serial_info() {
    print_header "串口配置信息"
    echo ""
    
    echo "可用ROS话题接口:"
    echo "  /serial/tx    - 发送数据到串口"
    echo "  /serial/rx    - 从串口接收数据"
    echo "  /serial/status - 串口状态信息"
    echo ""
    
    echo "串口配置参数:"
    echo "  serial_port     - 串口端口 (auto为自动检测)"
    echo "  baud_rate       - 波特率 (默认115200)"
    echo "  timeout         - 超时时间 (默认1.0秒)"
    echo "  auto_reconnect  - 自动重连 (默认true)"
    echo "  enable_echo     - 数据回显 (默认false)"
    echo ""
    
    echo "常用波特率:"
    echo "  9600, 19200, 38400, 57600, 115200"
    echo ""
    
    echo "Jetson Nano推荐串口:"
    echo "  /dev/ttyTHS1 - 主串口"
    echo "  /dev/ttyTHS2 - 次串口"
    echo "  /dev/ttyUSB0 - USB转串口"
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
    
    # 列出串口
    list_serial_ports
    
    # 检查权限
    check_serial_permissions
    
    # 测试脚本
    test_serial_node_script
    
    # 启动节点
    start_serial_node_virtual
    
    # 测试话题
    if [ ! -z "$SERIAL_NODE_PID" ]; then
        test_serial_topics
    fi
    
    # 回环测试
    test_serial_loopback
    
    # 显示信息
    show_serial_info
    
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
    echo "  $0           # 完整测试"
    echo "  $0 quick     # 快速测试"
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
        test_serial_node_script
        show_test_report
        ;;
    all)
        main
        ;;
    *)
        main
        ;;
esac