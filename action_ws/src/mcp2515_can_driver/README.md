# MCP2515 SPI转CAN驱动

## 概述

基于 MCP2515 SPI转CAN控制器 (Microchip) 和 TJA1050 CAN收发器的 ROS 功能包，通过 SPI 接口实现 CAN 总线通信。

## 硬件连接

### Jetson Nano SPI0 接口 (实际验证)

| Jetson Nano 引脚 | GPIO | 功能 | MCP2515 |
|-----------------|------|------|---------|
| 19 | GPIO 10/MOSI0 | MOSI 主出从入 | SI |
| 21 | GPIO 9/MISO0 | MISO 主入从出 | SO |
| 23 | GPIO 11/SCLK0 | SCLK 时钟 | SCK |
| 24 | GPIO 8/CE0 | 片选 0 | CS |
| 29 | GPIO 5 | 中断输入 | INT |

**重要**: MCP2515 INT 中断引脚连接到 GPIO 5 (Pin 29)

### 硬件框图

```
Jetson Nano              MCP2515              TJA1050              CAN Bus
+---------+            +-------+            +-------+           +-------+
|         |    SPI     |       |    CAN     |       |   CANH/L  |       |
| SPI0    |----------->|  SPI  |----------->| CAN   |==========>|  CAN  |
|         |            |   to   |            | Trans |           | Device|
+---------+            |  CAN   |            | ceiver|           +-------+
                        +-------+            +-------+
```

### MCP2515 芯片特性

- SPI 接口的 CAN 控制器 (Microchip)
- 支持 CAN 2.0A (11-bit ID) 和 CAN 2.0B (29-bit ID)
- 支持标准帧和扩展帧
- 支持远程帧和数据帧
- 最高 1Mbps 波特率
- **8MHz 外部晶振**

### TJA1050 芯片特性

- 高速 CAN 收发器
- 支持最高 1Mbps 波特率
- 内置静音模式

## 文件结构

```
mcp2515_can_driver/
├── action/
│   └── MCP2515CANComm.action    # Action 定义
├── include/
│   └── mcp2515_driver.h          # MCP2515 驱动类头文件
├── src/
│   ├── mcp2515_driver.cpp        # MCP2515 驱动实现
│   ├── mcp2515_can_server.cpp    # C++ Action Server
│   └── mcp2515_can_client.cpp    # C++ Action Client
├── scripts/
│   ├── mcp2515_can_server.py     # Python 服务器 (已不推荐)
│   └── mcp2515_can_client.py     # Python 客户端
├── launch/
│   └── mcp2515_can.launch       # 启动文件
├── test/
│   └── track_receive_500.py    # Python 独立测试脚本
├── CMakeLists.txt
└── package.xml
```

## C++ 版本说明 (推荐)

本驱动提供 **C++ 版本** (推荐) 和 Python 版本。C++ 版本性能更好、延迟更低。

### 架构设计

```
MCP2515Driver (底层驱动类)
    ├── SPI 通信 (spidev)
    ├── MCP2515 寄存器操作
    ├── CAN 帧发送/接收
    └── RX 接收线程

MCP2515CANServer (ROS Action Server)
    ├── 继承 MCP2515Driver
    ├── ROS Action 接口
    ├── 接收回调处理
    └── 日志输出
```

### 核心类说明

#### MCP2515Driver (include/mcp2515_driver.h)

| 方法 | 说明 |
|------|------|
| `connect()` | 连接 SPI 设备 |
| `disconnect()` | 断开 SPI 连接 |
| `initialize()` | 初始化 MCP2515 |
| `reset()` | 软件复位 MCP2515 |
| `sendCanFrame()` | 发送 CAN 帧 |
| `receiveCanFrame()` | 接收 CAN 帧 |
| `setReceiveCallback()` | 设置接收回调函数 |
| `startRxThread()` | 启动 RX 接收线程 |
| `stopRxThread()` | 停止 RX 接收线程 |

### C++ 构建与运行

```bash
cd ~/Desktop/Jetson_Nano/action_ws

# 完整构建工作空间
catkin_make

# 激活环境
source devel/setup.bash
```

### C++ 服务器运行

