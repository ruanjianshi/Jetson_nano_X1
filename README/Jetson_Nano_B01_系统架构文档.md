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
- **TensorRT**: 8.2.1.8
- **VPI (Vision Programming Interface)**: 1.2.3
- **Vulkan**: 1.2.141
- **OpenCV**: 4.13.0 (带CUDA加速支持)
- **numpy**: 1.17.4

### 3.3 Python包
- **jetson-stats**: 4.3.2 ✅ (系统监控工具)
- **numpy**: 1.24.4 ✅ (已升级，支持YOLOv11)
- **PyTorch**: 1.13.0a0+git7c98e70 ✅ (支持CUDA 10.2，GPU加速可用)
- **TorchVision**: 0.14.0a0+5ce4506 ✅ (支持CUDA 10.2)
- **ultralytics**: 8.4.33 ✅ (YOLOv11框架，支持GPU推理)
- **TensorFlow**: ❌ (放弃GPU版本，依赖冲突)
- **tensorrt**: 通过TensorRT SDK支持
- **pyyaml**: 5.3.1 ✅

### 3.4 关键工具
- **jtop**: 4.3.2 ✅ (Jetson系统监控工具, 位于 /usr/local/bin/jtop)
- **JetPack**: NVIDIA边缘AI开发工具包 4.6.2
- **tegrastats**: GPU/CPU实时监控工具
- **nvcc**: NVIDIA CUDA编译器 V10.2.300

### 3.5 深度学习框架状态

| 框架 | 版本 | 安装状态 | GPU支持 | 推荐度 |
|------|------|----------|---------|--------|
| **PyTorch** | 1.13.0a0+git7c98e70 | ✅ 已安装 | ✅ CUDA可用 | ⭐⭐⭐⭐⭐ |
| **TorchVision** | 0.14.0a0+5ce4506 | ✅ 已安装 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **Ultralytics** | 8.4.33 | ✅ 已安装 | ✅ 支持 | ⭐⭐⭐⭐⭐ |
| **TensorRT** | 8.2.1.8 | SDK可用 | ✅ 支持 | ⭐⭐⭐⭐ |

**推荐**: 使用PyTorch + Ultralytics进行YOLOv11开发，GPU支持完美

---

## 4. 项目架构

### 4.1 目录结构
```
/home/jetson/Desktop/Jetson_Nano/
│
├── README/                                    # 项目文档目录
│   ├── Jetson_Nano_B01_系统架构文档.md         # 本文档
│   └── 项目架构详解.md                         # 详细的模块架构说明
│
├── src/                                       # 源代码目录 (Python)
│   ├── __init__.py                            # Python包初始化
│   ├── main.py                                # 主程序入口 (待创建)
│   ├── config/                                # 配置模块
│   │   ├── __init__.py
│   │   └── config.yaml                        # 主配置文件 (待创建)
│   ├── models/                                # AI模型目录 (模型文件待添加)
│   ├── utils/                                 # 工具模块
│   │   ├── __init__.py
│   │   ├── camera.py                          # 摄像头接口 (待创建)
│   │   ├── logger.py                          # 日志模块 (待创建)
│   │   └── hardware.py                        # 硬件接口 (待创建)
│   └── inference/                             # AI推理模块
│       └── __init__.py                        # 推理模块 (待创建)
│
├── data/                                      # 数据目录
│   ├── input/                                 # 输入数据 (原始图像、视频)
│   ├── output/                                # 输出结果 (推理结果、标注图像)
│   └── models/                                # 模型文件 (.onnx, .engine)
│
├── tests/                                     # 测试目录
│   ├── test_camera.py                         # 摄像头测试 (待创建)
│   ├── test_inference.py                      # 推理测试 (待创建)
│   └── test_hardware.py                       # 硬件测试 (待创建)
│
├── docs/                                      # 项目文档 (待添加)
│   ├── README.md                              # 项目概述
│   ├── API.md                                 # API参考
│   └── architecture.md                        # 架构决策记录
│
├── scripts/                                   # 脚本目录 (待添加)
│   ├── setup.sh                               # 环境安装脚本
│   └── run.sh                                 # 程序运行脚本
│
└── log/                                       # 日志目录 (运行时日志)
```

### 4.2 项目文件说明

#### 待创建的文件
| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `src/main.py` | Python | 主程序入口，初始化和协调所有模块 |
| `src/config/config.yaml` | YAML | 系统配置文件 (摄像头、模型、推理参数) |
| `src/utils/camera.py` | Python | 摄像头接口模块 (支持CSI/USB) |
| `src/utils/logger.py` | Python | 日志记录模块 (多级别日志) |
| `src/utils/hardware.py` | Python | 硬件接口 (GPIO、I2C、串口) |
| `src/inference/*.py` | Python | AI推理模块 (TensorRT加速) |
| `tests/*.py` | Python | 单元测试和集成测试 |
| `scripts/setup.sh` | Bash | 自动安装脚本 |
| `scripts/run.sh` | Bash | 程序运行脚本 |
| `requirements.txt` | 文本 | Python依赖包列表 |
| `setup.py` | Python | 项目安装配置 |
| `Makefile` | Makefile | 构建和管理任务 |

---

## 5. 模块说明

### 5.1 main.py
主程序入口，负责初始化和调度各模块

### 5.2 config/config.yaml
配置文件，包含：
- 摄像头参数
- 模型路径
- 推理参数
- 日志配置

### 5.3 utils/
- `camera.py`: CSI/USB摄像头接口封装
- `logger.py`: 日志记录模块
- `hardware.py`: Jetson硬件接口(GPIO, I2C等)

### 5.4 inference/
AI推理模块，支持TensorRT加速和YOLOv11

---

## 6. 常用命令

