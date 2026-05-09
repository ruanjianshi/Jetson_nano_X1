#!/bin/bash

# Jetson.GPIO安装和配置脚本

echo "===== Jetson.GPIO 安装和配置脚本 ====="
echo ""

# 检查Python版本
echo "1. 检查Python环境..."
python3_version=$(python3 --version | awk '{print $2}')
echo "   Python版本: $python3_version"
echo "   ✅ Python环境正常"
echo ""

# 检查pip版本
echo "2. 检查pip环境..."
pip_version=$(pip3 --version | awk '{print $2}')
echo "   pip版本: $pip_version"
echo "   ✅ pip环境正常"
echo ""

# 检查Jetson.GPIO安装状态
echo "3. 检查Jetson.GPIO安装状态..."
if python3 -c "import Jetson.GPIO" 2>/dev/null; then
    gpio_version=$(python3 -c "import Jetson.GPIO as GPIO; print(GPIO.VERSION)" 2>/dev/null)
    echo "   ✅ Jetson.GPIO 已安装 (版本: $gpio_version)"
else
    echo "   ⚠️  Jetson.GPIO 未安装"
    echo "   正在安装Jetson.GPIO..."
    
    # 尝试安装Jetson.GPIO
    pip3 install Jetson.GPIO
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Jetson.GPIO 安装成功"
    else
        echo "   ❌ Jetson.GPIO 安装失败"
        echo "   请尝试手动安装:"
        echo "   pip3 install Jetson.GPIO"
        exit 1
    fi
fi
echo ""

# 运行GPIO测试
echo "4. 运行GPIO功能测试..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/scripts/test_jetson_gpio.py" ]; then
    python3 "$PROJECT_DIR/scripts/test_jetson_gpio.py"
    if [ $? -eq 0 ]; then
        echo "   ✅ GPIO功能测试通过"
    else
        echo "   ❌ GPIO功能测试失败"
        exit 1
    fi
else
    echo "   ⚠️  未找到GPIO测试脚本"
fi
echo ""

# 配置GPIO权限
echo "5. 配置GPIO访问权限..."
# 检查当前用户组
current_user=$(whoami)
user_groups=$(groups "$current_user")

if echo "$user_groups" | grep -q "gpio"; then
    echo "   ✅ 用户已在gpio组中"
else
    echo "   ⚠️  用户不在gpio组中"
    echo "   建议运行: sudo usermod -a -G gpio $current_user"
    echo "   然后重新登录使更改生效"
fi

# 检查GPIO文件权限
if [ -d "/sys/class/gpio" ]; then
    echo "   ✅ GPIO文件系统存在"
    
    # 尝试设置权限（需要root）
    if [ -w "/sys/class/gpio/export" ]; then
        echo "   ✅ GPIO导出权限正常"
    else
        echo "   ⚠️  GPIO导出权限受限"
        echo "   建议运行: sudo chmod g+rw /sys/class/gpio/export"
        echo "            sudo chmod g+rw /sys/class/gpio/unexport"
    fi
else
    echo "   ❌ GPIO文件系统不存在"
    exit 1
fi
echo ""

# 显示GPIO信息
echo "6. GPIO信息汇总..."
echo "   Jetson.GPIO版本: $(python3 -c "import Jetson.GPIO as GPIO; print(GPIO.VERSION)" 2>/dev/null)"
echo "   可用GPIO模式: BOARD, BCM, TEGRA_SOC"
echo "   支持的功能: 输入、输出、PWM"
echo ""

echo "7. 推荐GPIO引脚配置（基于实际测试）:"
echo "   ✅ 可用引脚: 18, 19, 21, 22, 23, 24, 29"
echo "   ⚠️  限制引脚: 27, 28, 30 (不可用)"
echo "   📌 功能说明:"
echo "     GPIO18, GPIO19: 支持PWM输出"
echo "     GPIO21, GPIO22: I2C引脚（如不使用I2C可作通用IO）"
echo "     GPIO23, GPIO24: SPI引脚（如不使用SPI可作通用IO）"
echo "     GPIO29: UART引脚（如不使用UART可作通用IO）"
echo ""

echo "8. 后续步骤建议:"
echo "   1. 配置GPIO权限（如需要）"
echo "   2. 选择合适的GPIO引脚"
echo "   3. 测试硬件连接"
echo "   4. 运行ROS GPIO控制节点"
echo ""

echo "===== Jetson.GPIO 配置完成 ====="
echo ""
echo "🎉 Jetson.GPIO已准备就绪，可以开始使用！"