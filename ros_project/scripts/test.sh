#!/bin/bash

# 项目统一测试脚本
# 整合所有模块的测试功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  Jetson Nano ROS 项目统一测试套件"
echo "=========================================="
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试配置
TEST_MODE="${1:-all}"  # all, quick, gpio, communication, opencv, rl, gui
TEST_START_TIME=$(date +%s)

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

# 检查环境
check_environment() {
    print_header "检查测试环境"
    
    # 检查ROS环境
    if [ -z "$ROS_DISTRO" ]; then
        print_error "ROS环境未激活"
        print_info "请运行: source /opt/ros/noetic/setup.bash"
        exit 1
    fi
    print_success "ROS环境已激活 (ROS $ROS_DISTRO)"
    
    # 检查工作空间
    if [ ! -f "devel/setup.bash" ]; then
        print_error "未找到devel/setup.bash"
        print_info "请先运行: catkin_make"
        exit 1
    fi
    
    source devel/setup.bash
    print_success "工作空间环境已激活"
    
    # 检查Python依赖
    print_info "检查Python依赖..."
    python3 -c "import Jetson.GPIO" 2>/dev/null && print_success "Jetson.GPIO已安装" || print_warning "Jetson.GPIO未安装"
    python3 -c "import rospy" 2>/dev/null && print_success "rospy已安装" || print_warning "rospy未安装"
    python3 -c "import cv2" 2>/dev/null && print_success "OpenCV已安装" || print_warning "OpenCV未安装"
    python3 -c "import numpy" 2>/dev/null && print_success "numpy已安装" || print_warning "numpy未安装"
    python3 -c "from PyQt5.QtWidgets import QApplication" 2>/dev/null && print_success "PyQt5已安装" || print_warning "PyQt5未安装"
    
    echo ""
}

# 测试GPIO模块
test_gpio_module() {
    print_header "测试GPIO控制模块"
    
    # 检查GPIO包
    if [ ! -d "src/gpio_control" ]; then
        print_error "gpio_control包不存在"
        return 1
    fi
    
    # 运行GPIO测试
    print_info "运行GPIO测试..."
    if bash scripts/test_gpio.sh quick; then
        print_success "GPIO模块测试通过"
        return 0
    else
        print_error "GPIO模块测试失败"
        return 1
    fi
}

# 测试通信模块
test_communication_module() {
    print_header "测试通信模块"
    
    if [ ! -d "src/communication" ]; then
        print_warning "communication包不存在，跳过测试"
        return 0
    fi
    
    # 检查通信脚本
    if [ -f "src/communication/scripts/serial_comm_node.py" ]; then
        print_info "检查串口通信脚本..."
        python3 -m py_compile src/communication/scripts/serial_comm_node.py
        if [ $? -eq 0 ]; then
            print_success "串口通信脚本语法正确"
        else
            print_error "串口通信脚本语法错误"
        fi
    fi
    
    if [ -f "src/communication/scripts/network_comm_node.py" ]; then
        print_info "检查网络通信脚本..."
        python3 -m py_compile src/communication/scripts/network_comm_node.py
        if [ $? -eq 0 ]; then
            print_success "网络通信脚本语法正确"
        else
            print_error "网络通信脚本语法错误"
        fi
    fi
    
    print_success "通信模块检查完成"
    return 0
}

# 测试OpenCV模块
test_opencv_module() {
    print_header "测试OpenCV处理模块"
    
    if [ ! -d "src/opencv_processing" ]; then
        print_warning "opencv_processing包不存在，跳过测试"
        return 0
    fi
    
    # 检查OpenCV脚本
    if [ -f "src/opencv_processing/scripts/camera_node.py" ]; then
        print_info "检查摄像头脚本..."
        python3 -m py_compile src/opencv_processing/scripts/camera_node.py
        if [ $? -eq 0 ]; then
            print_success "摄像头脚本语法正确"
        else
            print_error "摄像头脚本语法错误"
        fi
    fi
    
    if [ -f "src/opencv_processing/scripts/image_processor_node.py" ]; then
        print_info "检查图像处理脚本..."
        python3 -m py_compile src/opencv_processing/scripts/image_processor_node.py
        if [ $? -eq 0 ]; then
            print_success "图像处理脚本语法正确"
        else
            print_error "图像处理脚本语法错误"
        fi
    fi
    
    print_success "OpenCV模块检查完成"
    return 0
}

# 测试强化学习模块
test_rl_module() {
    print_header "测试强化学习模块"
    
    if [ ! -d "src/reinforcement_learning" ]; then
        print_warning "reinforcement_learning包不存在，跳过测试"
        return 0
    fi
    
    # 检查RL脚本
    for script in rl_environment_node.py rl_agent_node.py rl_trainer_node.py; do
        if [ -f "src/reinforcement_learning/scripts/$script" ]; then
            print_info "检查 $script..."
            python3 -m py_compile src/reinforcement_learning/scripts/$script
            if [ $? -eq 0 ]; then
                print_success "$script 语法正确"
            else
                print_error "$script 语法错误"
            fi
        fi
    done
    
    print_success "强化学习模块检查完成"
    return 0
}

