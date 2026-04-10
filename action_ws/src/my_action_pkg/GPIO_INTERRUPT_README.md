# GPIO 中断 Action 实现说明文档

## 📋 项目概述

基于 ROS Action 和 Jetson.GPIO 库实现通用 GPIO 中断检测功能，支持上升沿、下降沿、双边沿检测，并通过 ROS Action 框架实时发送中断事件反馈。

## 🏗️ 文件结构

```
my_action_pkg/
├── action/
│   └── GPIOInterrupt.action      # GPIO 中断 Action 定义
├── scripts/
│   ├── gpio_interrupt_server.py  # GPIO 中断服务器
│   └── gpio_interrupt_client.py  # GPIO 中断客户端
└── launch/
    └── gpio_interrupt.launch     # 启动文件
```

## 📦 Action 定义

### Goal - 发送目标
```yaml
uint8 pin_number           # GPIO 引脚号 (BCM 编号)
uint8 edge_mode            # 边沿模式: 0=上升沿, 1=下降沿, 2=双边沿
uint8 debounce_ms          # 去抖动时间 (毫秒)
```

### Result - 返回结果
```yaml
bool success               # 操作是否成功
uint32 interrupt_count     # 检测到的中断次数
```

### Feedback - 进度反馈
```yaml
std_msgs/String event_type    # 事件类型: "rising", "falling"
uint64 timestamp              # 中断时间戳 (纳秒)
```

## 🔌 硬件连接

### Jetson Nano GPIO 引脚图

#### 常用 GPIO 引脚 (BCM 编号)

| 物理引脚 | BCM 编号 | 功能 | 说明 |
|---------|---------|------|------|
| 12 | 18 | GPIO 18 | PWM 输出，支持中断 |
| 13 | 27 | GPIO 27 | 通用 GPIO，支持中断 |
| 15 | 22 | GPIO 22 | 通用 GPIO，支持中断 |
| 16 | 23 | GPIO 23 | 通用 GPIO，支持中断 |
| 18 | 24 | GPIO 24 | 通用 GPIO，支持中断 |
| 29 | 5  | GPIO 5  | 通用 GPIO，支持中断 |
| 31 | 6  | GPIO 6  | 通用 GPIO，支持中断 |
| 32 | 12 | GPIO 12 | PWM 输出，支持中断 |
| 33 | 13 | GPIO 13 | PWM 输出，支持中断 |
| 35 | 19 | GPIO 19 | 通用 GPIO，支持中断 |
| 36 | 16 | GPIO 16 | 通用 GPIO，支持中断 |
| 37 | 26 | GPIO 26 | 通用 GPIO，支持中断 |
| 38 | 20 | GPIO 20 | 通用 GPIO，支持中断 |
| 40 | 21 | GPIO 21 | 通用 GPIO，支持中断 |

#### 电源引脚

| 物理引脚 | 功能 | 电压 |
|---------|------|------|
| 1, 17 | 3.3V 电源 | 3.3V |
| 2, 4 | 5V 电源 | 5.0V |
| 6, 9, 14, 20, 25, 30, 34, 39 | GND | 0V |

### GPIO 编号模式

**两种编号方式：**

1. **BCM 编号（推荐）**: 使用 Broadcom SOC 通道编号
   - 例如: GPIO 18 对应 BCM 18
   - 本项目使用此模式

2. **BOARD 编号**: 使用物理引脚编号
   - 例如: 引脚 12 对应 BOARD 12
   - 需要转换计算

### 硬件连接示例

#### 示例 1: 按钮中断检测

```
连接图:

GPIO 18 (BCM) ──┬── 10kΩ 上拉电阻 ─── 3.3V (Pin 1 或 17)
                 │
                按钮
                 │
                GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
```

**工作原理:**
- 按钮未按下时，GPIO 18 通过上拉电阻连接到 3.3V，状态为 HIGH
- 按钮按下时，GPIO 18 连接到 GND，状态变为 LOW
- 从 HIGH 到 LOW 的变化触发**下降沿中断**

#### 示例 2: 外部信号中断检测

```
连接图:

外部信号源 ──┬── GPIO 18 (BCM)
             │
          1kΩ 电阻
             │
            GND
```

**工作原理:**
- 外部信号可以是传感器、定时器等
- 信号跳变时触发中断
- 需要确保信号电平在 0V-3.3V 范围内

#### 示例 3: 光耦隔离（推荐）

