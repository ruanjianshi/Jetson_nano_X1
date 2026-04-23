# Jetson Nano B01 机器人开发平台

> NVIDIA Jetson Nano B01 (4GB RAM, aarch64) 机器人开发平台，支持 AI 推理、电机控制、传感器融合等多种功能。

## 项目概述

本项目是一个完整的 Jetson Nano 机器人开发平台，集成了：

- **AI 推理**: YOLOv11 目标检测、PyTorch GPU 加速
- **电机控制**: EtherCAT DCU 驱动、MCP2515 CAN 总线
- **传感器驱动**: 九轴 IMU、摄像头、编码器
- **通信协议**: SPI、I2C、Serial、GPIO、CANFD
- **中间件**: ROS 1 Noetic Action 通信架构

## 硬件平台

| 组件 | 型号 | 说明 |
|------|------|------|
| 开发板 | NVIDIA Jetson Nano B01 | 4GB RAM, 128 CUDA cores |
| 处理器 | ARM Cortex-A57 (4核) | Maxwell GPU |
| 系统 | Ubuntu 20.04 + JetPack 4.6.2 | L4T 32.7.2 |
| 电源模式 | MAXN | 最大性能模式 |

## 目录结构

```
Jetson_Nano/
├── action_ws/                    # ROS 1 工作空间
│   └── src/
│       ├── yolov11_pkg/         # YOLOv11 GPU 推理包
│       ├── sim2real_pkg/        # PT→ONNX 转换 + 部署包
│       ├── dcu_driver_pkg/     # EtherCAT DCU 电机驱动
│       ├── mcp2515_can_driver/  # SPI-CAN 驱动 (MCP2515)
│       ├── yb_imu_driver/       # 九轴 IMU 驱动
│       ├── my_action_pkg/       # GPIO/I2C/Serial/SPI/PWM 示例
│       ├── opencv_cuda_pkg/    # OpenCV CUDA 处理
│       └── maita_can_comm/      # CAN 通信
├── ROS_Project/                  # 主 ROS 项目
├── ThreadPoolProject/           # C++ 多线程测试 (C++20)
├── data/                        # 数据存储
├── tests/                       # 测试文件
├── scripts/                      # 工具脚本
└── yolo11n.pt                   # YOLOv11 nano 模型
```

## 软件环境

### 深度学习框架

| 框架 | 版本 | GPU 支持 | 说明 |
|------|------|---------|------|
| **PyTorch** | 1.13.0 | ✅ CUDA 10.2 | 推荐用于生产环境 |
| **TorchVision** | 0.14.0 | ✅ 支持 | 配合 PyTorch 1.13 |
| **Ultralytics** | 8.4.33 | ✅ 支持 | YOLOv11 官方框架 |
| **TensorRT** | 8.2.1 | ✅ C API | Python bindings 仅支持 3.6 |
| **ONNX Runtime** | 1.19.2 | ⚠️ CPU only | aarch64 无 GPU 版本 |
| **TensorFlow** | 2.4.1 | ⚠️ CPU only | 不推荐 |

### 推理方案对比

| 方案 | 延迟 | 适用场景 |
|------|------|----------|
| **PyTorch GPU** | ~200-400ms (YOLOv8s) | ✅ 推荐生产环境 |
| **ONNX Runtime CPU** | ~1-2s (YOLOv8s) | 测试/调试 |
| **TensorRT** | <50ms (YOLOv8s) | 极致性能 (待完善) |

## 快速开始

### 1. 环境验证

```bash
# 验证 CUDA
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# 验证 YOLOv11
python3 -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# 系统监控
sudo jtop
```

### 2. 性能优化

```bash
# MAXN 模式 (最大性能)
sudo nvpmodel -m 0
sudo jetson_clocks

# 查看当前模式
sudo nvpmodel -q
```

### 3. ROS 工作空间

```bash
# 构建
cd action_ws && catkin_make

# 环境变量
source devel/setup.bash
```

---

## 功能包详解

### yolov11_pkg - YOLOv11 目标检测

**功能**: 基于 PyTorch GPU 的实时目标检测

**支持输入**:
- ROS Topic (`/camera/image_raw`)
- 图像文件 (`.jpg/.png`)
- USB/CSI 摄像头 (设备号)
- 视频文件 (`.mp4`)

**推理结果发布**:
- Topic: `/yolov11/inference_result` (sensor_msgs/Image)
- 包含检测框、类别、置信度、边界框坐标

**启动**:
```bash
# 服务器
roslaunch yolov11_pkg yolov11_inference_server.launch

# 客户端 - 图像推理
rosrun yolov11_pkg yolov11_inference_client.py \
    --type image_file --source img/dog.png --save result.jpg

# 客户端 - 摄像头推理
rosrun yolov11_pkg yolov11_inference_client.py \
    --type camera --source 0
```

---

### sim2real_pkg - 模型转换与部署

