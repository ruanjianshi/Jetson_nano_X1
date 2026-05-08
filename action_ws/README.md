# Jetson Nano B01 — ROS1 综合项目

基于 ROS1 Noetic 的 Jetson Nano B01 (4GB) 硬件通信、电机控制、传感与视觉项目，支持 **PC 分布式通信**。

## 功能包列表

| 功能包 | 描述 | 语言 | 状态 |
|--------|------|------|------|
| `my_action_pkg` | 基础硬件 I/O：串口、I2C、SPI、GPIO、PWM | Python/C++ | ✅ |
| `mcp2515_can_driver` | MCP2515+TJA1050 SPI CAN 驱动 | Python | ✅ |
| `maita_can_comm` | 脉塔智能 USB-CAN-II 通信 | Python/C++ | ✅ |
| `yb_imu_driver` | 维特智能 IMU 驱动 (串口/I2C) | C++ | ✅ |
| `dcu_driver_pkg` | 智元 DCU + PowerFlow 电机驱动 (EtherCAT) | C++ | ✅ |
| `balance_control` | 轮足机器人平衡控制 (LQR/VMC/MPC/ADP) | Python | ✅ |
| `yolov11_pkg` | YOLOv11 目标检测 (Jetson 本地推理) | Python | ✅ |
| `opencv_cuda_pkg` | OpenCV CUDA 检测/跟踪/图像处理 | Python | ✅ |
| `sim2real_pkg` | Sim2Real 部署 (PT→ONNX, 强化学习推理) | Python | ✅ |
| `distributed_comm` | **PC ↔ Jetson 分布式通信桥接** | C++/Python | ✅ |

## 快速开始

### 1. 编译全部

```bash
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make
source devel/setup.bash
```

> 部分包编译耗时较长，可单独编译：
> ```bash
> catkin_make -DCATKIN_WHITELIST_PACKAGES="distributed_comm"
> ```

### 2. 硬件接口

```bash
# 串口
sudo rosrun my_action_pkg serial_comm_server

# I2C
sudo rosrun my_action_pkg i2c_comm_server

# SPI
sudo rosrun my_action_pkg spi_comm_server

# GPIO 中断
sudo rosrun my_action_pkg gpio_interrupt_server

# PWM 输出
sudo rosrun my_action_pkg pwm_output_server

# MCP2515 CAN
sudo roslaunch mcp2515_can_driver mcp2515_can.launch

# 脉塔 USB-CAN
sudo rosrun maita_can_comm can_comm_maita_server_cpp

# IMU
sudo rosrun yb_imu_driver imu_serial_server
```

### 3. PC 分布式通信

Jetson 与 PC 通过 WiFi 组成 ROS 分布式系统：

```bash
# Jetson（运行 roscore）
export ROS_IP=<Jetson_IP>
roscore &
rosrun distributed_comm jetson_bridge _pub_rate:=50

# PC（连接到 Jetson 的 roscore）
export ROS_MASTER_URI=http://<Jetson_IP>:11311
export ROS_IP=<PC_IP>
rosrun distributed_comm pc_bridge _pub_rate:=50
```

详细文档：[distributed_comm/README.md](src/distributed_comm/README.md)

### 4. 分布式 YOLO 推理

Jetson 摄像头 → WiFi → PC 推理 → 结果返回 Jetson：

```bash
# Jetson
roslaunch distributed_comm camera_bridge.launch

# PC（需 CUDA GPU + ultralytics）
roslaunch distributed_comm pc_yolo.launch device:=cuda:0
```

详细文档：[distributed_comm/test/README.md](src/distributed_comm/test/README.md)

## 硬件引脚映射

| 接口 | 设备路径 | GPIO 引脚 |
|------|----------|-----------|
| 串口 | `/dev/ttyTHS1` | 8 (TX), 10 (RX) |
| I2C-1 | `/dev/i2c-1` | 3 (SDA), 5 (SCL) |
| SPI1 | `/dev/spidev0.0` | 19,21,23,24,26 |
| PWM | BCM 12, 13 | 32, 33 |

## 项目结构

```
action_ws/
├── src/
│   ├── my_action_pkg/          # 基础硬件 I/O
│   ├── mcp2515_can_driver/     # SPI CAN 驱动
│   ├── maita_can_comm/         # USB-CAN 通信
│   ├── yb_imu_driver/          # IMU 驱动
│   ├── dcu_driver_pkg/         # EtherCAT 电机驱动
│   ├── balance_control/        # 平衡控制算法
│   ├── yolov11_pkg/            # YOLO 本地推理
│   ├── opencv_cuda_pkg/        # OpenCV 视觉
│   ├── sim2real_pkg/           # Sim2Real 部署
│   └── distributed_comm/       # PC-Jetson 分布式通信
│       ├── src/                # C++ 节点
│       ├── scripts/            # 工具脚本
│       ├── test/               # 分布式 YOLO 测试
│       └── model/              # YOLO 模型文件
├── build/
├── devel/
└── install/
```

## 系统要求

- Jetson Nano B01 (4GB)
- Ubuntu 20.04 + ROS1 Noetic
- Python 3.8+
- PC 端（分布式）：Ubuntu 20.04 + ROS1 Noetic + ultralytics

## 注意事项

1. 硬件 I/O Server 需要 `sudo` 权限
2. 脉塔 USB-CAN 需安装 `libusbcan.so` 到 `/lib/`
3. GPIO 使用 **BCM 编号**
4. PWM 仅支持 BCM 12 / 13
5. PC 无法连接 Jetson 时，Jetson 执行 `sudo ufw disable`
6. PC 编译只拷贝 `distributed_comm` 目录即可，无 Jetson 特有依赖

## 许可证

MIT License

## 作者

**作者**: Qi Xiao  
**邮箱**: 2408128687@qq.com

## 更新日期

2026-05-08
