# Jetson Nano B01 系统架构文档

## 1. 系统概述

- **设备型号**: NVIDIA Jetson Nano Developer Kit (P-Number: p3448-0002)
- **模块**: NVIDIA Jetson Nano module (16Gb eMMC)
- **内核版本**: Linux 4.9.253-tegra #1 SMP PREEMPT
- **CPU架构**: aarch64 (ARMv8)
- **操作系统**: Ubuntu 20.04.4 LTS (Focal Fossa)
- **JetPack版本**: 4.6.2 [L4T 32.7.2]
- **Python版本**: Python 3.8.10 (GCC 9.4.0)
- **pip版本**: 20.0.2
- **电源模式**: MAXN (最大性能模式)

---

## 2. 硬件规格

### 2.1 CPU
- **型号**: ARMv8 Processor rev 1 (v8l)
- **核心数**: 4核 (Quad-core ARM Cortex-A57)
- **BogoMIPS**: 38.40
- **特性**: fp, asimd, evtstrm, aes, pmull, sha1, sha2, crc32

### 2.2 GPU
- **型号**: NVIDIA Maxwell GPU
- **CUDA核心**: 128个
- **支持**: NVIDIA JetPack

### 2.3 内存
- **总内存**: 4GB LPDDR4
- **当前使用**: 约2.4GB
- **可用内存**: 约294MB
- **缓存/缓冲**: 约1.1GB
- **实际可用**: 约1.2GB

### 2.4 存储
- **主存储**: 58GB eMMC (/dev/mmcblk1p1)
- **已使用**: 23GB (42%)
- **可用空间**: 33GB
- **文件系统类型**: ext4

---

## 3. 软件环境

### 3.1 CUDA
- **版本**: CUDA 10.2
- **构建**: V10.2.300
- **发布日期**: 2021年2月28日

### 3.2 关键库
- **CUDA**: 10.2.300 (构建: V10.2.300, 发布: 2021-02-28)
- **cuDNN**: 8.2.1.32
- **TensorRT**: 8.2.1.8 (C API可用，Python bindings仅支持Python 3.6)
- **VPI (Vision Programming Interface)**: 1.2.3
- **Vulkan**: 1.2.141
- **OpenCV**: 4.13.0 (带CUDA加速支持)
- **numpy**: 1.24.4

### 3.3 Python包
| 包名 | 版本 | 状态 | 说明 |
|------|------|------|------|
| jetson-stats | 4.3.2 | ✅ | 系统监控工具 |
| numpy | 1.24.4 | ✅ | 已升级，支持YOLOv11 |
| PyTorch | 1.13.0a0+git7c98e70 | ✅ | CUDA 10.2, GPU加速可用 |
| TorchVision | 0.14.0a0+5ce4506 | ✅ | CUDA 10.2 支持 |
| ultralytics | 8.4.33 | ✅ | YOLOv11框架, GPU推理 |
| onnx | 1.10.0 | ✅ | ONNX模型支持 |
| onnxruntime | 1.19.2 | ✅ | ONNX推理(CPU only) |
| pycuda | 2026.1 | ✅ | CUDA Python绑定 |
| pyyaml | 5.3.1 | ✅ | YAML配置解析 |
| opencv-python | 4.13.0 | ✅ | CUDA加速 |
| TensorFlow | 2.4.1 | ⚠️ | CPU模式，GPU版本已放弃 |

### 3.4 关键工具
- **jtop**: 4.3.2 ✅ (Jetson系统监控工具)
- **JetPack**: NVIDIA边缘AI开发工具包 4.6.2
- **tegrastats**: GPU/CPU实时监控工具
- **nvcc**: NVIDIA CUDA编译器 V10.2.300

### 3.5 深度学习框架状态

| 框架 | 版本 | 安装状态 | GPU支持 | 推荐度 |
|------|------|----------|---------|--------|
| **PyTorch** | 1.13.0a0 | ✅ 已安装 | ✅ CUDA可用 | ⭐⭐⭐⭐⭐ |
| **TorchVision** | 0.14.0a0 | ✅ 已安装 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **Ultralytics** | 8.4.33 | ✅ 已安装 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **TensorRT** | 8.2.1.8 | ✅ SDK可用 | ✅ C API | ⭐⭐⭐⭐ |
| **ONNX Runtime** | 1.19.2 | ✅ 已安装 | ⚠️ CPU only | ⭐⭐⭐ |

**推荐**: 使用PyTorch + Ultralytics进行YOLOv11开发，GPU支持完美

---

## 4. ROS工作空间

### 4.1 action_ws (ROS 1 工作空间)