**功能**: PyTorch → ONNX 转换、ONNX Runtime 推理

**支持模型**:
- YOLO 系列
- 强化学习模型 (轮腿机器人等)

**模型转换**:
```bash
rosrun sim2real_pkg pt2onnx_converter.py \
    --mode pt2onnx --pt model.pt --type yolo --onnx model.onnx
```

**启动**:
```bash
# YOLO 推理
roslaunch sim2real_pkg sim2real.launch model_path:=models/yolo11n.onnx

# RL 模型推理
roslaunch sim2real_pkg rl_model.launch model_path:=models/jump_model.onnx
```

**性能测试结果** (jump_model.onnx):
- 推理延迟: 0.39ms (平均)
- 吞吐量: 2554 FPS
- 50Hz 连续推理: ✅ 稳定

---

### dcu_driver_pkg - EtherCAT DCU 电机驱动

**功能**: 通过 EtherCAT 控制智元 PowerFlow 执行器

**硬件架构**:
```
Jetson Nano (EtherCAT) → DCU (网关) → CANFD → PowerFlow 执行器
```

**支持的电机**:
| 型号 | 减速比 | 额定转矩 | CAN ID |
|------|--------|----------|--------|
| R86-2 | 16:1 | 20 Nm | 2, 3 |
| R52 | 36:1 | 6 Nm | 3, 5 |

**控制流程**:
```bash
# Step 1: 使能电机
rostopic pub /motor/command dcu_driver_pkg/MotorCommand \
    "{cmd: 1, motor_id: 3, channel: 1}" -1

# Step 2: 设置 MIT 模式
rostopic pub /motor/command dcu_driver_pkg/MotorCommand \
    "{cmd: 3, motor_id: 3, channel: 1, mode: 6}" -1

# Step 3: MIT 控制 (持续发送)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand \
    "{cmd: 4, motor_id: 3, channel: 1, q: 0.5, kp: 20.0, kd: 2.0}" -r 10
```

**启动**:
```bash
# 推荐配置 (关闭 DC 时钟)
roslaunch dcu_driver_pkg dcu_driver_server.launch \
    ethercat_if:=eth0 enable_dc:=false
```

**MIT 控制参数**:
| 参数 | 范围 | 说明 |
|------|------|------|
| q | ±6.283 rad | 目标位置 |
| dq | ±12.566 rad/s | 目标速度 |
| tau | ±100 Nm | 目标力矩 |
| kp | 0-500 | 刚度 (位置环增益) |
| kd | 0-8 | 阻尼 (速度环增益) |

---

### mcp2515_can_driver - SPI-CAN 驱动

**功能**: MCP2515 SPI 转 CAN 控制器驱动

**硬件连接**:
| Jetson Nano | MCP2515 | 说明 |
|-------------|---------|------|
| GPIO 10/MOSI0 | SI | 主出从入 |
| GPIO 9/MISO0 | SO | 主入从出 |
| GPIO 11/SCLK0 | SCK | 时钟 |
| GPIO 8/CE0 | CS | 片选 |
| GPIO 5 | INT | 中断 |

**波特率配置** (8MHz 晶振):
| 波特率 | 采样点 | 验证状态 |
|--------|--------|----------|
| 125 Kbps | 80% | ✅ |
| 250 Kbps | 80% | ✅ |
| **500 Kbps** | **80%** | ✅ **推荐** |
| 800 Kbps | 80% | ⚠️ 易丢失数据 |

**启动**:
```bash
rosrun mcp2515_can_driver mcp2515_can_server_cpp \
    _bitrate:=500000 _sampling_point:=80
```

**ROS Action 接口**:
```bash
# 发送 CAN 帧
rosservice call /mcp2515_can_comm "can_id: 0x601
data: [0x0B, 0x10, 0x60, 0x60, 0x00, 0x81, 0xE1, 0xC8]"
```

**硬件注意**:
- ⚠️ MCP2515 与 CAN 设备必须**共地**
- ⚠️ CAN 总线两端需 120Ω 终端电阻

---

### yb_imu_driver - 九轴 IMU 驱动

**功能**: 支持 I2C 和串口通信的九轴 IMU 驱动

**通信方式**:
| 方式 | 设备路径 | 典型速率 |
|------|----------|----------|
| I2C | /dev/i2c-1 | 400KHz |
| 串口 | /dev/ttyUSB0 | 115200 baud |

**发布话题**:
| 话题 | 类型 | 说明 |
|------|------|------|
| `/imu_serial/data` | sensor_msgs/Imu | 加速度、陀螺仪、四元数 |
| `/imu_serial/mag` | geometry_msgs/Vector3 | 磁力计 (uT) |
| `/imu_serial/temperature` | geometry_msgs/Vector3 | 高度、温度、气压 |

**启动**:
```bash
# 串口 + RViz 可视化
roslaunch yb_imu_driver imu_visualization.launch serial_port:=/dev/ttyUSB0

# I2C 方式
roslaunch yb_imu_driver imu_i2c.launch i2c_port:=7
```

