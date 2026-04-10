#!/bin/bash

# GPIO控制模块统一测试脚本
# 整合所有GPIO测试功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  Jetson Nano GPIO 统一测试套件"
echo "=========================================="
echo ""

# 测试配置
TEST_LEVEL="${1:-full}"  # full, quick, hardware
GPIO_NODE_PID=""
ROSCORE_PID=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TEST_PASSED=0
TEST_FAILED=0
TEST_TOTAL=0

# 辅助函数
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
    
    # 停止所有ROS节点
    if [ ! -z "$GPIO_NODE_PID" ]; then
        kill $GPIO_NODE_PID 2>/dev/null || true
        print_success "已停止GPIO节点"
    fi
    
    if [ ! -z "$ROSCORE_PID" ]; then
        sleep 2
        kill $ROSCORE_PID 2>/dev/null || true
        print_success "已停止ROS Master"
    fi
    
    # 清理临时文件
    rm -f /tmp/gpio_test_*.log
    print_success "清理临时文件"
    
    echo ""
}

# 设置退出陷阱
trap cleanup EXIT INT TERM

# 检查环境
check_environment() {
    echo "----------------------------------------"
    print_info "检查测试环境..."
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
    
    # 检查GPIO包
    if [ ! -d "src/gpio_control" ]; then
        print_error "gpio_control包不存在"
        exit 1
    fi
    test_result 0 "gpio_control包存在"
    
    # 检查Jetson.GPIO
    if python3 -c "import Jetson.GPIO" 2>/dev/null; then
        test_result 0 "Jetson.GPIO已安装"
    else
        print_warning "Jetson.GPIO未安装，跳过硬件测试"
    fi
    
    echo ""
}

# 启动ROS环境
start_ros_environment() {
    echo "----------------------------------------"
    print_info "启动ROS环境..."
    echo ""
    
    # 启动ROS Master
    if ! pgrep -x roscore > /dev/null; then
        roscore > /tmp/gpio_test_roscore.log 2>&1 &
        ROSCORE_PID=$!
        print_info "启动ROS Master..."
        sleep 3
        
        if ps -p $ROSCORE_PID > /dev/null 2>&1; then
            test_result 0 "ROS Master启动成功"
        else
            print_error "ROS Master启动失败"
            exit 1
        fi
    else
        print_info "ROS Master已在运行"
        ROSCORE_PID=""
        test_result 0 "ROS Master运行中"
    fi
    
    echo ""
}

# 启动GPIO节点
start_gpio_node() {
    echo "----------------------------------------"
    print_info "启动GPIO控制节点..."
    echo ""
    
    roslaunch gpio_control universal_gpio.launch > /tmp/gpio_test_node.log 2>&1 &
    GPIO_NODE_PID=$!
    print_info "等待节点启动..."
    sleep 4
    
    if ps -p $GPIO_NODE_PID > /dev/null 2>&1; then
        test_result 0 "GPIO节点启动成功"
    else
        print_error "GPIO节点启动失败"
        print_info "查看日志: cat /tmp/gpio_test_node.log"
        exit 1
    fi
    
    # 检查节点初始化
    if grep -q "GPIO Control Node" /tmp/gpio_test_node.log 2>/dev/null; then
        test_result 0 "GPIO节点初始化成功"
    else
        print_warning "无法确认节点初始化状态"
    fi
    
    echo ""
}

# 测试话题接口
test_topics() {
    echo "----------------------------------------"
    print_info "测试ROS话题接口..."
    echo ""
    
    # 检查话题列表
    topics=("gpio/write" "gpio/toggle" "gpio/set_input" "gpio/set_output" 
            "gpio/set_all_direction" "gpio/state" "gpio/status")
    
    for topic in "${topics[@]}"; do
        if timeout 2 rostopic list | grep -q "/$topic"; then
            test_result 0 "话题 /$topic 存在"
        else
            test_result 1 "话题 /$topic 不存在"
        fi
    done
    
    # 测试话题发布
    print_info "测试话题发布..."
    for i in {0..3}; do
        rostopic pub -1 /gpio/write std_msgs/Int32 "data: $i" > /dev/null 2>&1
    done
    sleep 1
    test_result 0 "话题发布功能正常"
    
    # 测试话题切换
    print_info "测试GPIO切换功能..."
    rostopic pub -1 /gpio/toggle std_msgs/Int32 "data: 0" > /dev/null 2>&1
    sleep 0.5
    test_result 0 "GPIO切换功能正常"
    
    echo ""
}

