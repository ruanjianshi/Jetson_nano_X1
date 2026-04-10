# Jetson Nano 硬件通信项目

这是一个基于 ROS 的 Jetson Nano 硬件通信项目，包含多个硬件接口的功能包。

## 📦 功能包列表

| 功能包 | 描述 | 硬件接口 | 状态 | 语言 |
|--------|------|----------|------|------|
| `my_action_pkg` | 基础硬件通信接口 | 串口/I2C/SPI/GPIO/PWM | ✅ 已完成 | Python/C++ |
| `maita_can_comm` | 脉塔智能 USB-CAN 通信 | USBCAN-II | ✅ 已完成 | Python/C++ |

## 🚀 快速开始

### 1. 安装依赖

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-serial \
    python3-smbus2 \
    python3-can \
    libusb-1.0-0 \
    ros-noetic-can-utils
```

### 2. 编译项目

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make
source devel/setup.bash
```

### 3. 使用示例

#### 脉塔智能 CAN 通信（C++ 版本，最高速率 1Mbps）

```bash
# 安装驱动库
sudo cp src/maita_can_comm/usbcan_ii_libusb_aarch64/libusbcan.so /lib/
sudo chmod 644 /lib/libusbcan.so

# 终端1: 启动 C++ Server（最高速率 1Mbps）
source devel/setup.bash
sudo rosrun maita_can_comm can_comm_maita_server_cpp

# 终端2: 发送 CAN 帧
source devel/setup.bash
python3 src/maita_can_comm/scripts/can_comm_client.py \
    _can_id:=0x123 \
    _data:="[0x01, 0x02, 0x03]" \
    _dlc:=3
```

#### 串口通信

```bash
# 终端1: 启动 Server
sudo roslaunch my_action_pkg serial_comm.launch

# 终端2: 发送数据
python3 src/my_action_pkg/scripts/serial_comm_client.py _data:="Hello"
```

#### I2C 通信

```bash
# 终端1: 启动 Server
sudo roslaunch my_action_pkg i2c_comm.launch

# 终端2: 读写 I2C 设备
python3 src/my_action_pkg/scripts/i2c_comm_client.py \
    _device_address:=0x50 \
    _register_address:=0x00 \
    _data:=0xAA
```

#### GPIO PWM 输出

```bash
# 终端1: 启动 Server
sudo roslaunch my_action_pkg pwm_output.launch

# 终端2: 控制 PWM 输出
python3 src/my_action_pkg/scripts/pwm_output_client.py \
    _pin_number:=12 \
    _frequency:=1000 \
    _duty_cycle:=50 \
    _duration:=5
```

## 📚 详细文档

- [脉塔智能 CAN 通信指南](src/maita_can_comm/README.md)
- [C++ CAN 通信指南](CPP_CAN_GUIDE.md) ⭐ C++ 版本（1Mbps）
- 串口通信: `src/my_action_pkg/SERIAL_COMM_README.md`
- I2C 通信: `src/my_action_pkg/I2C_COMM_README.md`
- GPIO 中断: `src/my_action_pkg/GPIO_INTERRUPT_README.md`
- GPIO PWM 输出: `src/my_action_pkg/PWM_OUTPUT_README.md`
- SPI 通信: `src/my_action_pkg/SPI_COMM_README.md`

## 📁 项目结构

```
action_ws/
├── src/
│   ├── my_action_pkg/          # 基础硬件通信
│   │   ├── action/             # Action 定义
│   │   ├── scripts/            # Python 脚本
│   │   └── launch/             # 启动文件
│   └── maita_can_comm/         # 脉塔智能 CAN 通信
│       ├── action/             # Action 定义
│       ├── scripts/            # Python 脚本
│       ├── launch/             # 启动文件
│       └── usbcan_ii_libusb_aarch64/  # 官方驱动
├── build/                      # 编译输出
├── devel/                      # 开发环境
└── install/                    # 安装目录
```

## 🎯 硬件支持

### 脉塔智能 USBCAN-II
- Vendor ID: 0471
- Product ID: 1200
- 设备类型: USBCAN-II (4)
- 双通道 CAN
- 波特率: 125K/250K/500K/1M
- **状态**: ✅ 已验证可用

### 基础硬件接口
- **串口**: /dev/ttyTHS1 (引脚 8, 10)
- **I2C**: /dev/i2c-1 (引脚 3, 5)
- **SPI**: SPI1 (引脚 19, 21, 23, 24, 26)
- **GPIO**: BCM 编号 (PWM: 12, 13)

## 🔧 系统要求

- Jetson Nano B01
- ROS Noetic
- Ubuntu 20.04 (Focal)
- Python 3.8+

## 📝 开发说明

所有功能包都使用 ROS Action 接口，支持以下模式：
- Goal/Result/Feedback 模式
- 异步通信
- 多客户端支持

## ⚠️ 注意事项

1. 所有 Server 都需要 **sudo** 权限
2. 脉塔智能 CAN 需要先安装 `libusbcan.so` 到 `/lib/` 目录
3. GPIO 引脚使用 **BCM 编号**
4. Jetson.GPIO 不支持软件上拉/下拉（需要硬件电阻）
5. PWM 支持引脚: 12, 13 (BCM)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👤 作者

Jetson Nano

## 📅 更新日期

2026-04-02