**Action 操作**:
```bash
# 单次读取
rosrun yb_imu_driver imu_serial_client.py single

# IMU 校准
rosrun yb_imu_driver imu_serial_client.py calibrate

# 磁力计校准
rosrun yb_imu_driver imu_serial_client.py calibrate_mag

# 设置九轴融合
rosrun yb_imu_driver imu_serial_client.py algo9
```

---

### my_action_pkg - 硬件通信示例

**功能**: GPIO、I2C、Serial、SPI、PWM 的 ROS Action 示例

| Action 服务器 | 说明 | 硬件接口 |
|---------------|------|----------|
| SerialComm | 串口通信 | /dev/ttyTHS1 (115200 baud) |
| I2CComm | I2C 总线 | /dev/i2c-1 |
| GPIOInterrupt | GPIO 边沿检测 | Jetson.GPIO |
| PWMOutput | PWM 输出 | 硬件 PWM |
| SPIComm | SPI 通信 | spidev |

**启动**:
```bash
rosrun my_action_pkg serial_comm_server.py
rosrun my_action_pkg i2c_comm_server.py
rosrun my_action_pkg gpio_interrupt_server.py
rosrun my_action_pkg pwm_output_server.py
rosrun my_action_pkg spi_comm_server.py
```

---

### ThreadPoolProject - C++ 多线程测试

**功能**: C++ 多线程同步原语的教学测试

**测试模块**:
1. **线程管理**: 创建、ID、join、detach
2. **互斥锁**: basic、lock_guard、unique_lock、try_lock、recursive
3. **条件变量**: wait、notify、producer-consumer
4. **信号量**: counting、binary、try_acquire
5. **读写锁**: 多读者并发、独占写者
6. **线程局部存储**: thread_local 变量

**构建与运行**:
```bash
cd ThreadPoolProject && make all

# 交互式测试
make run

# 自动测试所有模块
make test

# 运行单个测试
echo "1" | ./build/multithread_test
```

---

## 性能基准

### YOLOv11 在 Jetson Nano 4GB

| 输入尺寸 | FPS | GPU 使用率 | 内存占用 |
|----------|-----|-----------|----------|
| 640x640 | ~12 | 85% | ~1.2GB |
| 416x416 | ~18 | 70% | ~0.9GB |
| 320x320 | ~25 | 55% | ~0.7GB |

**测试条件**: MAXN 模式, `sudo jetson_clocks`

### 系统延迟基准

| 任务 | 延迟 | 说明 |
|------|------|------|
| RL ONNX 推理 | 0.39ms | jump_model.onnx |
| CAN 帧发送 | ~1ms | MCP2515 @ 500Kbps |
| IMU 数据发布 | 20ms | 50Hz 采样 |

---

## 常见问题

### Q: TensorRT Python 无法导入?
A: TensorRT Python bindings 仅支持 Python 3.6，Jetson Nano 默认 3.8。可用 C API 或 `trtexec` 工具。

### Q: onnxruntime-gpu 无法安装?
A: aarch64 架构无官方预编译包。使用 PyTorch GPU 推理或 ONNX Runtime CPU 版本。

### Q: 内存不足 OOM?
A: 使用 yolo11n 模型，降低 `imgsz=416`，设置 `batch=1`。

### Q: CAN 通信失败?
A: 检查:
1. MCP2515 与 CAN 设备是否**共地**
2. CAN 总线两端 120Ω 终端电阻
3. 波特率与采样点设置一致

### Q: EtherCAT 通信不稳定?
A: 尝试关闭分布式时钟 (DC):
```bash
roslaunch dcu_driver_pkg dcu_driver_server.launch enable_dc:=false
```

---

## 开发指南

### 代码风格

**Python**:
- 4 空格缩进，PEP 8
- import 顺序: ROS → 标准库 → 第三方 → 本地
- 类型提示: Python 3.8+
- 日志: 使用 `rospy.loginfo/warn/err`

**C++**:
- 4 空格缩进
- 命名: PascalCase (类), camelCase (函数), snake_case (变量)
- 头文件: `#include "path.h"`

### 构建命令

```bash
# ROS 工作空间
cd action_ws && catkin_make

# C++ 项目
cd ThreadPoolProject && make all

# 清理
cd ThreadPoolProject && make clean
```

---

## 参考资源

- [NVIDIA Jetson Nano](https://developer.nvidia.com/embedded/jetson-nano)
- [Ultralytics YOLOv11](https://docs.ultralytics.com)
- [ROS Noetic 文档](http://wiki.ros.org/noetic)
- [智元 PowerFlow 执行器](https://www.agibot.com.cn/DOCS/PM/PFR)
- [SOEM EtherCAT Master](https://github.com/OpenEtherCATsociety/SOEM)

---

**最后更新**: 2026-04-23
**文档版本**: v1.0