```
连接图:

外部设备 ──┬─ 光耦输入端
           │
         光耦 PC817
           │
GPIO 18 ───┬─ 光耦输出端
           │
           └── 上拉电阻 ─── 3.3V
```

**优点:**
- 电气隔离，保护 Jetson Nano
- 抗干扰能力强
- 适用于工业环境

## 🚀 使用方法

### 1. 安装依赖

```bash
# Jetson.GPIO 已预装，检查版本
python3 -c "import Jetson.GPIO as GPIO; print('GPIO 版本:', GPIO.VERSION)"

# 如果未安装
pip3 install Jetson.GPIO
```

### 2. 启动 Server (需要 sudo 权限)

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash
sudo roslaunch my_action_pkg gpio_interrupt.launch
```

### 3. 检测 GPIO 中断 (Client)

打开新终端：

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash

# 使用 python3 直接运行（推荐）
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=2 \
    _debounce_ms:=50 \
    _duration:=30
```

## ⚙️ 参数配置

### Server 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 无 | 无 | Server 无需配置参数 |

### Client 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `_pin_number` | `18` | GPIO 引脚号 (BCM 编号) |
| `_edge_mode` | `2` | 边沿模式 (0=上升, 1=下降, 2=双边) |
| `_debounce_ms` | `50` | 去抖动时间 (毫秒) |
| `_duration` | `30` | 监听时长 (秒) |

### 边沿模式说明

| 值 | 常量 | 名称 | 触发条件 |
|----|------|------|---------|
| 0 | RISING | 上升沿 | 从 LOW 变为 HIGH |
| 1 | FALLING | 下降沿 | 从 HIGH 变为 LOW |
| 2 | BOTH | 双边沿 | 上升和下降都触发 |

## 📊 工作流程

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │────────▶│   Server    │────────▶│   GPIO      │
│             │  Goal   │             │  Config │  (BCM 18)   │
│             │         │             │         │             │
│   Client    │◀────────│   Server    │◀────────│   GPIO      │
│             │  Result │             │  Stats  │  Interrupt  │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ▼
                      Feedback (实时中断事件)
```

### 详细流程

1. **Client 发送 Goal**
   - 指定 GPIO 引脚、边沿模式、去抖动时间
   - Server 开始配置 GPIO

2. **Server 配置 GPIO**
   - 设置 GPIO 为输入模式
   - 配置上拉/下拉电阻
   - 注册中断回调函数

3. **检测中断事件**
   - GPIO 状态发生变化时触发
   - 调用回调函数
   - 发送 Feedback 给 Client

4. **Client 接收 Feedback**
   - 实时显示中断事件
   - 记录时间戳和事件类型

5. **返回 Result**
   - 统计总中断次数
   - 返回操作状态

## 🔍 测试示例

### 示例 1: 基本测试（按钮）

```bash
# 硬件准备: GPIO 18 连接按钮到 GND

# 启动 Server
sudo roslaunch my_action_pkg gpio_interrupt.launch

# 检测下降沿中断（按钮按下）
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=1 \
    _duration:=30
```

**预期输出:**
```
📤 发送 Goal:
   GPIO 引脚: 18 (BCM 编号)
   边沿模式: 下降沿
   去抖动时间: 50 ms
   监听时长: 30 秒

============================================================
🔔 开始监听 GPIO 中断事件...
============================================================

🔔 中断 #1: 下降沿 at 2026-03-31 14:30:15.123
🔔 中断 #2: 下降沿 at 2026-03-31 14:30:18.456
...

============================================================
✅ GPIO 中断监听完成！
   GPIO 引脚: 18
   边沿模式: 下降沿
   总中断次数: 5
============================================================
```

### 示例 2: 上升沿检测

```bash
# 硬件准备: GPIO 18 通过下拉电阻连接到 GND，按钮连接到 3.3V

# 检测上升沿中断（按钮按下）
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=0
```

### 示例 3: 双边沿检测

```bash
# 同时检测上升和下降沿
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=2
```

**预期输出:**
```
🔔 中断 #1: 上升沿 at 2026-03-31 14:30:15.123
🔔 中断 #2: 下降沿 at 2026-03-31 14:30:15.456
```

### 示例 4: 调整去抖动时间

```bash
# 增加去抖动时间到 200ms（适用于机械按钮）
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=1 \
    _debounce_ms:=200
```

### 示例 5: 长时间监听

```bash
# 监听 60 秒
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
    _pin_number:=18 \
    _duration:=60
