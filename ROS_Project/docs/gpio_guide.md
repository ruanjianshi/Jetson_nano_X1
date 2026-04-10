# GPIO使用指南

## 概述

Jetson Nano B01提供40引脚GPIO接口，本指南详细介绍GPIO引脚分布、功能和使用方法。

## GPIO引脚分布

### 40引脚完整分布

| Pin | 名称        | 类型      | 功能             | BCM  | 推荐用途         |
|-----|-------------|-----------|------------------|------|------------------|
| 1   | 3.3V        | Power     | 3.3V电源         | -    | 电源             |
| 2   | 5V          | Power     | 5V电源           | -    | 电源             |
| 3   | GPIO2       | GPIO      | I2C_SDA_1        | 2    | I2C/通用         |
| 4   | 5V          | Power     | 5V电源           | -    | 电源             |
| 5   | GPIO3       | GPIO      | I2C_SCL_1        | 3    | I2C/通用         |
| 6   | GND         | Ground    | 地线             | -    | 地线             |
| 7   | GPIO4       | GPIO      | GPIO_GPCLK0      | 4    | 通用             |
| 8   | GPIO14      | GPIO      | UART_TXD0        | 14   | UART/通用        |
| 9   | GND         | Ground    | 地线             | -    | 地线             |
| 10  | GPIO15      | GPIO      | UART_RXD0        | 15   | UART/通用        |
| 11  | GPIO17      | GPIO      | GPIO_GEN0        | 17   | 通用             |
| 12  | GPIO18      | GPIO      | GPIO_GEN1/PWM0   | 18   | PWM/通用 ⭐       |
| 13  | GPIO27      | GPIO      | GPIO_GEN2        | 27   | 通用             |
| 14  | GND         | Ground    | 地线             | -    | 地线             |
| 15  | GPIO22      | GPIO      | GPIO_GEN3        | 22   | 通用             |
| 16  | GPIO23      | GPIO      | GPIO_GEN4        | 23   | 通用             |
| 17  | 3.3V        | Power     | 3.3V电源         | -    | 电源             |
| 18  | GPIO24      | GPIO      | GPIO_GEN5        | 24   | 通用             |
| 19  | GPIO10      | GPIO      | SPI_MOSI         | 10   | SPI/通用         |
| 20  | GND         | Ground    | 地线             | -    | 地线             |
| 21  | GPIO9       | GPIO      | SPI_MISO         | 9    | SPI/通用         |
| 22  | GPIO25      | GPIO      | GPIO_GEN6        | 25   | 通用             |
| 23  | GPIO11      | GPIO      | SPI_SCLK         | 11   | SPI/通用         |
| 24  | GPIO8       | GPIO      | SPI_CE0_N        | 8    | SPI/通用         |
| 25  | GND         | Ground    | 地线             | -    | 地线             |
| 26  | GPIO7       | GPIO      | SPI_CE1_N        | 7    | SPI/通用         |
| 27  | ID_SD       | EEPROM    | ID_SD(EEPROM)    | 0    | EEPROM           |
| 28  | ID_SC       | EEPROM    | ID_SC(EEPROM)    | 1    | EEPROM           |
| 29  | GPIO5       | GPIO      | GPIO_GEN7        | 5    | 通用             |
| 30  | GND         | Ground    | 地线             | -    | 地线             |
| 31  | GPIO6       | GPIO      | GPIO_GEN8        | 6    | 通用 ⭐           |
| 32  | GPIO12      | GPIO      | GPIO_GEN9/PWM0   | 12   | PWM/通用 ⭐       |
| 33  | GPIO13      | GPIO      | GPIO_GEN10/PWM1  | 13   | PWM/通用 ⭐       |
| 34  | GND         | Ground    | 地线             | -    | 地线             |
| 35  | GPIO19      | GPIO      | GPIO_GEN11/PWM1  | 19   | PWM/通用 ⭐       |
| 36  | GPIO16      | GPIO      | GPIO_GEN12       | 16   | 通用             |
| 37  | GPIO26      | GPIO      | GPIO_GEN13       | 26   | 通用             |
| 38  | GPIO20      | GPIO      | GPIO_GEN14       | 20   | 通用             |
| 39  | GND         | Ground    | 地线             | -    | 地线             |
| 40  | GPIO21      | GPIO      | GPIO_GEN15       | 21   | 通用             |

⭐ = 推荐引脚

### GPIO功能分类

