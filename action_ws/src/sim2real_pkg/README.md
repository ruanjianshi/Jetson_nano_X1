# sim2real_pkg

Sim2Real 部署包 - 用于将 PyTorch 模型转换为 ONNX 格式，并在 Jetson Nano B01 上进行部署推理。

## 功能特性

- **PT → ONNX 转换**: 将 YOLO / 强化学习模型的 `.pt` 文件转换为 ONNX 格式
- **YOLO 推理**: ONNX Runtime CPU 目标检测推理
- **强化学习推理**: 轮腿机器人 RL 模型 ONNX 推理
- **TensorRT 支持**: 框架已搭建，待 Python bindings 支持

## 包结构

```
sim2real_pkg/
├── scripts/
│   ├── rl_inference/              # 轮腿强化学习推理
│   │   ├── rl_onnx_inference.py   # RL ONNX 推理节点 (ROS)
│   │   ├── tensorrt_rl_inference.py  # TensorRT 推理 (待完善)
│   │   └── rl_model_sim_test.py  # RL 模型模拟测试 (独立脚本)
│   │
│   ├── yolo_inference/            # YOLO 推理
│   │   └── onnx_inference.py     # YOLO ONNX 推理 (ROS)
│   │
│   └── tools/                    # 工具
│       └── pt2onnx_converter.py  # PT -> ONNX 转换工具
│
├── msg/                          # ROS 消息
│   ├── DetectionResult.msg
│   └── ModelInfo.msg
│
├── action/                       # ROS Action
│   └── ONNXInference.action
│
├── launch/                       # 启动文件
│   ├── sim2real.launch           # YOLO 推理启动
│   └── rl_model.launch           # RL 模型推理启动
│
├── config/                       # 配置文件
│   └── default_config.yaml
│
└── models/                      # 模型文件目录
    ├── jump_model.onnx           # 轮腿 RL 模型
    └── yolo11n.onnx             # YOLO 模型
```

## 快速开始

### 1. 轮腿强化学习模型

**模型信息:**
- 输入: observations [1, 174] float32
- 输出: actions [1, 6] float32

**独立测试 (无需 ROS):**
```bash
source action_ws/devel/setup.bash

python3 -m sim2real_pkg.rl_inference.rl_model_sim_test --test all
# 或直接运行
python3 action_ws/src/sim2real_pkg/scripts/rl_inference/rl_model_sim_test.py --test all
```

**ROS 节点运行:**
```bash
source action_ws/devel/setup.bash

roslaunch sim2real_pkg rl_model.launch model_path:=models/jump_model.onnx
```

### 2. YOLO 模型

**PT -> ONNX 转换:**
```bash
source action_ws/devel/setup.bash

rosrun sim2real_pkg pt2onnx_converter.py \
    --mode pt2onnx \
    --pt /path/to/yolo11n.pt \
    --type yolo \
    --onnx models/yolo11n.onnx
```

**ROS 节点运行:**
```bash
source action_ws/devel/setup.bash

roslaunch sim2real_pkg sim2real.launch \
    model_path:=models/yolo11n.onnx \
    model_type:=yolo
```

## 脚本说明

### 轮腿强化学习 (rl_inference/)

| 脚本 | 类型 | 说明 |
|------|------|------|
| `rl_model_sim_test.py` | 独立脚本 | RL 模型模拟测试，无需 ROS |
| `rl_onnx_inference.py` | ROS 节点 | RL ONNX 推理 ROS 节点 |
| `tensorrt_rl_inference.py` | 框架 | TensorRT 推理 (待完善) |

### YOLO 推理 (yolo_inference/)

| 脚本 | 类型 | 说明 |
|------|------|------|
| `onnx_inference.py` | ROS 节点 | YOLO ONNX 推理 |

### 工具 (tools/)

| 脚本 | 说明 |
|------|------|
| `pt2onnx_converter.py` | PT -> ONNX 转换，支持 YOLO 和 RL 模型 |

## launch 文件

| launch | 说明 | 启动命令 |
|--------|------|----------|
| `rl_model.launch` | 轮腿 RL 模型推理 | `roslaunch sim2real_pkg rl_model.launch` |
| `sim2real.launch` | YOLO ONNX 推理 | `roslaunch sim2real_pkg sim2real.launch` |

### launch 参数

