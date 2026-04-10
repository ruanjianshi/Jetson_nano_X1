# SPI 通信 Action 实现说明

## 📋 项目概述

基于 ROS Action 和 spidev 库实现 SPI 通信功能，支持向指定 SPI 设备写入数据并读取回环数据。

## 🏗️ 文件结构

```
my_action_pkg/
├── action/
│   └── SPIComm.action           # SPI 通信 Action 定义
├── scripts/
│   ├── spi_comm_server.py       # SPI 通信服务器 (Python)
│   └── spi_comm_client.py       # SPI 通信客户端 (Python)
├── src/
│   ├── spi_comm_server.cpp       # SPI 通信服务器 (C++)
│   └── spi_comm_client.cpp       # SPI 通信客户端 (C++)
└── launch/
    └── spi_comm.launch          # 启动文件
```

## 💻 可用版本

本项目提供两个版本的 SPI 通信实现：

| 版本 | 语言 | 优点 | 使用场景 |
|------|------|------|---------|
| **Python** | Python | 简单易用，快速开发 | 开发测试、教学、原型 |
| **C++** | C++ | 高性能，类型安全 | 生产环境、高性能应用 |

## 📦 Action 定义

### Goal - 发送目标
```yaml
uint8 spi_bus              # SPI 总线编号 (0, 1, 2)
uint8 device_address       # 设备地址 (片选线编号)
uint8 write_data           # 要写入的数据 (1字节)
bool read_after_write      # 写入后是否读取
```

### Result - 返回结果
```yaml
bool success               # 操作是否成功
uint8 received_data        # 接收到的数据
```

### Feedback - 进度反馈
```yaml
std_msgs/String status    # 状态描述
uint8 current_data         # 当前数据
```

## 🔌 硬件连接

### Jetson Nano SPI 引脚

| 物理引脚 | GPIO | 设备 | 功能 |
|---------|------|------|------|
| **19** | GPIO 10 | /dev/spidev0.0 | MOSI1 (主出从入) |
| **21** | GPIO 9 | /dev/spidev0.0 | MISO1 (主入从出) |
| **23** | GPIO 11 | /dev/spidev0.0 | SCLK1 (时钟) |
| **24** | GPIO 8 | /dev/spidev0.0 | CE0 (片选 0) |
| **26** | GPIO 7 | /dev/spidev0.1 | CE1 (片选 1) |

### SPI 总线说明

Jetson Nano 通常有多个 SPI 总线：
- **SPI0**: `/dev/spidev0.0` (CE0), `/dev/spidev0.1` (CE1)
  - 引脚: 19 (MOSI), 21 (MISO), 23 (SCLK), 24 (CE0), 26 (CE1)

### 硬件连接示例

#### 示例 1: SPI 回环测试

```
Pin 19 (MOSI) ───┐
                 │
                 └── Pin 21 (MISO)  (回环连接)

Pin 23 (SCLK) ───┐
                 │
                 └── Pin 23 (SCLK)  (无需连接)

Pin 24 (CE0) ────┐
                 │
                 └── Pin 24 (CE0)   (无需连接)
```

#### 示例 2: 连接 SPI 设备

```
Jetson Nano              SPI 设备
    19 (MOSI) ────────── MOSI
    21 (MISO) ────────── MISO
    23 (SCLK) ────────── SCLK
    24 (CE0)  ────────── CS
    GND      ────────── GND
```

## 🚀 使用方法

### 1. 安装依赖

```bash
# 安装 spidev 库（Python 版本需要）
sudo apt update
sudo apt install python3-spidev

# 或使用 pip
pip3 install spidev
```

### 2. 编译项目

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make
source install/setup.bash
```

### 3. 启动 Server (需要 sudo 权限)

```bash
source install/setup.bash

# Python 版本
sudo roslaunch my_action_pkg spi_comm.launch

# C++ 版本
sudo rosrun my_action_pkg spi_comm_server_cpp
```

### 4. 发送数据 (Client)

打开新终端，执行：

```bash
source install/setup.bash

# Python 版本
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/spi_comm_client.py \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=true

# C++ 版本
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=true
```

## ⚙️ 参数配置

### Server 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `enable_echo` | `true` | 是否打印详细日志 |

### Client 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `_spi_bus` | `0` | SPI 总线编号 |
| `_device_address` | `0` | 设备地址 (片选编号) |
| `_write_data` | `0xAA` | 要写入的数据 |
| `_read_after_write` | `true` | 写入后是否读取 |

### 修改 Server 参数

#### 方法 1: 通过 launch 文件
```xml
<launch>
  <node name="spi_comm_server" pkg="my_action_pkg" type="spi_comm_server.py">
    <param name="enable_echo" value="true" />
  </node>
</launch>
```

#### 方法 2: 通过命令行
```bash
sudo roslaunch my_action_pkg spi_comm.launch enable_echo:=false
```

## 📊 工作流程

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │────────▶│   Server    │────────▶│  SPI 设备   │
│             │  Goal   │             │  Write  │  spidev0.0  │
│             │         │             │         │             │
│   Client    │◀────────│   Server    │◀────────│  SPI 设备   │
│             │  Result │             │  Read   │  spidev0.0  │
└─────────────┘         └─────────────┘         └─────────────┘
                               │
                               ▼
                       Feedback (可选)
```

## 🔍 测试示例

### 示例 1: SPI 回环测试