```bash
# YOLOv11推理
yolo predict model=yolo11n.pt source=image.jpg device=0  # GPU推理
yolo predict model=yolo11n.pt source=0 device=0         # 摄像头实时推理
yolo export model=yolo11n.pt format=onnx                # 导出ONNX格式

# 系统监控
sudo jtop

# 查看CUDA版本
nvcc --version

# 查看GPU状态
tegrastats

# 查看内存
free -h

# 查看磁盘
df -h
```

---

## 7. 开发环境配置

### 7.1 已安装的Python包
- **jetson-stats**: 4.3.2 ✅
- **numpy**: 1.24.4 ✅ (已升级)
- **opencv-python**: 4.13.0.92 ✅ (CUDA加速)
- **PyTorch**: 1.13.0a0+git7c98e70 ✅ (CUDA支持)
- **TorchVision**: 0.14.0a0+5ce4506 ✅ (CUDA支持)
- **ultralytics**: 8.4.33 ✅ (YOLOv11框架)
- **TensorFlow**: 2.4.1 ✅ (CPU模式)
- **tensorflow-estimator**: 2.4.0 ✅
- **protobuf**: 3.20.3 ✅
- **termcolor**: 2.0.0 ✅
- **wrapt**: 2.0.1 ✅
- **absl-py**: 0.15.0 ✅
- **flatbuffers**: 1.12 ✅
- **gast**: 0.3.3 ✅
- **opt-einsum**: 3.3.0 ✅
- **six**: 1.15.0 ✅
- **typing-extensions**: 3.7.4.3 ✅
- **pyyaml**: 5.3.1 ✅

### 7.2 可选安装的Python包
```txt
# 可选依赖
grpcio~=1.32.0       # TensorFlow RPC通信
tensorboard~=2.4     # TensorFlow可视化工具
pycuda>=2021.1       # CUDA Python绑定
onnx>=1.10.0        # ONNX模型支持
```

### 7.3 PyTorch安装验证
```bash
# 验证PyTorch
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU型号: {torch.cuda.get_device_name(0)}')"

# 验证TorchVision
python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')"

# PyTorch GPU测试
python3 << 'EOF'
import torch
x = torch.rand(1000, 1000).cuda()
y = torch.matmul(x, x)
print(f"GPU矩阵乘法成功: {y.shape}")
EOF
```

### 7.4 YOLOv11安装验证
```bash
# 验证Ultralytics (YOLOv11)
python3 -c "import ultralytics; print(f'Ultralytics版本: {ultralytics.__version__}')"

# 测试YOLOv11模型加载 (首次运行会自动下载yolo11n.pt)
python3 << 'EOF'
from ultralytics import YOLO
import torch

# 加载YOLOv11n轻量模型 (适合Jetson Nano 4GB内存)
model = YOLO('yolo11n.pt')
print(f'✅ YOLOv11n模型加载成功')

# 验证GPU加速
if torch.cuda.is_available():
    print(f'✅ GPU可用: {torch.cuda.get_device_name(0)}')
    # 运行测试推理
    import numpy as np
    dummy_input = np.zeros((1, 640, 640, 3), dtype=np.uint8)
    results = model.predict(dummy_input, device='cuda:0', verbose=False)
    print(f'✅ GPU推理测试成功')
else:
    print('⚠️ GPU不可用，使用CPU模式')
EOF
```

### 7.5 YOLOv11性能优化建议
- **模型选择**: 推荐使用yolo11n (nano)或yolo11s (small)以适应4GB内存
- **推理尺寸**: 默认640x640，可降低至416x416提升速度
- **批处理**: 单张图像推理，避免批处理导致内存不足
- **性能模式**: 运行前执行`sudo jetson_clocks`开启最大性能

# 注意：TensorFlow 2.4.1在Jetson Nano上的GPU检测可能有问题，但CPU模式正常工作
```

---

## 8. 系统电源模式

Jetson Nano支持多种电源模式，可通过以下命令切换：

| 模式 | CPU频率 | GPU频率 | 说明 |
|------|---------|---------|------|
| MAXN | 最高 | 最高 | 最大性能模式 (当前模式) |
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

# 应用电源模式后需要设置风扇速度
sudo jetson_clocks
```

---

## 9. 性能监控命令

| 命令 | 说明 |
|------|------|
| `sudo jtop` | 完整的系统监控界面 (推荐) |
| `tegrastats` | 实时GPU/CPU/内存使用率 |
| `jetson_release` | 显示系统版本信息 |
| `nvcc --version` | 显示CUDA编译器版本 |
| `free -h` | 显示内存使用情况 |
| `df -h` | 显示磁盘使用情况 |
| `nvpmodel -q` | 显示当前电源模式 |

---

**文档创建日期**: 2026-03-24
**设备ID**: Jetson-Nano-B01 (p3448-0002)
**最后更新**: 2026-04-02
**文档版本**: v5.0

### 安装历史
- **PyTorch**: 2026-03-24 (版本 1.13.0a0+git7c98e70)
- **OpenCV 4.13.0**: 2026-03-26 (版本 4.13.0 - CUDA/cuDNN加速)
- **Python环境恢复**: 2026-03-26 (版本 1.17.4 - 系统默认)
- **Ultralytics YOLOv11**: 2026-04-02 (版本 8.4.33 - YOLOv11框架)
- **NumPy升级**: 2026-04-02 (版本 1.24.4 - 支持YOLOv11)

### 重要说明
- **TensorFlow GPU版本已放弃**：依赖冲突导致系统环境破坏
- **推荐使用PyTorch + Ultralytics**：完美支持CUDA 10.2和cuDNN 8.2
- **OpenCV 4.13.0 CUDA版本已安装**：支持GPU加速图像处理
- **YOLOv11已就绪**：推荐使用yolo11n模型以适应4GB内存限制