**基础运行 (500Kbps, 80%采样点)**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80
```

**完整参数运行**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp \
    _spi_bus:=0 \
    _spi_device:=0 \
    _bitrate:=500000 \
    _sampling_point:=80 \
    _enable_rx_thread:=true \
    _enable_echo:=true
```

### C++ 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `spi_bus` | int | 0 | SPI 总线编号 |
| `spi_device` | int | 0 | SPI 设备编号 |
| `bitrate` | int | 500000 | CAN 波特率 |
| `sampling_point` | int | 80 | 采样点百分比 (70/80) |
| `enable_rx_thread` | bool | true | 启用独立接收线程 |
| `enable_echo` | bool | true | 打印收发日志 |

### C++ 客户端示例

```cpp
#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <mcp2515_can_driver/MCP2515CANCommAction.h>

int main(int argc, char** argv)
{
    ros::init(argc, argv, "can_client_cpp");
    ros::NodeHandle nh;

    actionlib::SimpleActionClient<mcp2515_can_driver::MCP2515CANCommAction>
        client("mcp2515_can_comm", true);

    ROS_INFO("等待服务器...");
    client.waitForServer();

    mcp2515_can_driver::MCP2515CANCommGoal goal;
    goal.can_id = 0x601;
    goal.dlc = 8;
    goal.data = {0x0B, 0x10, 0x60, 0x60, 0x00, 0x81, 0xE1, 0xC8};
    goal.extended = false;
    goal.remote = false;

    ROS_INFO("发送 CAN 帧 ID=0x601");
    client.sendGoal(goal);

    client.waitForResult(ros::Duration(5.0));

    if (client.getResult()->success) {
        ROS_INFO("成功: %s", client.getResult()->message.c_str());
    } else {
        ROS_WARN("失败: %s", client.getResult()->message.c_str());
    }

    return 0;
}
```

### C++ 编译注意事项

- 使用 `catkin_make` 编译整个工作空间
- 可执行文件位于: `devel/lib/mcp2515_can_driver/mcp2515_can_server_cpp`
- 如需单独编译: `catkin_make -DCATKIN_WHITELIST_PACKAGES=mcp2515_can_driver`

## 构建与安装

### C++ 版本 (推荐)

```bash
cd ~/Desktop/Jetson_Nano/action_ws

# 构建工作空间
catkin_make

# 激活环境
source devel/setup.bash
```

> **提示**: C++ 版本是推荐的生产版本，性能更好。

## 运行

### C++ 版本 (推荐)

**正常模式**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80
```

**环回测试模式**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80 _loopback_test:=true
```

### Launch 文件方式 (Python 版本)

```bash
roslaunch mcp2515_can_driver mcp2515_can.launch
```

**注意**: 环回测试模式下，发送的帧会被 MCP2515 自身接收，用于验证 TX/RX 路径是否正常工作。

### 自定义参数

```bash
roslaunch mcp2515_can_driver mcp2515_can.launch \
    spi_bus:=0 \
    spi_device:=0 \
    bitrate:=500000 \
    enable_echo:=true \
    loopback_test:=false
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `spi_bus` | int | 0 | SPI 总线编号 (0=SPI0, 1=SPI1) |
| `spi_device` | int | 0 | SPI 设备编号 (0=CE0, 1=CE1) |
| `bitrate` | int | 500000 | CAN 波特率 (125000/250000/500000/1000000) |
| `enable_rx_thread` | bool | true | 启用接收线程 |
| `enable_echo` | bool | true | 打印收发日志 |
| `loopback_test` | bool | false | 启用环回测试模式 |

## ROS Action 接口

### Action 名称

```
mcp2515_can_comm
```

### Goal 定义

```yaml
uint32 can_id                  # CAN ID (11-bit 标准 或 29-bit 扩展)
uint8 dlc                      # 数据长度 (0-8)
uint8[8] data                  # CAN 数据
bool extended                  # 扩展帧标志 (true=29-bit, false=11-bit)
bool remote                    # 远程帧标志
---
bool success                   # 操作是否成功
string message                 # 状态消息
uint8[8] received_data         # 接收到的数据
uint32 received_id             # 接收到的 CAN ID
uint8 received_dlc             # 接收到的 DLC
---
string status                  # 状态描述
```

### Python 客户端示例

```python
#!/usr/bin/env python3
import rospy
import actionlib
from mcp2515_can_driver.msg import MCP2515CANCommAction, MCP2515CANCommGoal

client = actionlib.SimpleActionClient('mcp2515_can_comm', MCP2515CANCommAction)
client.wait_for_server()

goal = MCP2515CANCommGoal()
goal.can_id = 0x123
goal.dlc = 4
goal.data = [0x11, 0x22, 0x33, 0x44, 0, 0, 0, 0]
goal.extended = False
goal.remote = False

client.send_goal(goal)
client.wait_for_result(rospy.Duration(5.0))
result = client.get_result()

print(f"Success: {result.success}, Message: {result.message}")
```

## MCP2515 寄存器映射

| 寄存器 | 地址 | 说明 |
|--------|------|------|
| CANSTAT | 0x0E | CAN 状态寄存器 |
| CANCTRL | 0x0F | CAN 控制寄存器 |
| CNF1 | 0x2A | 波特率配置 1 |
| CNF2 | 0x29 | 波特率配置 2 |
| CNF3 | 0x28 | 波特率配置 3 |
| CANINTF | 0x2C | 中断标志寄存器 |
| EFLG | 0x2D | 错误标志寄存器 |
| TXB0CTRL | 0x30 | 发送缓冲器 0 控制 |
| TXB0SIDH | 0x31 | 发送缓冲器 0 标准 ID 高位 |
| TXB0SIDL | 0x32 | 发送缓冲器 0 标准 ID 低位 |
| TXB0DLC | 0x35 | 发送缓冲器 0 数据长度 |
| TXB0D0-D7 | 0x36-0x3D | 发送缓冲器 0 数据 |
| RXB0CTRL | 0x60 | 接收缓冲器 0 控制 |
| RXB0SIDH | 0x61 | 接收缓冲器 0 标准 ID 高位 |
| RXB0SIDL | 0x62 | 接收缓冲器 0 标准 ID 低位 |
| RXB0DLC | 0x65 | 接收缓冲器 0 数据长度 |
| RXB0D0-D7 | 0x66-0x6D | 接收缓冲器 0 数据 |

## MCP2515 位定时原理

### Time Quantum (时间量子) 计算

MCP2515 使用 Time Quantum (TQ) 作为基本时间单元：

```
TQ = 2 × (BRP + 1) / Fosc
```

其中 Fosc 是晶振频率。

### CAN 位时间结构

每个 CAN 位时间由以下段组成：

```
+---------+----------+----------+---------+
| Sync_Seg| Prop_Seg | PhSeg1   | PhSeg2  |
+---------+----------+----------+---------+
1 TQ       1-8 TQ    1-8 TQ     1-8 TQ
          (PRSEG)    (PHSEG1)   (PHSEG2)
          <-------- 采样点位置 -------->
```

- **Sync_Seg**: 同步段 (固定 1 TQ)
- **Prop_Seg**: 传播段 (PRSEG + 1 TQ, 范围 1-8 TQ)
- **PhSeg1**: 相位段1 (PHSEG1 + 1 TQ, 范围 1-8 TQ)
- **PhSeg2**: 相位段2 (PHSEG2 + 1 TQ, 范围 1-8 TQ)

**采样点** = (Prop_Seg + PhSeg1) / (总 TQ 数)

### CNF 寄存器字段说明

#### CNF1 (0x2A) - 波特率配置 1

| Bit 7-6 | Bit 5-0 |
|---------|---------|
| SJW[1:0] (同步跳转宽度) | BRP[5:0] (波特率预分频) |

- **SJW**: 同步跳转宽度，用于重新同步 (范围 1-4 TQ)
- **BRP**: 波特率预分频，决定 TQ 长度 (范围 0-63)

#### CNF2 (0x29) - 波特率配置 2

| Bit 7 | Bit 6 | Bit 5-3 | Bit 2-0 |
|-------|-------|---------|---------|
| BTLMODE | SAM | PHSEG1[2:0] | PRSEG[2:0] |

- **BTLMODE**: 1=PhSeg2 由 PHSEG2[2:0] 设置; 0=PhSeg2 = 2×PHSEG1
- **SAM**: 1=三次采样; 0=单次采样
- **PHSEG1**: 相位段1长度 = PHSEG1 + 1 TQ
- **PRSEG**: 传播段时间 = PRSEG + 1 TQ

#### CNF3 (0x28) - 波特率配置 3

| Bit 7-3 | Bit 2-0 |
|---------|---------|
| 保留 | PHSEG2[2:0] |

- **PHSEG2**: 相位段2长度 = PHSEG2 + 1 TQ (当 BTLMODE=1)

### 计算示例: 8MHz 晶振, 500Kbps, 80% 采样点

```
目标: 500Kbps = 1/500000 = 2000ns per bit
晶振: 8MHz => TQ = 2 × (0+1) / 8MHz = 250ns
所需 TQ 数: 2000ns / 250ns = 8 TQ