**rl_model.launch:**
```bash
roslaunch sim2real_pkg rl_model.launch \
    model_path:=models/jump_model.onnx \
    inference_rate:=50.0
```

**sim2real.launch:**
```bash
roslaunch sim2real_pkg sim2real.launch \
    model_path:=models/yolo11n.onnx \
    model_type:=yolo \
    backend:=onnxruntime
```

## 命令行参数

### pt2onnx_converter.py

```bash
rosrun sim2real_pkg pt2onnx_converter.py [options]

选项:
  --mode MODE              转换模式: pt2onnx, onnx2trt (default: pt2onnx)
  --pt PATH               PyTorch 模型路径 (.pt)
  --onnx PATH             ONNX 模型路径
  --type TYPE             模型类型: yolo, rl (default: yolo)
  --imgsz SIZE            YOLO 输入尺寸 (default: 640)
  --input_shape SHAPE     RL 模型输入形状，如: 1,3,64,64
  --fp16                  启用 FP16 (default: True)
  --workspace SIZE         TensorRT 工作空间 GB (default: 4)
```

### rl_model_sim_test.py

```bash
python3 action_ws/src/sim2real_pkg/scripts/rl_inference/rl_model_sim_test.py [options]

选项:
  --model PATH            模型路径 (default: models/jump_model.onnx)
  --test TYPE             测试类型: all, random, latency, continuous
  --iterations N          迭代次数 (default: 100)
  --interval MS           连续测试间隔 ms (default: 20.0)
```

## 推理方案对比

| 方案 | 依赖 | 性能 | 适用场景 |
|------|------|------|----------|
| **PyTorch GPU** | PyTorch + CUDA | YOLOv8s ~200-400ms | ✅ 推荐生产环境 |
| **ONNX Runtime CPU** | onnxruntime 1.19.2 | YOLOv8s ~1-2s | 测试/调试阶段 |
| **TensorRT** | TensorRT SDK + pycuda | YOLOv8s <50ms | 极致优化(待完善) |

## 性能测试结果

**RL 模型 (jump_model.onnx) - ONNX Runtime CPU:**
| 指标 | 值 |
|------|------|
| 推理延迟 (Mean) | 0.39ms |
| 延迟 P95 | 0.56ms |
| 吞吐量 | 2554 FPS |
| 50Hz 连续推理 | ✅ 稳定达成 |

## 系统要求

- ROS Noetic
- Python 3.8+
- CUDA 10.2 / cuDNN 8.2.1 / TensorRT 8.2.1
- PyTorch 1.13+
- Ultralytics 8.4.33
- onnxruntime 1.19.2
- pycuda 2026.1

## 已安装依赖

```bash
pip3 list | grep -E "onnx|onnxruntime|pycuda|ultralytics|torch"

# 预期输出:
# onnx                         1.10.0
# onnxruntime                   1.19.2
# pycuda                        2026.1
# ultralytics                   8.4.33
# torch                         1.13.0a0+git7c98e70
```

## 与 yolov11_pkg 协同

| 包 | 功能 | 推理后端 |
|----|------|----------|
| `yolov11_pkg` | YOLO 推理 | PyTorch GPU (推荐) |
| `sim2real_pkg` | 模型转换 + ONNX 推理 | ONNX Runtime CPU |

```bash
# 1. 转换 YOLO 模型为 ONNX
rosrun sim2real_pkg pt2onnx_converter.py --mode pt2onnx --pt your_model.pt --type yolo

# 2. yolov11_pkg 使用 PyTorch GPU 推理 (推荐)
rosrun yolov11_pkg yolov11_inference_server.py

# 或使用 sim2real_pkg ONNX 推理 (CPU，较慢)
roslaunch sim2real_pkg sim2real.launch model_path:=models/your_model.onnx
```

## 常见问题

**Q: TensorRT Python 无法导入?**
A: TensorRT Python bindings 仅支持 Python 3.6，Jetson Nano 默认 Python 3.8。C 库可用，可使用 trtexec 工具构建引擎。

**Q: onnxruntime-gpu 无法安装?**
A: aarch64 架构无官方预编译包，使用 CPU 版本或 PyTorch GPU 推理。

**Q: 内存不足 OOM?**
A: 使用 yolo11n 模型，降低输入分辨率，避免批处理。

## License

MIT