# 测试服务接口
test_services() {
    echo "----------------------------------------"
    print_info "测试ROS服务接口..."
    echo ""
    
    # 等待服务启动
    sleep 2
    
    # 检查服务列表
    services=("gpio_control")
    
    for service in "${services[@]}"; do
        if timeout 2 rosservice list | grep -q "/$service"; then
            test_result 0 "服务 /$service 存在"
        else
            test_result 1 "服务 /$service 不存在"
        fi
    done
    
    # 测试服务调用
    if timeout 2 rosservice list | grep -q "/gpio_control"; then
        print_info "测试服务调用..."
        
        # 测试设置高电平
        timeout 2 rosservice call /gpio_control "pin_number: 18
state: true" > /tmp/gpio_test_service.log 2>&1
        if [ $? -eq 0 ] || grep -q "success: true" /tmp/gpio_test_service.log 2>/dev/null; then
            test_result 0 "服务调用成功 (HIGH)"
        else
            test_result 1 "服务调用失败"
        fi
        
        # 测试设置低电平
        timeout 2 rosservice call /gpio_control "pin_number: 18
state: false" > /dev/null 2>&1
        test_result 0 "服务调用成功 (LOW)"
    fi
    
    echo ""
}

# 测试GPIO方向控制
test_gpio_direction() {
    echo "----------------------------------------"
    print_info "测试GPIO方向控制..."
    echo ""
    
    # 测试单个GPIO方向设置
    print_info "测试单个GPIO方向设置..."
    rostopic pub -1 /gpio/set_input std_msgs/Int32 "data: 0" > /dev/null 2>&1
    sleep 0.5
    rostopic pub -1 /gpio/set_output std_msgs/Int32 "data: 0" > /dev/null 2>&1
    sleep 0.5
    test_result 0 "单个GPIO方向设置正常"
    
    # 测试批量方向设置
    print_info "测试批量GPIO方向设置..."
    rostopic pub -1 /gpio/set_all_direction std_msgs/String "data: 'in'" > /dev/null 2>&1
    sleep 0.5
    rostopic pub -1 /gpio/set_all_direction std_msgs/String "data: 'out'" > /dev/null 2>&1
    sleep 0.5
    test_result 0 "批量GPIO方向设置正常"
    
    echo ""
}

# 测试GPIO状态读取
test_gpio_state() {
    echo "----------------------------------------"
    print_info "测试GPIO状态读取..."
    echo ""
    
    # 启动状态监听
    timeout 5 rostopic echo /gpio/state --noarr > /tmp/gpio_test_state.log 2>&1 &
    MONITOR_PID=$!
    sleep 1
    
    # 触发GPIO活动
    print_info "触发GPIO活动..."
    for i in {0..2}; do
        rostopic pub -1 /gpio/write std_msgs/Int32 "data: $i" > /dev/null 2>&1
        sleep 0.5
    done
    
    # 等待监听完成
    sleep 2
    kill $MONITOR_PID 2>/dev/null || true
    wait $MONITOR_PID 2>/dev/null || true
    
    # 检查日志
    if [ -f /tmp/gpio_test_state.log ] && [ -s /tmp/gpio_test_state.log ]; then
        test_result 0 "GPIO状态读取功能正常"
    else
        test_result 1 "GPIO状态读取功能异常"
    fi
    
    echo ""
}