采样点 80% => 采样在 8 × 0.8 = 6.4 TQ 位置

配置方案 (BTLMODE=1):
- Sync_Seg: 1 TQ
- Prop_Seg: 1 TQ (PRSEG=0)
- PhSeg1: 4 TQ (PHSEG1=3)
- PhSeg2: 2 TQ (PHSEG2=1)

实际采样点: (1+4) / 8 = 62.5% (理论)
实际波特率: 1 / (8 × 250ns) = 500Kbps ✓
```

## 支持的晶振频率

本驱动默认支持 **8MHz 晶振**。

**重要限制**: MCP2515 的 PHSEG2 最小值为 2 TQ，导致 8MHz 晶振下最高只能达到 **800Kbps**（而非 1Mbps）。

| 晶振频率 | 支持状态 | 实际最高速率 | 说明 |
|---------|---------|-------------|------|
| 8MHz | ✅ 默认 | **800Kbps** | 受限于 PHSEG2 最小值 2TQ |
| 16MHz | ⚙️ 可修改 | 1 Mbps | BRP=1 时 TQ=250ns，可满足 1Mbps |
| 20MHz | ⚙️ 可修改 | 1 Mbps | BRP=1 时 TQ=200ns，可满足 1Mbps |

### 8MHz 晶振最高速率计算

```
8MHz 晶振:
  TQ = 2 × (BRP+1) / Fosc = 2 × 1 / 8MHz = 250ns

最小位时间 (BTLMODE=1):
  Sync_Seg = 1 TQ (固定)
  Prop_Seg = 1 TQ (最小, PRSEG=0)
  PhSeg1   = 1 TQ (最小, PHSEG1=0)
  PhSeg2   = 2 TQ (最小, PHSEG2[2:0]=0 实际是 2TQ)
  ------------------------
  总计     = 5 TQ