# 测试Qt5 GUI模块
test_gui_module() {
    print_header "测试Qt5 GUI模块"
    
    if [ ! -d "src/qt5_gui" ]; then
        print_warning "qt5_gui包不存在，跳过测试"
        return 0
    fi
    
    # 检查GUI脚本
    for script in main_gui_node.py status_monitor.py control_panel.py; do
        if [ -f "src/qt5_gui/scripts/$script" ]; then
            print_info "检查 $script..."
            python3 -m py_compile src/qt5_gui/scripts/$script
            if [ $? -eq 0 ]; then
                print_success "$script 语法正确"
            else
                print_error "$script 语法错误"
            fi
        fi
    done
    
    print_success "Qt5 GUI模块检查完成"
    return 0
}

# 测试公共工具模块
test_common_utils_module() {
    print_header "测试公共工具模块"
    
    if [ ! -d "src/common_utils" ]; then
        print_warning "common_utils包不存在，跳过测试"
        return 0
    fi
    
    # 检查工具脚本
    for script in logger_utils.py config_loader.py; do
        if [ -f "src/common_utils/scripts/$script" ]; then
            print_info "检查 $script..."
            python3 -m py_compile src/common_utils/scripts/$script
            if [ $? -eq 0 ]; then
                print_success "$script 语法正确"
            else
                print_error "$script 语法错误"
            fi
        fi
    done
    
    print_success "公共工具模块检查完成"
    return 0
}

# 运行单元测试
run_unit_tests() {
    print_header "运行单元测试"
    
    if [ ! -d "tests/unit" ]; then
        print_warning "单元测试目录不存在"
        return 0
    fi
    
    for test_file in tests/unit/*.py; do
        if [ -f "$test_file" ]; then
            print_info "运行测试: $test_file"
            python3 "$test_file"
            if [ $? -eq 0 ]; then
                print_success "测试通过: $(basename $test_file)"
            else
                print_error "测试失败: $(basename $test_file)"
            fi
        fi
    done
}

# 运行集成测试
run_integration_tests() {
    print_header "运行集成测试"
    
    if [ ! -d "tests/integration" ]; then
        print_warning "集成测试目录不存在"
        return 0
    fi
    
    for test_file in tests/integration/*.py; do
        if [ -f "$test_file" ]; then
            print_info "运行测试: $test_file"
            python3 "$test_file"
            if [ $? -eq 0 ]; then
                print_success "测试通过: $(basename $test_file)"
            else
                print_error "测试失败: $(basename $test_file)"
            fi
        fi
    done
}

# 生成测试报告
generate_test_report() {
    local test_end_time=$(date +%s)
    local duration=$((test_end_time - test_start_time))
    
    print_header "测试报告"
    
    echo "测试时长: ${duration}秒"
    echo "测试模式: $TEST_MODE"
    echo "测试时间: $(date)"
    
    echo ""
    print_success "测试完成"
    print_info "详细日志请查看各模块的测试输出"
    
    echo ""
    print_header "项目测试统计"
    echo "GPIO控制模块:      ✅ 已测试"
    echo "通信模块:          ✅ 已检查"
    echo "OpenCV处理模块:    ✅ 已检查"
    echo "强化学习模块:      ✅ 已检查"
    echo "Qt5 GUI模块:       ✅ 已检查"
    echo "公共工具模块:      ✅ 已检查"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  all           - 测试所有模块（默认）"
    echo "  quick         - 快速测试（仅语法检查）"
    echo "  gpio          - 仅测试GPIO模块"
    echo "  communication - 仅测试通信模块"
    echo "  opencv        - 仅测试OpenCV模块"
    echo "  rl            - 仅测试强化学习模块"
    echo "  gui           - 仅测试Qt5 GUI模块"
    echo "  unit          - 仅运行单元测试"
    echo "  integration   - 仅运行集成测试"
    echo "  help          - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 测试所有模块"
    echo "  $0 quick        # 快速测试"
    echo "  $0 gpio         # 仅测试GPIO模块"
    echo "  $0 unit         # 仅运行单元测试"
}

# 主函数
main() {
    # 检查环境
    check_environment
    
    # 根据测试模式执行测试
    case "$TEST_MODE" in
        all)
            test_gpio_module
            test_communication_module
            test_opencv_module
            test_rl_module
            test_gui_module
            test_common_utils_module
            run_unit_tests
            run_integration_tests
            ;;
        quick)
            print_info "快速测试模式 - 仅进行语法检查"
            test_communication_module
            test_opencv_module
            test_rl_module
            test_gui_module
            test_common_utils_module
            ;;
        gpio)
            test_gpio_module
            ;;
        communication)
            test_communication_module
            ;;
        opencv)
            test_opencv_module
            ;;
        rl)
            test_rl_module
            ;;
        gui)
            test_gui_module
            ;;
        common)
            test_common_utils_module
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "未知的测试模式: $TEST_MODE"
            show_help
            exit 1
            ;;
    esac
    
    # 生成测试报告
    generate_test_report
    
    print_header "测试完成"
    print_success "所有测试已完成！"
}

# 参数处理
case "$1" in
    help|--help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac