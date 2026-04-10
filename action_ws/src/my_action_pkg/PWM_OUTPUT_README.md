# GPIO PWM 输出 Action 实现说明文档

## 📋 项目概述

基于 ROS Action 和 Jetson.GPIO 库实现 GPIO PWM 输出功能，支持频率和占空比控制，适用于 LED 调光、伺服电机控制、电机调速等应用场景。

## 🏗️ 文件结构

```
my_action_pkg/
├── action/
│   └── PWMOutput.action          # PWM 输出 Action 定义
├── scripts/
│   ├── pwm_output_server.py      # PWM 输出服务器
│   └── pwm_output_client.py      # PWM 输出客户端
└── launch/
    └── pwm_output.launch         # 启动文件
```

## 📦 Action 定义

### Goal - 发送目标
```yaml
uint8 pin_number           # GPIO 引脚号 (BCM 编号)
uint32 frequency           # PWM 频率 (Hz)
uint8 duty_cycle           # 占空比 0-100%
float32 duration           # 持续时间 (秒)
```

### Result - 返回结果
```yaml
bool success               # 操作是否成功
```

### Feedback - 进度反馈
```yaml
uint8 current_duty_cycle   # 当前占空比
uint64 timestamp           # 时间戳 (纳秒)
```

## 🔌 硬件连接

### Jetson Nano PWM 引脚

| 物理引脚 | BCM 编号 | PWM 通道 | 功能 | 支持状态 |
|---------|---------|---------|------|---------|
| **32** | **12** | PWM0 | PWM 通道 0 | ⭐⭐⭐⭐⭐ 推荐 |
| **33** | **13** | PWM1 | PWM 通道 1 | ⭐⭐⭐⭐⭐ 推荐 |
| 12 | 18 | - | GPIO 通用 | ❌ 不支持 PWM |
| 35 | 19 | - | GPIO 通用 | ❌ 不支持 PWM |

### ⚠️ 重要提示

**Jetson Nano 仅支持 2 个 PWM 通道：**
- **PWM0**: 仅 GPIO 12 (Pin 32)
- **PWM1**: 仅 GPIO 13 (Pin 33)

**常见错误:**
- GPIO 18 (Pin 12) - 不支持 PWM ❌
- GPIO 19 (Pin 35) - 不支持 PWM ❌

### PWM 引脚图

```
             ┌────────────────────────────────┐
   3.3V (1) │ ② ① │ (40) GND
   5V  (2) │ ④ ③ │ (39) GND
 GPIO 2 (3) │ ⑥ ⑤ │ (38) GPIO 20
   5V  (4) │ ⑧ ⑦ │ (37) GPIO 26
 GPIO 3 (5) │ ⑨ ⑨ │ (36) GPIO 16
 GND  (6) │ ⑪ ⑪ │ (35) GPIO 19
 GPIO 4 (7) │ ⑫ ⑫ │ (34) GND
 GPIO14 (8) │ ⑭ ⑭ │ (33) GPIO 13 ✅ (PWM1)
 GND  (9) │ ⑮ ⑮ │ (32) GPIO 12 ✅ (PWM0)
 GPIO15(10) │ ⑯ ⑯ │ (31) GPIO 6
 GPIO17(11) │ ⑱ ⑱ │ (30) GND
 GPIO18(12) │ ⑲ ⑱ │ (29) GPIO 5
 GPIO27(13) │ ⑳ ⑲ │ (28) GPIO 4
 GND  (14) │ ⑵ ⑴ │ (27) ID_SD
 GPIO23(15) │ ⑶ ⑵ │ (26) ID_SC
  3.3V(16) │ ⑸ ⑶ │ (25) GND
 GPIO24(17) │ ⑹ ⑸ │ (24) GPIO 8
 GPIO10(18) │ ⑺ ⑹ │ (23) GPIO 11
 GND  (19) │ ⑻ ⑺ │ (22) GPIO 9
 GPIO 9 (20) │ ⑽ ⑻ │ (21) GPIO 10
             └────────────────────────────────┘
```

**标注说明:**
- ✅ = 支持 PWM 的引脚（仅 GPIO 12 和 GPIO 13）
- ⚠️ = 不支持 PWM 的 GPIO 18 和 GPIO 19

### 硬件连接示例

#### 示例 1: LED 调光（推荐使用 GPIO 12）

```
Pin 32 (GPIO 12) ✅
    │
    │
   LED (正极 → 引脚)
    │
  220Ω 电阻
    │
   GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
```

**占空比与亮度关系:**
- 0%: LED 关闭
- 25%: LED 较暗
- 50%: LED 半亮
- 75%: LED 较亮
- 100%: LED 全亮

#### 示例 2: 伺服电机控制（GPIO 12）

```
Pin 32 (GPIO 12) ✅
    │
    │
  伺服电机信号线 (橙色/黄色)
  
伺服电机:
  - 红色线 → 5V (Pin 2 或 4)
  - 棕色线 → GND
  - 橙色线 → GPIO 12 (PWM 信号)
```

**伺服电机 PWM 参数:**
- 频率: 50 Hz (20ms 周期)
- 占空比范围: 5% - 10%
  - 5% (1ms) → -90°
  - 7.5% (1.5ms) → 0°
  - 10% (2ms) → +90°

#### 示例 3: 蜂鸣器控制（GPIO 13）

```
Pin 33 (GPIO 13) ✅
    │
    │
  蜂鸣器
    │
  100Ω 电阻
    │
   GND
```

**注意:** GPIO 13 和 GPIO 12 是独立的 PWM 通道，可以同时使用。

## 🚀 使用方法

### 1. 编译项目

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make install
source install/setup.bash
```

### 2. 启动 Server (需要 sudo 权限)

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash
sudo roslaunch my_action_pkg pwm_output.launch
```

### 3. 控制 PWM 输出

打开新终端：

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash

# 使用 python3 直接运行（推荐）
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/pwm_output_client.py \
    _pin_number:=12 \
    _frequency:=1000 \
    _duty_cycle:=50 \
    _duration:=5
```

## ⚙️ 参数配置

### Goal 参数

| 参数 | 默认值 | 说明 | 范围 |
|------|--------|------|------|
| `pin_number` | 12 | GPIO 引脚号 (BCM) | **12, 13** (仅这两个支持 PWM) |
| `frequency` | 1000 | PWM 频率 | 1-10000 Hz |
| `duty_cycle` | 50 | 占空比 | 0-100% |
| `duration` | 5 | 持续时间（秒） | 0.1-3600 秒 |

### ⚠️ 重要提示

**Jetson Nano 仅支持 2 个 PWM 引脚：**
- **GPIO 12** (Pin 32) - PWM0 通道
- **GPIO 13** (Pin 33) - PWM1 通道

**不支持的引脚：**
- GPIO 18 (Pin 12) - ❌
- GPIO 19 (Pin 35) - ❌

### 常用 PWM 频率

| 应用场景 | 频率 | 说明 |
|---------|------|------|
| LED 调光 | 100-1000 Hz | 人眼无法察觉闪烁 |
| 伺服电机 | 50 Hz | 标准伺服控制频率 |
| 直流电机 | 1-20 kHz | 高频可降低噪音 |
| 蜂鸣器 | 500-5000 Hz | 产生不同音调 |

## 📊 工作流程

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │────────▶│   Server    │────────▶│   GPIO      │
│             │  Goal   │             │  Start   │  (PWM 信号)  │
│             │         │             │ PWM     │             │
│   Client    │◀────────│   Server    │◀────────│  硬件设备   │
│             │  Result │             │  Status  │ (LED/电机)   │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ▼
                      Feedback (PWM 状态)
```

## 🔍 测试示例

### 示例 1: LED 呼吸效果

```bash
# 硬件准备: LED 连接到 Pin 32 (GPIO 12)

# 50% 占空比，500 Hz，持续 10 秒
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/pwm_output_client.py \
    _pin_number:=12 \
    _frequency:=500 \
    _duty_cycle:=50 \
    _duration:=10
```

### 示例 2: LED 亮度渐变

```bash
# 25% 占空比（较暗）
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=25 _duration:=3

# 50% 占空比（半亮）
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=50 _duration:=3

# 75% 占空比（较亮）
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=75 _duration:=3

# 100% 占空比（全亮）
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=100 _duration:=3
```

### 示例 3: 伺服电机控制