#### 电源和地线 (不可用于GPIO)
- **3.3V**: 引脚 1, 17
- **5V**: 引脚 2, 4
- **GND**: 引脚 6, 9, 14, 20, 25, 30, 34, 39

#### 特殊功能引脚
- **I2C**: GPIO2, GPIO3 (引脚 3, 5)
- **UART**: GPIO14, GPIO15 (引脚 8, 10)
- **SPI**: GPIO7, 8, 9, 10, 11 (引脚 19, 21, 23, 24, 26)

#### 通用GPIO引脚推荐
**优先级1：纯通用IO（推荐）**
- 31, 32, 33, 35, 36, 37, 38, 40

**优先级2：支持PWM的通用IO**
- 12, 18, 19, 21, 32, 33, 35

**优先级3：条件性通用IO**
- 7, 8, 9, 10, 11 (不使用SPI时)
- 14, 15 (不使用UART时)
- 2, 3 (不使用I2C时)

## 推荐配置

### 基础配置（8个纯通用IO）
```python
recommended_gpio_pins = [31, 32, 33, 35, 36, 37, 38, 40]
```

### 扩展配置（10个通用IO，包含PWM支持）
```python
extended_gpio_pins = [18, 19, 31, 32, 33, 35, 36, 37, 38, 40]
```

### 完整配置（所有可用GPIO）
```python
full_gpio_pins = [7, 8, 9, 10, 11, 14, 15, 18, 19, 31, 32, 33, 35, 36, 37, 38, 40]
```

## 使用方法

### 1. 环境设置

#### 安装Jetson.GPIO
```bash
sudo apt update
sudo apt install python3-libgpiod
pip3 install Jetson.GPIO
```

#### 设置GPIO权限
```bash
sudo usermod -a -G gpio jetson
sudo chmod g+rw /sys/class/gpio/export
sudo chmod g+rw /sys/class/gpio/unexport
```

### 2. 启动GPIO控制节点

#### 激活ROS环境
```bash
cd /home/jetson/Desktop/Jetson_Nano/ROS_Project
source devel/setup.bash
```

#### 启动节点
```bash
# 使用推荐配置
roslaunch gpio_control universal_gpio.launch

# 使用自定义配置
roslaunch gpio_control universal_gpio.launch gpio_pins:="[18, 19, 31, 32, 33, 35, 36, 37, 38, 40]"
```

### 3. GPIO控制

#### 通过话题控制
```bash
# 写入GPIO（高电平脉冲）
rostopic pub /gpio/write std_msgs/Int32 "data: 0"

# 切换GPIO状态
rostopic pub /gpio/toggle std_msgs/Int32 "data: 0"

# 设置GPIO为输入
rostopic pub /gpio/set_input std_msgs/Int32 "data: 0"

# 设置GPIO为输出
rostopic pub /gpio/set_output std_msgs/Int32 "data: 0"

# 批量设置方向
rostopic pub /gpio/set_all_direction std_msgs/String "data: 'in'"
rostopic pub /gpio/set_all_direction std_msgs/String "data: 'out'"
```

#### 通过服务控制
```bash
# 设置GPIO为高电平
rosservice call /gpio_control "pin_number: 18
state: true"

# 设置GPIO为低电平
rosservice call /gpio_control "pin_number: 18
state: false"
```

#### 读取GPIO状态
```bash
# 监听GPIO状态
rostopic echo /gpio/state
```

### 4. GPIO信息查询

#### 查询40引脚分布
```bash
python3 src/gpio_control/scripts/gpio_info_query.py
```

#### 查看特定引脚信息
```bash
# 在交互界面选择选项5，输入引脚编号
python3 src/gpio_control/scripts/gpio_info_query.py
# 选择: 5
# 输入: 18, 19, 31
```

## 引脚对照表

| 索引 | GPIO引脚 | 功能     | 推荐用途     |
|------|----------|----------|--------------|
| 0    | 18       | PWM/IO   | LED控制 ⭐   |
| 1    | 19       | PWM/IO   | LED控制 ⭐   |
| 2    | 31       | 纯IO     | 数字输出 ⭐   |
| 3    | 32       | PWM/IO   | 传感器控制 ⭐ |
| 4    | 33       | PWM/IO   | 传感器控制 ⭐ |
| 5    | 35       | PWM/IO   | 数字输出 ⭐   |
| 6    | 36       | 纯IO     | 数字输出 ⭐   |
| 7    | 37       | 纯IO     | 数字输出 ⭐   |
| 8    | 38       | 纯IO     | 数字输出 ⭐   |
| 9    | 40       | 纯IO     | 数字输出 ⭐   |