最高速率 = 1 / (5 × 250ns) = 800Kbps
```

### 不同晶振的 TQ 计算

| 晶振 | BRP=0 | BRP=1 | BRP=3 | 最高速率 |
|------|-------|-------|-------|----------|
| 8MHz | 250ns | 500ns | 1000ns | 800Kbps |
| 16MHz | 125ns | 250ns | 500ns | 1Mbps |
| 20MHz | 100ns | 200ns | 400ns | 1Mbps |

## 波特率配置表 (8MHz晶振)

### 配置索引说明

| 采样点范围 | 索引范围 | 包含速率 |
|-----------|---------|----------|
| 80% | 0-3 | 125K, 250K, 500K, **800K** (高速) |
| 70% | 4-6 | 125K, 250K, 500K |
| <70% | 7-9 | 125K, 250K, 500K |

> **注意**: 800Kbps **仅支持 80% 采样点**，不支持其他采样点设置。

### 完整配置表

#### 125Kbps

| 采样点 | CNF1 | CNF2 | CNF3 | 启动参数 |
|--------|------|------|------|----------|
| 80% | 0x03 | 0x90 | 0x02 | `_bitrate:=125000 _sampling_point:=80` |
| 70% | 0x03 | 0x98 | 0x01 | `_bitrate:=125000 _sampling_point:=70` |
| <70% | 0x03 | 0xAC | 0x03 | `_bitrate:=125000 _sampling_point:=60` |

#### 250Kbps

| 采样点 | CNF1 | CNF2 | CNF3 | 启动参数 |
|--------|------|------|------|----------|
| 80% | 0x01 | 0x90 | 0x02 | `_bitrate:=250000 _sampling_point:=80` |
| 70% | 0x01 | 0x98 | 0x01 | `_bitrate:=250000 _sampling_point:=70` |
| <70% | 0x01 | 0xAC | 0x03 | `_bitrate:=250000 _sampling_point:=60` |

#### 500Kbps (最常用)

| 采样点 | CNF1 | CNF2 | CNF3 | 启动参数 | 实测结果 |
|--------|------|------|------|----------|----------|
| 80% | 0x00 | 0x90 | 0x02 | `_bitrate:=500000 _sampling_point:=80` | ✅ **已验证通过** |
| 70% | 0x00 | 0x98 | 0x01 | `_bitrate:=500000 _sampling_point:=70` |  ✅ **已验证通过** |
| <70% | 0x00 | 0xAC | 0x03 | `_bitrate:=500000 _sampling_point:=60` | 未测试 |

#### 800Kbps (8MHz最高速率) ⚠️

| 采样点 | CNF1 | CNF2 | CNF3 | 启动参数 | 说明 |
|--------|------|------|------|----------|------|
| 80% | 0x00 | 0x80 | 0x01 | `_bitrate:=800000 _sampling_point:=80` | 5TQ = 1+1+1+2，**仅此采样点可用** |

**⚠️ 高速警告**:
- 800Kbps 是 8MHz 晶振的最高速率
- 仅支持 80% 采样点
- **容易产生数据丢失**，尤其在长总线或干扰环境下
- 建议尽可能使用 **500Kbps** 以获得更好的稳定性

#### 1Mbps (需16MHz或20MHz晶振)

8MHz 晶振**无法**达到 1Mbps，需要使用 16MHz 或 20MHz 晶振。

### CNF 寄存器值详解

```
CNF1 = 0x00:  BRP=0 (TQ=250ns@8MHz), SJW=1
CNF1 = 0x01:  BRP=1 (TQ=500ns@8MHz), SJW=1
CNF1 = 0x03:  BRP=3 (TQ=1000ns@8MHz), SJW=1

CNF2 = 0x80:  BTLMODE=1, PHSEG1=0(1TQ), PRSEG=0(1TQ)
CNF2 = 0x90:  BTLMODE=1, PHSEG1=2(3TQ), PRSEG=0(1TQ)
CNF2 = 0x98:  BTLMODE=1, PHSEG1=3(4TQ), PRSEG=0(1TQ)
CNF2 = 0xAC:  BTLMODE=1, PHSEG1=5(6TQ), PRSEG=0(1TQ)

CNF3 = 0x01:  PHSEG2=1(2TQ) [PHSEG2[2:0]=0 表示 2TQ!]
CNF3 = 0x02:  PHSEG2=2(3TQ)
CNF3 = 0x03:  PHSEG2=3(4TQ)
```

### 采样点计算

采样点 (%) = (Prop_Seg + PhSeg1) / (总 TQ) × 100%

| CNF2 | CNF3 | Prop_Seg | PhSeg1 | PhSeg2 | 总 TQ | 采样点 | 实际速率@8MHz |
|------|------|----------|--------|--------|-------|--------|-------------|
| 0x80 | 0x01 | 1 | 1 | 2 | 5 | 40% | 800Kbps |
| 0x90 | 0x02 | 1 | 3 | 2 | 7 | 57% | 571Kbps |
| 0x98 | 0x01 | 1 | 4 | 2 | 8 | 62.5% | 500Kbps |
| 0xAC | 0x03 | 1 | 6 | 3 | 11 | 64% | 364Kbps |

**注意**: PHSEG2[2:0]=0 实际代表 2TQ（MCP2515 最小要求），因此总 TQ 数比预期大 1。

## 启动参数示例

**500Kbps, 80% 采样点**(本驱动验证通过):
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80
```

**500Kbps, 70% 采样点** (本驱动验证通过):
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=70
```

**250Kbps, 80% 采样点**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=250000 _sampling_point:=80
```