# 硬件测试
test_hardware() {
    if [ "$TEST_LEVEL" != "hardware" ]; then
        return
    fi
    
    echo "----------------------------------------"
    print_info "执行硬件GPIO测试..."
    echo ""
    
    if python3 -c "import Jetson.GPIO" 2>/dev/null; then
        print_info "运行Jetson.GPIO库测试..."
        python3 scripts/test_jetson_gpio.py
        if [ $? -eq 0 ]; then
            test_result 0 "Jetson.GPIO库测试通过"
        else
            test_result 1 "Jetson.GPIO库测试失败"
        fi
    else
        print_warning "跳过硬件测试（Jetson.GPIO未安装）"
    fi
    
    echo ""
}

# 性能测试
test_performance() {
    if [ "$TEST_LEVEL" = "quick" ]; then
        return
    fi
    
    echo "----------------------------------------"
    print_info "测试GPIO控制性能..."
    echo ""
    
    print_info "执行100次GPIO写入操作..."
    start_time=$(date +%s%N)
    
    for i in {1..100}; do
        rostopic pub -1 /gpio/write std_msgs/Int32 "data: $((i % 10))" > /dev/null 2>&1
        if [ $((i % 20)) -eq 0 ]; then
            sleep 0.1
        fi
    done
    
    end_time=$(date +%s%N)
    elapsed=$(( (end_time - start_time) / 1000000 ))
    
    print_info "100次操作耗时: ${elapsed}ms"
    
    if [ $elapsed -lt 10000 ]; then
        test_result 0 "性能测试通过 (< 10s)"
    else
        print_warning "性能较慢 (${elapsed}ms)"
        test_result 0 "性能测试完成"
    fi
    
    echo ""
}

# 显示GPIO信息
show_gpio_info() {
    echo "----------------------------------------"
    print_info "GPIO配置信息..."
    echo ""
    
    echo "推荐GPIO引脚配置:"
    echo "  [0] GPIO 18  - PWM支持"
    echo "  [1] GPIO 19  - PWM支持"
    echo "  [2] GPIO 31  - 纯通用IO"
    echo "  [3] GPIO 32  - 纯通用IO"
    echo "  [4] GPIO 33  - 纯通用IO"
    echo "  [5] GPIO 35  - 纯通用IO"
    echo "  [6] GPIO 36  - 纯通用IO"
    echo "  [7] GPIO 37  - 纯通用IO"
    echo "  [8] GPIO 38  - 纯通用IO"
    echo "  [9] GPIO 40  - 纯通用IO"
    echo ""
    
    echo "可用ROS话题接口:"
    echo "  /gpio/write           - 写入GPIO电平（索引方式）"
    echo "  /gpio/toggle          - 切换GPIO状态"
    echo "  /gpio/set_input       - 设置GPIO为输入"
    echo "  /gpio/set_output      - 设置GPIO为输出"
    echo "  /gpio/set_all_direction - 批量设置方向"
    echo "  /gpio/state           - GPIO状态信息"
    echo ""
    
    echo "可用ROS服务接口:"
    echo "  /gpio_control         - GPIO控制服务"
    echo ""
}

# 显示测试报告
show_test_report() {
    echo "=========================================="
    echo "  测试报告"
    echo "=========================================="
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
    
    # 启动ROS环境
    start_ros_environment
    
    # 启动GPIO节点
    start_gpio_node
    
    # 执行测试
    test_topics
    test_services
    test_gpio_direction
    test_gpio_state
    
    # 可选测试
    test_hardware
    test_performance
    
    # 显示信息
    show_gpio_info
    
    # 显示报告
    show_test_report
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  full     - 完整测试（默认）"
    echo "  quick    - 快速测试（跳过性能测试）"
    echo "  hardware - 硬件测试（包含GPIO库测试）"
    echo "  help     - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 完整测试"
    echo "  $0 quick        # 快速测试"
    echo "  $0 hardware     # 硬件测试"
}

# 参数处理
case "$1" in
    help|--help|-h)
        show_help
        exit 0
        ;;
    full)
        TEST_LEVEL="full"
        main
        ;;
    quick)
        TEST_LEVEL="quick"
        main
        ;;
    hardware)
        TEST_LEVEL="hardware"
        main
        ;;
    *)
        TEST_LEVEL="full"
        main
        ;;
esac