```bash
# 0° 位置 (7.5% 占空比)
python3 pwm_output_client.py _pin_number:=12 _frequency:=50 _duty_cycle:=7.5 _duration:=2

# +90° 位置 (10% 占空比)
python3 pwm_output_client.py _pin_number:=12 _frequency:=50 _duty_cycle:=10 _duration:=2

# -90° 位置 (5% 占空比)
python3 pwm_output_client.py _pin_number:=12 _frequency:=50 _duty_cycle:=5 _duration:=2
```

### 示例 4: 高频 PWM（电机调速）

```bash
# 20 kHz 高频 PWM
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=30 _duration:=5

# 低速运行 (30% 占空比)
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=30 _duration:=5

# 中速运行 (60% 占空比)
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=60 _duration:=5

# 高速运行 (90% 占空比)
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=90 _duration:=5
```

### 示例 5: 蜂鸣器音调

```bash
# 低音 (500 Hz)
python3 pwm_output_client.py _pin_number:=13 _frequency:=500 _duty_cycle:=50 _duration:=1

# 中音 (1000 Hz)
python3 pwm_output_client.py _pin_number:=13 _frequency:=1000 _duty_cycle:=50 _duration:=1

# 高音 (2000 Hz)
python3 pwm_output_client.py _pin_number:=13 _frequency:=2000 _duty_cycle:=50 _duration:=1
```

## 🐛 故障排除

### 1. 引脚不支持 PWM

**问题**: `❌ 引脚 XX 不支持 PWM`

**原因:** Jetson Nano 仅支持 GPIO 12 和 GPIO 13

**解决方法:**
- 使用 GPIO 12 (Pin 32) 或 GPIO 13 (Pin 33)
- 避免使用 GPIO 18 或 GPIO 19

### 2. PWM 无输出

**问题:** LED 不亮或设备无响应

**可能原因:**
- 引脚配置错误
- 频率超出范围
- 硬件连接问题

**解决方法:**
```bash
# 检查 PWM 引脚
python3 -c "
import Jetson.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(12, GPIO.OUT)
pwm = GPIO.PWM(12, 1000)
pwm.start(50)
print('PWM 已启动')
import time
time.sleep(2)
pwm.stop()
GPIO.cleanup(12)
"
```

### 3. 占空比无效

**问题:** 占空比超出 0-100% 范围

**解决方法:**
- 确保占空比在 0-100% 之间
- 检查参数类型（uint8 最大值是 255）

## 💡 常见应用场景

### 1. LED 调光

**应用:** 智能照明、RGB LED 控制、指示灯

```bash
# 亮度控制
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=50 _duration:=10

# RGB LED (2 个 PWM 引脚可用)
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=100 _duration:=5  # 红色
python3 pwm_output_client.py _pin_number:=13 _frequency:=1000 _duty_cycle:=50 _duration:=5   # 绿色
```

### 2. 伺服电机控制

**应用:** 机器人关节、云台控制、机械臂

```bash
# 角度控制
python3 pwm_output_client.py _pin_number:=12 _frequency:=50 _duty_cycle:=7.5 _duration:=2  # 0°
python3 pwm_output_client.py _pin_number:=12 _frequency:=50 _duty_cycle:=10 _duration:=2   # +90°
python3 pwm_output_client.py _pin_number:=12 _frequency:=50 _duty_cycle:=5 _duration:=2    # -90°
```

### 3. 直流电机调速

**应用:** 小车控制、风扇调速、水泵控制

```bash
# 速度控制
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=30 _duration:=5  # 低速
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=60 _duration:=5  # 中速
python3 pwm_output_client.py _pin_number:=13 _frequency:=20000 _duty_cycle:=90 _duration:=5  # 高速
```

### 4. 蜂鸣器控制

**应用:** 报警提示、音乐播放、音效

```bash
# 音调控制
python3 pwm_output_client.py _pin_number:=13 _frequency:=500 _duty_cycle:=50 _duration:=1   # 低音
python3 pwm_output_client.py _pin_number:=13 _frequency:=1000 _duty_cycle:=50 _duration:=1  # 中音
python3 pwm_output_client.py _pin_number:=13 _frequency:=2000 _duty_cycle:=50 _duration:=1  # 高音
```

### 5. 温度控制

**应用:** 加热器控制、风扇调速、恒温控制