```

## 🔍 GPIO 中断原理

### 什么是 GPIO 中断？

GPIO 中断是一种硬件机制，当 GPIO 引脚的电平发生变化时，CPU 自动跳转到预定义的中断服务程序（ISR）执行特定任务。

### 为什么使用中断？

**轮询 vs 中断:**

| 特性 | 轮询 | 中断 |
|------|------|------|
| CPU 使用率 | 高（持续检测） | 低（仅在事件发生时） |
| 响应速度 | 取决于轮询频率 | 即时（微秒级） |
| 实时性 | 差 | 优秀 |
| 功耗 | 高 | 低 |

### 中断检测机制

```
时间线:

t0: GPIO 状态 = HIGH
t1: GPIO 状态 = LOW  (触发中断)
    └──> ISR 执行 ──┐
t2: GPIO 状态 = LOW  │
t3: GPIO 状态 = HIGH (如果双边沿，再次触发中断)
                    │
                    v
              发送 Feedback
```

### 去抖动原理

机械按钮在按下/释放时会产生多次抖动：

```
实际信号:

HIGH ─────┐     ┌────┐     ┌─────
        └─────┘     └─────┘
        ^^^ 抖动信号 ^^^

去抖动后:

HIGH ─────┐──────────────────────
        └─────┘
        稳定信号
```

**去抖动时间:**
- 软件去抖动: 在程序中忽略短时间内的多次中断
- 硬件去抖动: 使用 RC 电路或施密特触发器

### 上拉/下拉电阻

**上拉电阻:**
- GPIO 默认状态为 HIGH
- 外部连接到 GND 时触发
- 适用于按钮接地检测

**下拉电阻:**
- GPIO 默认状态为 LOW
- 外部连接到 3.3V 时触发
- 适用于按钮接电源检测

## 🐛 故障排除

### 1. 权限错误

**问题**: `RuntimeError: No access to /dev/mem. Try running as root!`

**解决方法**: 使用 sudo 运行 Server
```bash
sudo roslaunch my_action_pkg gpio_interrupt.launch
```

### 2. GPIO 编号错误

**问题**: `RuntimeError: The channel sent is invalid`

**解决方法**: 
- 检查 GPIO 编号是否正确
- 确认使用 BCM 编号（推荐）
- 查看引脚图确认引脚功能

### 3. 无中断响应

**问题**: 按钮按下但没有中断

**可能原因:**
- 边沿模式设置错误
- 按钮电路连接问题
- 去抖动时间过长

**解决方法:**
```bash
# 检查 GPIO 状态
python3 -c "
import Jetson.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print('GPIO 18 状态:', 'HIGH' if GPIO.input(18) else 'LOW')
GPIO.cleanup()
"

# 尝试双边沿模式
_edge_mode:=2

# 减少去抖动时间
_debounce_ms:=10
```

### 4. 频繁中断

**问题**: 一次触发多个中断

**解决方法:**
- 增加去抖动时间
- 使用硬件去抖动电路
- 检查信号质量

### 5. 未找到 Jetson.GPIO

**问题**: `ModuleNotFoundError: No module named 'Jetson.GPIO'`

**解决方法:**
```bash
pip3 install Jetson.GPIO
# 或
sudo apt install python3-gpio
```

## 📚 GPIO 引脚完整列表

### Jetson Nano 40-pin GPIO Header

```
            ┌─────────────────┐
  3.3V (1) │ ② ① │ (40) GND
  5V  (2) │ ④ ③ │ (39) GND
 GPIO 2 (3) │ ⑥ ⑤ │ (38) GPIO 21
  5V  (4) │ ⑧ ⑦ │ (37) GPIO 26
 GPIO 3 (5) │ ⑩ ⑨ │ (36) GPIO 16
 GND  (6) │ ⑫ ⑪ │ (35) GPIO 19
 GPIO 4 (7) │ ⑭ ⑬ │ (34) GND
 GPIO14 (8) │ ⑯ ⑮ │ (33) GPIO 13
 GND  (9) │ ⑱ ⑰ │ (32) GPIO 12
 GPIO15(10) │ ⑳ ⑲ │ (31) GPIO 6
 GPIO17(11) │ ⑮ ⑴ │ (30) GND
 GPIO18(12) │ ⑳ ⑳ │ (29) GPIO 5
 GPIO27(13) │ ⑮ ⑴ │ (28) GPIO 4
 GND  (14) │ ⑳ ⑲ │ (27) ID_SD
 GPIO23(15) │ ⑭ ⑬ │ (26) ID_SC
  3.3V(16) │ ⑩ ⑨ │ (25) GND
 GPIO24(17) │ ⑧ ⑦ │ (24) GPIO 8
 GPIO10(18) │ ⑥ ⑤ │ (23) GPIO 11
 GND  (19) │ ④ ③ │ (22) GPIO 9
 GPIO 9(20) │ ② ① │ (21) GPIO 25
            └─────────────────┘