```bash
# 硬件准备: 短接 Pin 19 (MOSI) 和 Pin 21 (MISO)

# 启动 Server
sudo roslaunch my_action_pkg spi_comm.launch

# 发送数据 0xAA 并读取回环数据
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/spi_comm_client.py \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=true
```

### 示例 2: 使用 CE1 片选

```bash
# 使用片选 1 (Pin 26)
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/spi_comm_client.py \
    _spi_bus:=0 \
    _device_address:=1 \
    _write_data:=0x55
```

### 示例 3: 仅写入不读取

```bash
# 只写入数据，不读取
python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/spi_comm_client.py \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xFF \
    _read_after_write:=false
```

## 🐛 故障排除

### 1. 权限错误

**问题**: `Permission denied: '/dev/spidev0.0'`

**解决方法**: 使用 sudo 运行 Server
```bash
sudo roslaunch my_action_pkg spi_comm.launch
```

或添加用户到 spi 组：
```bash
sudo usermod -a -G spi $USER
# 需要重新登录才能生效
```

### 2. 设备不存在

**问题**: `FileNotFoundError: [Errno 2] No such file or directory: '/dev/spidev0.0'`

**可能原因**:
- SPI 未在设备树中启用
- 总线编号错误

**解决方法**:
```bash
# 检查 SPI 设备
ls -l /dev/spidev*

# 检查设备树配置
sudo dtc -I fs /sys/firmware/devicetree/base
```

### 3. 设备无响应

**问题**: 数据写入成功但读取异常

**可能原因**:
- 硬件连接问题
- SPI 参数不匹配
- 设备需要特定命令

**解决方法**:
```bash
# 检查硬件连接
# 确认 MOSI、MISO、SCLK、CS 引脚正确连接

# 测试 SPI 设备
python3 -c "
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
print('发送:', [0xAA])
print('接收:', spi.xfer2([0xAA]))
spi.close()
"
```

### 4. 未找到 spidev

**问题**: `ModuleNotFoundError: No module named 'spidev'`

**解决方法**:
```bash
sudo apt install python3-spidev
# 或
pip3 install spidev
```

## 📚 spidev API 参考

### 常用方法

```python
import spidev

# 打开 SPI 设备
spi = spidev.SpiDev()
spi.open(bus, device)  # bus: 总线编号, device: 片选编号

# 配置 SPI 参数
spi.max_speed_hz = 1000000  # 时钟频率 (1 MHz)
spi.mode = 0                 # SPI 模式 (0-3)
spi.bits_per_word = 8        # 字长 (8 bit)

# 写入并读取数据
data = spi.xfer2([0xAA, 0xBB])  # 返回读取的数据列表

# 写入数据（不读取）
spi.writebytes([0xAA, 0xBB])

# 读取数据
data = spi.readbytes(2)

# 关闭 SPI 设备
spi.close()
```

### SPI 模式说明

| 模式 | CPOL | CPHA | 说明 |
|------|------|------|------|
| 0 | 0 | 0 | 时钟空闲低电平，第一个边沿采样 |
| 1 | 0 | 1 | 时钟空闲低电平，第二个边沿采样 |
| 2 | 1 | 0 | 时钟空闲高电平，第一个边沿采样 |
| 3 | 1 | 1 | 时钟空闲高电平，第二个边沿采样 |

## 💡 常见 SPI 设备

| 设备类型 | SPI 模式 | 时钟频率 | 说明 |
|---------|---------|---------|------|
| SD 卡 | 0 | 25 MHz | 存储卡 |
| TFT 显示屏 | 0 | 10-20 MHz | ILI9341, ST7735 |
| 传感器 | 0-3 | 1-10 MHz | MPU6050, BME280 |
| Flash 存储器 | 0 | 10-50 MHz | W25Q64, AT25F |
| NRF24L01 | 0 | 8 MHz | 无线模块 |

## ⚙️ SPI 参数配置

### Server 默认参数

```python
spi.max_speed_hz = 1000000  # 1 MHz
spi.mode = 0                # SPI 模式 0
spi.bits_per_word = 8       # 8 位数据
```

### 自定义参数

可以在 Server 代码中修改 `init_spi()` 函数来调整 SPI 参数：

```python
def init_spi(self, spi_bus, device_address):
    self.spi = spidev.SpiDev()
    self.spi.open(spi_bus, device_address)
    
    # 自定义 SPI 参数
    self.spi.max_speed_hz = 5000000   # 5 MHz
    self.spi.mode = 3                 # SPI 模式 3
    self.spi.bits_per_word = 8        # 8 位
```

## 📝 代码注释说明

所有代码都包含详细的中文注释：

- **Server 端** (`spi_comm_server.py`):
  - SPI 总线初始化
  - 数据写入和读取
  - 异常处理

- **Client 端** (`spi_comm_client.py`):
  - 参数获取
  - Goal 发送
  - Feedback 和 Result 处理

## 🎯 总结

本项目演示了如何使用 ROS Action 和 spidev 库实现 SPI 通信功能。完整的代码注释便于学习和理解 SPI 通信原理和 ROS Action 框架的使用。

### 关键点

1. ✅ 使用 Action 框架实现 SPI 通信
2. ✅ 支持多总线多设备
3. ✅ 支持读写操作
4. ✅ 详细的错误处理
5. ✅ 资源自动清理

---

**作者**: Jetson Nano Developer  
**日期**: 2026-03-31  
**版本**: 1.0.0