```bash
# 加热器控制
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=80 _duration:=30  # 加热
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=20 _duration:=30  # 保温
python3 pwm_output_client.py _pin_number:=12 _frequency:=1000 _duty_cycle:=0 _duration:=30   # 停止
```

## 📊 PWM 引脚选择建议

### ⚠️ 重要限制

**Jetson Nano 仅支持 2 个 PWM 引脚:**
- **GPIO 12** (Pin 32) - PWM0 通道
- **GPIO 13** (Pin 33) - PWM1 通道

**不支持 PWM 的引脚:**
- GPIO 18 (Pin 12) - ❌ 仅普通 GPIO
- GPIO 19 (Pin 35) - ❌ 仅普通 GPIO

### 选择标准

1. **功能需求**
   - LED 调光: 任一 PWM 引脚（推荐 GPIO 12）
   - 伺服电机: 推荐 GPIO 12
   - 直流电机: 推荐 GPIO 13（独立通道）
   - 蜂鸣器: GPIO 13

2. **硬件布局**
   - 根据硬件连接位置选择
   - 避免长导线（信号衰减）

3. **性能要求**
   - 高频应用: 任一 PWM 引脚
   - 精度要求: 两个引脚精度相同

4. **避免冲突**
   - GPIO 12 和 GPIO 13 是独立 PWM 通道，可以同时使用
   - 不使用 I2C、串口等专用引脚

### 推荐方案

| 应用 | 推荐引脚 | 原因 |
|------|---------|------|
| LED 调光 | GPIO 12 (Pin 32) | 最常用，容易访问 |
| 伺服电机 | GPIO 12 (Pin 32) | PWM0，位置方便 |
| 直流电机 | GPIO 13 (Pin 33) | PWM1，独立通道 |
| 蜂鸣器 | GPIO 13 (Pin 33) | PWM1，位置独立 |

## ⚠️ 注意事项

### 1. 电压限制

- Jetson Nano GPIO 电压: **3.3V**
- 超过 3.3V 的设备需要电平转换
- 5V 设备不能直接连接

### 2. 电流限制

- 每个 GPIO 最大输出电流: ~16mA
- 总电流限制: ~200mA
- 驱动大电流设备需要使用三极管或驱动模块

### 3. PWM 频率限制

- Jetson.GPIO PWM 频率范围: **1 Hz - 10000 Hz**
- 过低频率可能导致设备抖动
- 过高频率可能降低精度

### 4. 占空比范围

- 占空比范围: **0-100%**
- 必须为整数 (uint8 类型)
- 超出范围会被截断或报错

### 5. 持续时间限制

- 最小持续时间: 0.1 秒
- 最大持续时间: 3600 秒 (1小时)
- 长时间运行需要注意散热

### 6. 引脚冲突

- 避免使用 I2C、串口等专用引脚
- 同一 PWM 通道的引脚不能同时使用
- 检查引脚是否被其他程序占用

## 🎯 总结

本项目演示了如何使用 ROS Action 和 Jetson.GPIO 库实现 PWM 输出功能。PWM 是控制外设输出的重要方式，广泛应用于 LED 调光、电机控制、伺服驱动等场景。

### 关键点

1. ✅ 基于 Action 框架实现 PWM 控制
2. ✅ 支持频率和占空比参数配置
3. ✅ 实时反馈 PWM 状态
4. ✅ 仅支持 2 个 PWM 引脚 (GPIO 12, 13)
5. ✅ 详细的错误处理
6. ✅ 资源自动清理

### PWM 优势

1. **精确控制**: 可以精确控制功率和速度
2. **高效率**: 减少功耗和热量
3. **平滑调节**: 实现无级调速/调光
4. **广泛兼容**: 适用于多种设备

## 🔗 相关资源

- [Jetson.GPIO 官方文档](https://github.com/NVIDIA/jetson-gpio)
- [PWM 原理说明](https://en.wikipedia.org/wiki/Pulse-width_modulation)
- [ROS Actionlib 教程](http://wiki.ros.org/actionlib)
- [伺服电机控制教程](https://www.arduino.cc/en/Reference/Servo)

---

**作者**: Jetson Nano Developer  
**日期**: 2026-03-31  
**版本**: 1.0.0