```
action_ws/
├── src/
│   ├── yolov11_pkg/          # YOLOv11 PyTorch GPU推理包
│   ├── sim2real_pkg/         # PT→ONNX转换 + 强化学习部署包
│   ├── mcp2515_can_driver/   # CAN总线驱动
│   ├── opencv_cuda_pkg/      # OpenCV CUDA处理
│   ├── yb_imu_driver/        # IMU驱动
│   └── my_action_pkg/         # ROS Action示例
├── build/                    # 构建空间
└── devel/                    # 开发空间
```

### 4.2 项目包说明

#### yolov11_pkg
YOLOv11 目标检测推理包，使用 PyTorch GPU 推理。

| 功能 | 状态 |
|------|------|
| PyTorch GPU 推理 | ✅ |
| ROS Action 接口 | ✅ |
| 实时摄像头推理 | ✅ |
| 视频/图像文件推理 | ✅ |

#### sim2real_pkg
Sim2Real 部署包，支持模型格式转换和推理。

| 功能 | 状态 | 说明 |
|------|------|------|
| YOLO PT→ONNX | ✅ | 使用ultralytics导出 |
| RL PT→ONNX | ✅ | 支持自定义模型 |
| ONNX→TensorRT | ⏳ | pycuda已安装，待实现 |
| ONNX Runtime推理 | ✅ | CPU版本已安装 |
| PyTorch GPU推理 | ✅ | 复用yolov11_pkg |

---

## 5. 推理方案对比

### 5.1 方案对比表

| 方案 | 依赖 | 性能 | 适用场景 |
|------|------|------|----------|
| **PyTorch GPU** | PyTorch + CUDA | YOLOv8s ~200-400ms | ✅ 推荐，生产环境 |
| **ONNX Runtime CPU** | onnxruntime 1.19.2 | YOLOv8s ~1-2s | 测试/调试阶段 |
| **TensorRT** | TensorRT SDK + pycuda | YOLOv8s <50ms | 极致优化(待完善) |

### 5.2 推理后端选择建议

1. **快速部署/调试**: 使用 `yolov11_pkg` (PyTorch GPU)
2. **ONNX格式验证**: 使用 `sim2real_pkg` + ONNX Runtime CPU
3. **极致性能**: TensorRT (需要后续完善Python bindings)

### 5.3 模型转换工作流

```
训练环境 (PC)              Jetson Nano
     │                          │
     │  导出 .pt                 │
     ▼                          │
  .pt ──────────────────────────►│
     │                          │
     │  pt2onnx_converter        │
     ▼                          ▼
  .onnx ───────────────────────►│
     │                          │
     │  ONNX Runtime CPU测试     │  (当前可用)
     ▼                          ▼
  验证通过                       │
                                 │
     │  (可选) TensorRT优化      │  (待实现)
     ▼                          ▼
  .engine ◄──────────────────────│
     │                          │
     ▼                          ▼
  极致性能推理                   │
```

---

## 6. 项目架构

### 6.1 目录结构
```
/home/jetson/Desktop/Jetson_Nano/
│
├── README/                                    # 项目文档目录
│   ├── Jetson_Nano_B01_系统架构文档.md         # 本文档
│   └── 项目架构详解.md                         # 详细的模块架构说明
│
├── action_ws/                                 # ROS 1 工作空间
│   ├── src/
│   │   ├── yolov11_pkg/                      # YOLOv11 推理包
│   │   ├── sim2real_pkg/                     # 模型转换/部署包
│   │   ├── mcp2515_can_driver/                # CAN驱动
│   │   ├── opencv_cuda_pkg/                  # OpenCV CUDA
│   │   ├── yb_imu_driver/                     # IMU驱动
│   │   └── my_action_pkg/                    # Action示例
│   ├── build/
│   └── devel/
│
├── ROS_Project/                              # 主ROS项目
│   ├── src/                                   # 源代码
│   ├── config/                                # 配置
│   ├── launch/                                # 启动文件
│   ├── scripts/                               # 脚本
│   └── docs/                                  # 文档
│
├── ThreadPoolProject/                         # C++ CMake项目
├── data/                                      # 数据目录
├── tests/                                     # 测试目录
├── scripts/                                   # 工具脚本
└── log/                                       # 日志目录
```

---

## 7. 常用命令

### 7.1 YOLO推理命令

```bash
# PyTorch GPU推理 (yolov11_pkg)
source action_ws/devel/setup.bash
rosrun yolov11_pkg yolov11_inference_server.py

# 摄像头实时推理
roslaunch yolov11_pkg yolov11_camera.launch

# 模型转换 (sim2real_pkg)
source action_ws/devel/setup.bash

# PT -> ONNX
rosrun sim2real_pkg pt2onnx_converter.py \
    --mode pt2onnx \
    --pt /path/to/model.pt \
    --type yolo

# ONNX -> TensorRT (待完善)
rosrun sim2real_pkg pt2onnx_converter.py \
    --mode onnx2trt \
    --onnx /path/to/model.onnx \
    --engine /path/to/model.engine
```