⭐ = 推荐使用

## 硬件连接建议

### 输出引脚连接
- **LED**: 串联220Ω-1kΩ电阻到GND
- **继电器**: 使用驱动电路（如ULN2003）
- **电机**: 使用H桥驱动器（如L298N）
- **蜂鸣器**: 串联100Ω电阻和三极管

### 输入引脚连接
- **传感器**: 使用上拉/下拉电阻
- **按钮**: 配置内部上拉/下拉电阻
- **开关**: 使用上拉/下拉电阻

### 安全注意事项
1. 避免GPIO引脚短路
2. 注意电流限制（每个引脚约2-16mA）
3. 高电流设备使用驱动电路
4. 噪声敏感使用光耦隔离
5. 3.3V逻辑电平，注意电平转换

## 使用示例

### LED闪烁控制
```bash
# 启动节点
roslaunch gpio_control universal_gpio.launch

# 在另一个终端
source devel/setup.bash

# 快速闪烁LED (GPIO18)
for i in {1..10}; do
  rostopic pub -1 /gpio/write std_msgs/Int32 "data: 0"
  sleep 0.2
done
```

### 传感器读取
```bash
# 设置GPIO35为输入模式
rostopic pub -1 /gpio/set_input std_msgs/Int32 "data: 5"

# 监听状态
rostopic echo /gpio/state
```

### 批量设备控制
```bash
# 控制多个GPIO
for pin_index in 0 1 2 3; do
  rostopic pub -1 /gpio/write std_msgs/Int32 "data: $pin_index"
  sleep 0.1
done
```

## ROS话题接口

| 话题              | 功能           | 参数          | 示例                |
|-------------------|----------------|---------------|---------------------|
| /gpio/write       | 写入GPIO电平   | 索引          | data: 0 (控制GPIO18) |
| /gpio/toggle      | 切换GPIO状态   | 索引          | data: 4 (切换GPIO33) |
| /gpio/set_input   | 设置GPIO为输入 | 索引          | data: 5 (设置GPIO35) |
| /gpio/set_output  | 设置GPIO为输出 | 索引          | data: 6 (设置GPIO36) |
| /gpio/set_direction | 设置GPIO方向 | 0=input, 1=output | data: 1        |
| /gpio/set_all_direction | 批量设置方向 | 'in' 或 'out' | data: 'in'     |
| /gpio/state       | GPIO状态信息   | -             | 实时状态值          |

## 故障排除

### 权限问题
```bash
# 添加用户到gpio组
sudo usermod -a -G gpio jetson

# 设置GPIO访问权限
sudo chmod g+rw /sys/class/gpio/export
sudo chmod g+rw /sys/class/gpio/unexport
```

### GPIO初始化失败
1. 检查GPIO引脚是否被其他程序占用
2. 确认引脚编号正确
3. 检查系统权限
4. 查看错误日志

### ROS连接问题
1. 确保ROS环境已正确设置
2. 检查rosmaster是否运行
3. 确认网络连接正常

### 读取错误
某些GPIO引脚在当前硬件上可能存在兼容性问题，建议使用推荐的纯通用IO引脚。

## 性能优化

- 使用批量操作减少通信开销
- 适当设置读取频率
- 优化GPIO初始化过程
- 使用硬件PWM替代软件PWM

## 扩展功能

- PWM输出控制
- 中断处理
- 边沿检测
- GPIO组管理
- 状态机控制

## 测试验证

### 运行测试脚本
```bash
# GPIO基础测试
./scripts/test_gpio.sh

# GPIO简单测试
./scripts/test_gpio_simple.sh

# GPIO高级测试
./scripts/test_gpio_advanced.sh

# Jetson GPIO测试
python3 scripts/test_jetson_gpio.py
```

### 查询GPIO信息
```bash
python3 src/gpio_control/scripts/gpio_info_query.py
```

## 重要注意事项

1. **环境激活**: 每次使用前必须激活ROS环境
2. **节点启动**: 必须先启动GPIO控制节点
3. **索引控制**: 使用索引而非直接GPIO编号
4. **硬件安全**: 避免GPIO短路，注意电流限制
5. **引脚限制**: 只使用验证可用的引脚

## 参考资源

- [Jetson.GPIO文档](https://github.com/NVIDIA/jetson-gpio)
- [ROS Noetic文档](http://wiki.ros.org/noetic)
- [Jetson Nano技术参考手册](https://developer.nvidia.com/embedded/jetson-nano)