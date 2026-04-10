# I2C 通信 Action 实现说明

## 📋 概述

基于 ROS Action 和 smbus2 库实现 I2C 通信功能，支持向指定 I2C 设备写入数据并读取回环数据。

## 🏗️ 文件结构

```
my_action_pkg/
├── action/
│   └── I2CComm.action           # I2C 通信 Action 定义
├── scripts/
│   ├── i2c_comm_server.py       # I2C 通信服务器
│   └── i2c_comm_client.py       # I2C 通信客户端
└── launch/
    └── i2c_comm.launch          # 启动文件
```

## 📦 Action 定义

### Goal - 发送目标
```yaml
uint8 device_address      # I2C 设备地址 (0x00-0x7F)
uint8 register_address    # 寄存器地址 (0x00-0xFF)
uint8 data                # 要写入的数据 (0x00-0xFF)
```

### Result - 返回结果
```yaml
uint8 received_data       # 从设备读取的数据
bool success              # 操作是否成功
```

### Feedback - 进度反馈
```yaml
std_msgs/String status    # 状态描述
```

## 🔌 硬件连接

### Jetson Nano I2C 引脚

| 物理引脚 | GPIO | 设备 | 功能 |
|---------|------|------|------|
| **3** | GPIO 2 | /dev/i2c-1 | I2C1_SDA (数据线) |
| **5** | GPIO 3 | /dev/i2c-1 | I2C1_SCL (时钟线) |

### I2C 总线说明

Jetson Nano 通常有两个 I2C 总线：
- **I2C0**: `/dev/i2c-0` - 引脚 27 (SDA), 28 (SCL)
- **I2C1**: `/dev/i2c-1` - 引脚 3 (SDA1), 5 (SCL1) ✅ (推荐)

## 🚀 使用方法

### 1. 安装依赖

```bash
# 安装 smbus2 库
sudo apt update
sudo apt install python3-smbus2

# 或使用 pip
pip3 install smbus2
```

### 2. 启动 Server (需要 sudo 权限)

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash
sudo roslaunch my_action_pkg i2c_comm.launch
```

### 3. 发送数据 (Client)

打开新终端，执行：

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash

# 使用 python3 直接运行（推荐）
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/i2c_comm_client.py \
    _device_address:=0x50 \
    _register_address:=0x00 \
    _data:=0xAA
```

## ⚙️ 参数配置

### Server 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `i2c_bus` | `1` | I2C 总线编号 (0 或 1) |
| `enable_scan` | `false` | 是否在启动时扫描设备 |
| `enable_echo` | `true` | 是否打印详细日志 |

### Client 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `_device_address` | `0x50` | I2C 设备地址 |
| `_register_address` | `0x00` | 寄存器地址 |
| `_data` | `0xAA` | 要写入的数据 |

### 修改 Server 参数

#### 方法 1: 通过 launch 文件
```xml
<launch>
  <node name="i2c_comm_server" pkg="my_action_pkg" type="i2c_comm_server.py">
    <param name="i2c_bus" value="1" />
    <param name="enable_scan" value="true" />
    <param name="enable_echo" value="true" />
  </node>
</launch>
```

#### 方法 2: 通过命令行
```bash
sudo roslaunch my_action_pkg i2c_comm.launch i2c_bus:=1 enable_scan:=true
```

## 📊 工作流程

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │────────▶│   Server    │────────▶│  I2C 设备   │
│             │  Goal   │             │  Write  │  0x50:0x00  │
│             │         │             │         │             │
│   Client    │◀────────│   Server    │◀────────│  I2C 设备   │
│             │  Result │             │  Read   │  0x50:0x00  │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ▼
                      Feedback (可选)
```

## 🔍 测试示例

### 示例 1: 读写 EEPROM (地址 0x50)

```bash
# 写入数据 0xAA 到寄存器 0x00
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/i2c_comm_client.py \
    _device_address:=0x50 \
    _register_address:=0x00 \
    _data:=0xAA
```

### 示例 2: 使用不同总线

```bash
# 使用 I2C0 总线
sudo roslaunch my_action_pkg i2c_comm.launch i2c_bus:=0
```

### 示例 3: 启用设备扫描

```bash
# Server 启动时会自动扫描所有 I2C 设备
sudo roslaunch my_action_pkg i2c_comm.launch enable_scan:=true
```

## 🐛 故障排除

### 1. 权限错误

**问题**: `Permission denied: '/dev/i2c-1'`

**解决方法**: 使用 sudo 运行 Server
```bash
sudo roslaunch my_action_pkg i2c_comm.launch
```

或添加用户到 i2c 组：
```bash
sudo usermod -a -G i2c $USER
# 需要重新登录才能生效
```

### 2. 设备无响应

**问题**: `I2C I/O error`

**可能原因**:
- 设备地址错误
- 设备未正确连接
- 上拉电阻未连接

**解决方法**:
1. 扫描 I2C 设备确认设备地址
2. 检查硬件连接
3. 确保上拉电阻连接（4.7kΩ）

### 3. 未找到 smbus2

**问题**: `ModuleNotFoundError: No module named 'smbus2'`

**解决方法**:
```bash
sudo apt install python3-smbus2
# 或
pip3 install smbus2
```

## 🔍 I2C 设备扫描

使用提供的扫描功能查找 I2C 设备：

```bash
# 方法 1: 通过参数启用扫描
sudo roslaunch my_action_pkg i2c_comm.launch enable_scan:=true

# 方法 2: 手动扫描
sudo i2cdetect -y 1
```

扫描结果示例：
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: 50 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- -- --
```

表示在地址 `0x50` 有一个设备。

## 📚 SMBus2 API 参考

### 常用方法

```python
from smbus2 import SMBus

bus = SMBus(1)  # 打开 /dev/i2c-1

# 写入一个字节到寄存器
bus.write_byte_data(0x50, 0x00, 0xAA)

# 从寄存器读取一个字节
data = bus.read_byte_data(0x50, 0x00)

# 写入字节数组
bus.write_i2c_block_data(0x50, 0x00, [0x01, 0x02, 0x03])

# 读取字节数组
data = bus.read_i2c_block_data(0x50, 0x00, 16)

bus.close()  # 关闭总线
```

## 💡 常见 I2C 设备地址

| 设备类型 | 默认地址 | 说明 |
|---------|---------|------|
| EEPROM (AT24C02) | 0x50-0x57 | 常用 EEPROM 芯片 |
| RTC (DS1307) | 0x68 | 实时时钟 |
| 温度传感器 (LM75) | 0x48-0x4F | 温度传感器 |
| 加速度计 (MPU6050) | 0x68 | IMU 传感器 |
| OLED 显示屏 | 0x3C | SSD1306 OLED |
| LCD1602 (PCF8574) | 0x27, 0x3F | LCD 扩展板 |

## 📝 代码注释说明

所有代码都包含详细的中文注释：

- **Server 端** (`i2c_comm_server.py`):
  - I2C 总线初始化
  - 设备扫描功能
  - 数据写入和读取
  - 异常处理

- **Client 端** (`i2c_comm_client.py`):
  - 参数获取
  - Goal 发送
  - Feedback 和 Result 处理

## 🎯 总结

本项目演示了如何使用 ROS Action 和 smbus2 库实现 I2C 通信功能。完整的代码注释便于学习和理解 I2C 通信原理和 ROS Action 框架的使用。

---

**作者**: Jetson Nano Developer  
**日期**: 2026-03-30  
**版本**: 1.0.0