```

### 详细引脚功能表

| Pin | Name | Function | 中断支持 |
|-----|------|----------|---------|
| 3 | GPIO 2 | SDA1 (I2C) | ✅ |
| 5 | GPIO 3 | SCL1 (I2C) | ✅ |
| 7 | GPIO 4 | GPIO 通用 | ✅ |
| 8 | GPIO 14 | TXD0 (串口) | ✅ |
| 10| GPIO 15 | RXD0 (串口) | ✅ |
| 11| GPIO 17 | GPIO 通用 | ✅ |
| 12| GPIO 18 | PWM0 | ✅ |
| 13| GPIO 27 | GPIO 通用 | ✅ |
| 15| GPIO 22 | GPIO 通用 | ✅ |
| 16| GPIO 23 | GPIO 通用 | ✅ |
| 18| GPIO 24 | GPIO 通用 | ✅ |
| 19| GPIO 10 | MOSI1 (SPI) | ✅ |
| 21| GPIO 9 | MISO1 (SPI) | ✅ |
| 22| GPIO 25 | GPIO 通用 | ✅ |
| 23| GPIO 11 | SCLK1 (SPI) | ✅ |
| 24| GPIO 8 | CE0 (SPI) | ✅ |
| 26| GPIO 7 | CE1 (SPI) | ✅ |
| 29| GPIO 5 | GPIO 通用 | ✅ |
| 31| GPIO 6 | GPIO 通用 | ✅ |
| 32| GPIO 12 | PWM0 | ✅ |
| 33| GPIO 13 | PWM1 | ✅ |
| 35| GPIO 19 | MISO2 (SPI) | ✅ |
| 36| GPIO 16 | CE2 (SPI) | ✅ |
| 37| GPIO 26 | GPIO 通用 | ✅ |
| 38| GPIO 20 | MOSI2 (SPI) | ✅ |
| 40| GPIO 21 | SCLK2 (SPI) | ✅ |

## 💡 常见应用场景

### 1. 按钮检测

检测按钮按下/释放事件，用于用户交互。

```bash
# 检测按钮按下（下降沿）
python3 gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=1 \
    _duration:=30
```

### 2. 限位开关

机械限位开关检测，用于运动控制。

```bash
# 检测限位开关触发
python3 gpio_interrupt_client.py \
    _pin_number:=22 \
    _edge_mode:=1 \
    _debounce_ms:=10
```

### 3. 光电传感器

光电开关检测，用于计数或位置检测。

```bash
# 检测物体通过
python3 gpio_interrupt_client.py \
    _pin_number:=27 \
    _edge_mode:=2 \
    _duration:=60
```

### 4. 旋转编码器

旋转编码器 A/B 相信号检测。

```python
# 需要同时监听两个引脚
# Pin A: GPIO 27
# Pin B: GPIO 22
```

### 5. 外部设备触发

外部定时器、脉冲等信号检测。

```bash
# 检测外部脉冲
python3 gpio_interrupt_client.py \
    _pin_number:=18 \
    _edge_mode:=2 \
    _debounce_ms:=5
```

### 6. 紧急停止

工业控制中的紧急停止按钮。

```bash
# 快速响应停止信号
python3 gpio_interrupt_client.py \
    _pin_number:=26 \
    _edge_mode:=1 \
    _debounce_ms:=10