### 7.2 系统监控命令

```bash
# 完整系统监控 (推荐)
sudo jtop

# GPU状态
tegrastats

# CUDA版本
nvcc --version

# 内存
free -h

# 磁盘
df -h

# 电源模式
sudo nvpmodel -q
```

---

## 8. 开发环境配置

### 8.1 已安装的Python包

| 包名 | 版本 | 说明 |
|------|------|------|
| jetson-stats | 4.3.2 | 系统监控 |
| numpy | 1.24.4 | 数值计算 |
| opencv-python | 4.13.0 | CUDA加速 |
| PyTorch | 1.13.0a0 | CUDA 10.2 |
| TorchVision | 0.14.0a0 | CUDA支持 |
| ultralytics | 8.4.33 | YOLOv11 |
| onnx | 1.10.0 | ONNX支持 |
| onnxruntime | 1.19.2 | ONNX推理(CPU) |
| pycuda | 2026.1 | CUDA Python绑定 |
| pyyaml | 5.3.1 | 配置解析 |
| protobuf | 3.20.3 | ONNX依赖 |
| TensorFlow | 2.4.1 | CPU模式 |

### 8.2 安装命令

```bash
# PyTorch验证
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"

# Ultralytics验证
python3 -c "from ultralytics import YOLO; print('Ultralytics OK')"

# ONNX Runtime验证
python3 -c "import onnxruntime as ort; print(f'ONNX Runtime: {ort.__version__}')"

# pycuda验证
python3 -c "import pycuda.driver as cuda; cuda.init(); print(f'GPU: {cuda.Device(0).name()}')"
```

---

## 9. 系统电源模式

| 模式 | CPU频率 | GPU频率 | 说明 |
|------|---------|---------|------|
| MAXN | 最高 | 最高 | 最大性能模式 (当前) |
| 15W | 1479MHz | 921MHz | 15W模式 |
| 10W | 918MHz | 640MHz | 10W模式 |
| 5W | 918MHz | 640MHz | 5W模式 |

```bash
# 切换电源模式
sudo nvpmodel -m 0  # MAXN模式
sudo nvpmodel -m 1  # 15W模式
sudo nvpmodel -m 2  # 10W模式

# 查看当前模式
sudo nvpmodel -q

# 应用风扇和时钟设置
sudo jetson_clocks
```

---

## 10. 性能优化建议

### 10.1 YOLOv11优化
- **模型选择**: yolo11n (nano) 适合4GB内存
- **推理尺寸**: 640x640 可降至 416x416 提升速度
- **批处理**: 单张推理，避免OOM
- **性能模式**: 运行前 `sudo jetson_clocks`

### 10.2 内存优化
- 使用轻量模型 (yolo11n)
- 降低输入分辨率
- 避免同时运行多个推理进程
- 定期监控内存使用 `free -h`

### 10.3 TensorRT加速 (待完善)
```bash
# TensorRT引擎构建 (需要pycuda + TensorRT Python)
# 当前C库可用，Python bindings仅支持Python 3.6
```

---

## 11. 常见问题

### Q: onnxruntime-gpu无法安装?
A: aarch64架构无官方预编译包，使用CPU版本或PyTorch GPU推理

### Q: TensorRT Python无法导入?
A: TensorRT Python bindings仅支持Python 3.6，Jetson Nano默认Python 3.8。可用C API或等待社区支持

### Q: 内存不足 OOM?
A: 使用yolo11n模型，降低输入分辨率，避免批处理

### Q: 推理速度慢?
A: 启用MAXN模式 `sudo nvpmodel -m 0 && sudo jetson_clocks`

---

**文档创建日期**: 2026-03-24
**设备ID**: Jetson-Nano-B01 (p3448-0002)
**最后更新**: 2026-04-10
**文档版本**: v6.0

### 安装历史
- **PyTorch**: 2026-03-24 (版本 1.13.0a0+git7c98e70)
- **OpenCV 4.13.0**: 2026-03-26 (CUDA/cuDNN加速)
- **Ultralytics YOLOv11**: 2026-04-02 (版本 8.4.33)
- **NumPy升级**: 2026-04-02 (版本 1.24.4)
- **pycuda**: 2026-04-10 (版本 2026.1)
- **onnxruntime**: 2026-04-10 (版本 1.19.2, CPU版)
- **onnx**: 2026-04-10 (版本 1.10.0)

### 重要说明
- **推荐使用PyTorch + Ultralytics**: GPU加速完美，YOLOv11直接推理
- **ONNX Runtime**: aarch64无GPU版本，CPU推理较慢
- **TensorRT**: C库可用，Python bindings待社区支持
- **sim2real_pkg**: PT→ONNX转换工具，可配合yolov11_pkg使用