**800Kbps (8MHz最高速率)**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=800000 _sampling_point:=80
```

## 采样点选择指南

| 应用场景 | 推荐采样点 | 原因 |
|---------|-----------|------|
| 短总线 (<1m) | 80% | 信号质量好，需要快速采样 |
| 标准 CAN 分析仪 | 80% | 兼容性好 |
| 长总线 (>1m) | 70% | 更多时间用于信号稳定 |
| 干扰环境 | 70% | 更强的抗干扰能力 |
| **高速 (800Kbps)** | ⚠️ 80% | 8MHz最高速率，**易丢失数据** |

### ⚠️ 高速警告

| 速率 | 稳定性 | 推荐程度 | 原因 |
|------|--------|---------|------|
| 125Kbps | 最高 | ✅ 极力推荐 | 抗干扰能力强 |
| 250Kbps | 高 | ✅ 推荐 | 平衡速度与稳定性 |
| 500Kbps | 中等 | ✅ **推荐** | 最常用的CAN速率，已验证通过 |
| 800Kbps | 较低 | ⚠️ 慎用 | 8MHz最高速率，**易产生数据丢失** |

**建议**: 除非有特殊需求，优先使用 **500Kbps**。

**重要**: 采样点设置必须与 CAN 总线上所有设备一致，否则会导致通信错误。

## 模式说明

| 模式 | 值 | 说明 |
|------|-----|------|
| NORMAL | 0x00 | 正常模式 |
| SLEEP | 0x01 | 睡眠模式 |
| LOOPBACK | 0x02 | 环回模式 |
| LISTEN_ONLY | 0x03 | 只听模式 |
| CONFIG | 0x04 | 配置模式 |

## SPI 配置

- SPI 模式: 0 (CPOL=0, CPHA=0)
- 时钟频率: 1MHz (稳定可靠)
- 数据位宽: 8 bits
- 片选: 软件控制 (CE0)

## SPI 指令集

| 指令 | 值 | 说明 |
|------|-----|------|
| RESET | 0xC0 | 软件复位 |
| READ | 0x03 | 读取寄存器 |
| WRITE | 0x02 | 写入寄存器 |
| BIT_MODIFY | 0x05 | 位修改 |
| READ_STATUS | 0xA0 | 读取状态 |
| RX_STATUS | 0xB0 | 读取 RX 状态 |
| RTS | 0x80 | 请求发送 |
| RTS_0 | 0x81 | 请求发送 TX0 |

## 测试

### 推荐测试流程 (C++ 版本)

**第一步: 验证 MCP2515 SPI 通信**

使用 Python 脚本进行独立测试（不依赖 ROS）:
```bash
cd ~/Desktop/Jetson_Nano/action_ws/src/mcp2515_can_driver/test
python3 track_receive_500.py
```

**第二步: 验证环回模式 (C++)**

```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80 _loopback_test:=true
```

**第三步: 连接真实 CAN 设备测试 (C++)**

```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80
```

### 环回测试 (C++)

环回测试用于验证 MCP2515 的 TX/RX 路径是否正常：

```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80 _loopback_test:=true
```

**预期结果**:
- MCP2515 进入环回模式 (CANSTAT=0x40)
- 发送成功后能接收到相同 ID 的帧
- 显示 "回环测试通过"

### 正常 CAN 总线测试 (C++)

```bash
# 启动 C++ 驱动
rosrun mcp2515_can_driver mcp2515_can_server_cpp _bitrate:=500000 _sampling_point:=80

# 使用 C++ 客户端发送测试帧
rosrun mcp2515_can_driver mcp2515_can_client_cpp
```

## 硬件Setup要求 (重要!)

### ⚠️ 共地问题 (Common Ground)

**这是最容易忽略的问题！**

CAN 总线通信双方必须有共同的参考地电位。如果 MCP2515 模块和 CAN 设备（如 CAN 分析仪）没有共地，会导致：
- 数据完全接收不到
- 数据部分正确、部分错误
- 偶发性通信失败

**解决方法**: 将 MCP2515 模块的 GND 与 CAN 分析仪/其他 CAN 设备的 GND 连接在一起。

```
Jetson Nano (GND) ←────→ MCP2515 模块 (GND)
                              ↑
                         必须连接!
                              ↓