```

## ⚠️ 注意事项

### 1. 电压范围

- Jetson Nano GPIO 工作电压: **3.3V**
- 超过 3.3V 可能损坏 GPIO
- 使用 5V 设备需要电平转换

### 2. 电流限制

- 每个 GPIO 最大输出电流: ~16mA
- 所有 GPIO 总电流: ~200mA
- 驱动大电流设备需要使用三极管或继电器

### 3. 避免的引脚

以下引脚不建议用于中断：
- **Pin 3, 5**: I2C 通信（可能冲突）
- **Pin 8, 10**: 串口通信（可能冲突）
- **Pin 19, 21, 23, 24, 26**: SPI 通信（可能冲突）

### 4. 上拉/下拉电阻

- 推荐阻值: 1kΩ - 10kΩ
- 默认: 10kΩ
- 小电阻: 功耗大，响应快
- 大电阻: 功耗小，响应慢

### 5. 信号稳定性

- 避免长导线（会产生噪声）
- 使用屏蔽线
- 添加去抖动
- 使用光耦隔离

### 6. 中断优先级

- GPIO 中断优先级较低
- 如果有多个中断源，需要处理优先级
- 考虑使用实时操作系统（RTOS）

## 🔧 代码分析

### Server 端核心代码

```python
# 设置 GPIO 为输入模式，启用上拉电阻
GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 设置中断检测
GPIO.add_event_detect(
    pin_number,      # GPIO 引脚号
    edge,            # 边沿类型 (RISING, FALLING, BOTH)
    callback=self.interrupt_callback,  # 回调函数
    bouncetime=debounce_ms             # 去抖动时间
)

# 中断回调函数
def interrupt_callback(self, channel):
    self.interrupt_count += 1
    current_state = GPIO.input(channel)
    
    # 发送 Feedback
    feedback = GPIOInterruptFeedback()
    feedback.event_type = String(data="rising" if current_state else "falling")
    feedback.timestamp = int(time.time() * 1e9)
    self.server.publish_feedback(feedback)
```

### Client 端核心代码

```python
# 发送 Goal
goal = GPIOInterruptGoal()
goal.pin_number = pin_number
goal.edge_mode = edge_mode
goal.debounce_ms = debounce_ms
self.client.send_goal(goal, feedback_cb=self.feedback_cb)

# 接收 Feedback
def feedback_cb(self, feedback):
    self.interrupt_count += 1
    rospy.loginfo(f"🔔 中断 #{self.interrupt_count}: "
                 f"{feedback.event_type.data} "
                 f"at {timestamp_str}")
```

## 📊 边沿模式对比

| 模式 | 值 | 触发条件 | 应用场景 |
|------|-----|---------|---------|
| 上升沿 | 0 | LOW → HIGH | 光电传感器、霍尔传感器 |
| 下降沿 | 1 | HIGH → LOW | 按钮、限位开关 |
| 双边沿 | 2 | 上升+下降 | 旋转编码器、脉冲计数 |

## 🎯 性能优化

### 1. 中断响应时间

- GPIO 硬件中断响应: ~1μs
- Python 回调执行: ~100μs - 1ms
- ROS Feedback 发送: ~1ms - 5ms

### 2. 去抖动优化

```python
# 快速信号（光电传感器）
debounce_ms = 5

# 机械按钮
debounce_ms = 50

# 抖动大的信号
debounce_ms = 200
```

### 3. 减少延迟

- 使用双边沿检测可以减少遗漏
- 合理设置去抖动时间
- 优化回调函数代码

## 📝 扩展建议

### 1. 支持多个 GPIO

```python
# 同时监听多个 GPIO
pins = [18, 22, 27]
for pin in pins:
    GPIO.add_event_detect(pin, GPIO.BOTH, callback=multi_gpio_callback)
```

### 2. 脉冲宽度测量

```python
def multi_gpio_callback(channel):
    now = time.time()
    if channel in self.last_time:
        pulse_width = (now - self.last_time[channel]) * 1e3  # ms
        rospy.loginfo(f"脉冲宽度: {pulse_width:.2f} ms")
    self.last_time[channel] = now
```

### 3. 频率统计

```python
# 统计中断频率
if self.interrupt_count > 0:
    elapsed = time.time() - self.start_time
    frequency = self.interrupt_count / elapsed
    rospy.loginfo(f"中断频率: {frequency:.2f} Hz")
```

### 4. 事件记录

```python
# 记录所有中断事件到文件
with open('gpio_events.log', 'a') as f:
    f.write(f"{timestamp},{channel},{event_type}\n")
```

## 🔗 相关资源

- [Jetson.GPIO 官方文档](https://github.com/NVIDIA/jetson-gpio)
- [GPIO 中断原理](https://www.kernel.org/doc/Documentation/gpio/sysfs.txt)
- [ROS Actionlib 教程](http://wiki.ros.org/actionlib)
- [Jetson Nano 引脚图](https://www.pinout.xyz/)

## 📞 问题反馈

如有问题或建议，请联系项目维护者。

---

**作者**: Jetson Nano Developer  
**日期**: 2026-03-31  
**版本**: 1.0.0