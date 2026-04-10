# SPI 通信 C++ 版本实现说明

## 📋 概述

本文档说明如何使用 C++ 实现的 SPI 通信功能。

## 🏗️ 文件结构

```
my_action_pkg/
├── action/
│   └── SPIComm.action           # SPI 通信 Action 定义
├── src/
│   ├── spi_comm_server.cpp    # SPI 通信服务器 (C++)
│   └── spi_comm_client.cpp    # SPI 通信客户端 (C++)
└── CMakeLists.txt               # 编译配置
```

## 📦 编译和运行

### 编译项目

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make
source install/setup.bash
```

### 运行 C++ 版本的 SPI 通信

#### Terminal 1: 启动 Server

```bash
source /home/jetson/Desktop/Jetson_Nano/action_ws/install/setup.bash
rosrun my_action_pkg spi_comm_server_cpp
```

#### Terminal 2: 启动 Client

```bash
source /home/jetson/Desktop/Jetson_Nano/action_ws/install/setup.bash

# 发送数据（写后读取）
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=true

# 只写入不读取
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=false
```

## 🔌 硬件连接

### SPI1 (对应 /dev/spidev0.0)

| 物理引脚 | GPIO | 功能 | 说明 |
|---------|------|------|------|
| **19** | GPIO 16 | **SPI_1_MOSI** | 主出从入 |
| **21** | GPIO 17 | **SPI_1_MISO** | 主入从出 |
| **23** | GPIO 18 | **SPI_1_SCK** | 时钟 |
| **24** | GPIO 19 | **SPI_1_CS0** | 片选 0 |
| **26** | GPIO 20 | **SPI_1_CS1** | 片选 1 |

**回环测试:** 短接 Pin 19 (MOSI) 和 Pin 21 (MISO)

## 💻 C++ 代码特点

### Server 端 (spi_comm_server.cpp)

#### 主要功能

1. **SPI 设备管理**
   - 打开/关闭 SPI 设备
   - 配置 SPI 参数（模式、时钟频率、数据位数）

2. **Action Server**
   - 接收客户端的 Goal
   - 执行 SPI 通信操作
   - 发送 Feedback
   - 返回 Result

#### 关键代码片段

**打开 SPI 设备:**
```cpp
int spi_fd_ = open("/dev/spidev0.0", O_RDWR);
if (spi_fd_ < 0) {
    ROS_ERROR("无法打开 SPI 设备");
    return false;
}
```

**配置 SPI 参数:**
```cpp
uint8_t mode = SPI_MODE_0;
uint8_t bits = 8;
uint32_t speed = 1000000;

ioctl(spi_fd_, SPI_IOC_WR_MODE, &mode);
ioctl(spi_fd_, SPI_IOC_WR_BITS_PER_WORD, &bits);
ioctl(spi_fd_, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
```

**SPI 传输:**
```cpp
struct spi_ioc_transfer tr = {
    .tx_buf = (unsigned long)&write_data,
    .rx_buf = (unsigned long)&received_data,
    .len = 1,
    .speed_hz = 1000000,
    .bits_per_word = 8,
};

ioctl(spi_fd_, SPI_IOC_MESSAGE(1), &tr);
```

### Client 端 (spi_comm_client.cpp)

#### 主要功能

1. **创建 Action Client**
   - 连接到 Action Server
   - 发送 Goal

2. **回调函数**
   - Feedback 回调：接收服务器的反馈信息
   - Done 回调：处理服务器返回的结果

#### 关键代码片段

**创建 Client:**
```cpp
actionlib::SimpleActionClient<my_action_pkg::SPICommAction> 
    client_("spi_comm", true);
client_.waitForServer();
```

**发送 Goal:**
```cpp
my_action_pkg::SPICommGoal goal;
goal.spi_bus = 0;
goal.device_address = 0;
goal.write_data = 0xAA;
goal.read_after_write = true;

client_.sendGoal(goal);
```

## 🎯 C++ vs Python 版本对比

| 特性 | Python 版本 | C++ 版本 |
|------|-----------|---------|
| **易用性** | ✅ 简单易用 | ⚠️ 需要编译 |
| **性能** | ⚠️ 一般 | ✅ 高性能 |
| **类型安全** | ❌ 弱类型 | ✅ 强类型 |
| **部署** | ✅ 无需编译 | ⚠️ 需要编译 |
| **依赖** | Python + spidev | C++ + ROS C++ 库 |

## 🚀 使用示例

### 示例 1: 写入数据

```cpp
// 发送数据 0xAA
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=false
```

### 示例 2: 写入并读取

```cpp
// 写入 0x90 并读取响应
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=0 \
    _device_address:=0 \
    _write_data:=0x90 \
    _read_after_write:=true
```

### 示例 3: 使用不同的 SPI 设备

```cpp
// 使用 /dev/spidev0.1 (CS1)
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=0 \
    _device_address:=1 \
    _write_data:=0xAA \
    _read_after_write:=true

// 使用 /dev/spidev1.0 (SPI2)
rosrun my_action_pkg spi_comm_client_cpp \
    _spi_bus:=1 \
    _device_address:=0 \
    _write_data:=0xAA \
    _read_after_write:=true
```

## 🔧 参数配置

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

## 🐛 故障排除

### 1. 编译错误

**问题**: 找不到 actionlib

**解决**: 确保已安装 ROS actionlib:
```bash
sudo apt install ros-noetic-actionlib
```

### 2. 链接错误

**问题**: undefined reference to `SPI_IOC_MESSAGE`

**解决**: 确保包含了正确的头文件:
```cpp
#include <linux/spi/spidev.h>
#include <sys/ioctl.h>
```

### 3. 运行时错误

**问题**: 无法打开 SPI 设备

**解决**: 使用 sudo 运行或修改设备权限:
```bash
sudo rosrun my_action_pkg spi_comm_server_cpp
```

## 📊 性能优势

C++ 版本相比 Python 版本有以下优势：

1. **更高的性能** - 直接系统调用，无 Python 解释器开销
2. **更好的实时性** - 更低的延迟
3. **更强的类型检查** - 编译时错误检测
4. **更小的内存占用** - 无 Python 运行时

## 🎯 最佳实践

### 1. 使用 C++ 版本的场景

- 需要高性能的实时应用
- 需要严格的类型安全
- 需要部署到生产环境
- 需要更低的延迟

### 2. 使用 Python 版本的场景

- 快速原型开发
- 脚本和测试
- 教学和学习
- 不需要高性能的应用

## 📝 总结

C++ 版本的 SPI 通信实现提供了：
- ✅ 高性能的 SPI 通信
- ✅ 完整的 Action 框架支持
- ✅ 详细的错误处理
- ✅ 易于集成到现有项目

**项目状态: ✅ 完成，Python 和 C++ 版本都已可用！**