Jetson Nano (GND) ←────→ CAN 分析仪 (GND)
```

### ⚠️ 终端电阻匹配 (120Ω Termination)

CAN 总线是差分信号，需要在总线两端安装 **120Ω 终端电阻** 来吸收信号反射。

- **每根 CAN 总线需要 2 个 120Ω 终端电阻**（分别位于总线两端）
- 如果缺少终端电阻，会导致信号反射，引起通信错误
- 很多 MCP2515 模块自带 120Ω 电阻（可通过模块上的电阻跳线选择）

**检查方法**:
```bash
# 使用万用表测量 CANH 和 CANL 之间的电阻
# 正常值应为约 60Ω（两个120Ω电阻并联）
# 如果是 120Ω，说明一端缺少终端电阻
# 如果是无穷大，说明完全没有终端电阻
```

### 完整硬件连接检查清单

- [ ] MCP2515 模块与 Jetson Nano SPI0 连接正确 (MOSI/MISO/SCK/CS)
- [ ] MCP2515 INT 引脚连接到 GPIO 5 (Pin 29)
- [ ] MCP2515 模块 GND 与 CAN 设备 GND **共地**
- [ ] CAN 总线两端各有 120Ω 终端电阻
- [ ] CANH 接 CANH，CANL 接 CANL（没有接反）
- [ ] 所有设备供电正常

## 注意事项

1. **权限**: 访问 `/dev/spidev*` 需要足够权限
2. **波特率**: 确保 CAN 总线上所有设备波特率一致
3. **终端电阻**: CAN 总线两端需安装 120Ω 终端电阻
4. **硬件连接**: 确保 MOSI/MISO/SCK/CS 连接正确
5. **时钟频率**: MCP2515 使用 8MHz 外部晶振
6. **GPIO 中断**: INT 引脚连接到 GPIO 5 (Pin 29)
7. **共地**: MCP2515 与 CAN 设备必须共地

## 常见问题

### 发送超时 (❌ 发送超时!)

可能原因:
1. **缺少共地** - MCP2515 与 CAN 设备没有共同参考地
2. CAN 总线连接问题 (H/L 接反或未连接)
3. 缺少终端电阻 (120Ω)
4. 其他 CAN 设备干扰
5. MCP2515 未正确初始化

解决方法:
1. **首先检查共地！** 确保 MCP2515 GND 与 CAN 设备 GND 相连
2. 检查 CAN 总线 wiring
3. 添加终端电阻（120Ω 两端）
4. 使用环回模式验证硬件

### 数据接收错误 (数据与发送不一致)

可能原因:
1. **缺少共地** - 导致数据信号采样错误
2. **采样点不匹配** - CAN 设备与 MCP2515 采样点设置不同
3. SPI 通信速率过高

解决方法:
1. 确保共地连接
2. 尝试修改 `_sampling_point` 参数 (70% / 80%)
3. 将 SPI 速度降低到 1MHz

### SPI 设备不存在

```bash
# 检查 SPI 设备
ls -la /dev/spidev*

# 启用 SPI0 ( Jetson Nano 默认已启用)
# 如需启用 SPI1:
sudo vi /boot/config.txt
# 添加: dtparam=spi1=on
```

### 权限不足

```bash
# 使用 sudo 运行
sudo roslaunch mcp2515_can_driver mcp2515_can.launch
```

### 导入模块失败

```bash
# 重新构建
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make
source devel/setup.bash
```

## 调试日志

### C++ 版本关键日志

```
OK: SPI connection established: /dev/spidev0.0 @ 1MHz
Initializing MCP2515 (8MHz crystal)...
OK: Baudrate 500000 bps configured
    CNF1=0x0 CNF2=0x90 CNF3=0x2
OK: Initialization complete, CANSTAT=0x0, mode=0
OK: MCP2515 CAN Action Server started
OK: RX thread started
========================================
[1775797253.712] CAN帧接收
----------------------------------------
  ID类型: STD  CAN ID: 0x601
  帧类型: DATA  DLC: 8 bytes
  数据: [0x0b, 0x10, 0x60, 0x60, 0x00, 0x81, 0xe1, 0xc8]
```

### 关键日志信息

| 日志 | 说明 |
|------|------|
| `OK: SPI connection established` | SPI 通信正常 |
| `OK: Baudrate ... configured` | MCP2515 波特率配置成功 |
| `OK: Initialization complete` | MCP2515 初始化完成 |
| `CAN帧接收` | 收到 CAN 帧 |
| `ERROR: Send timeout` | 发送超时 |
| `ERROR: CNF2 write failed` | 寄存器写入失败 |

## License

MIT
