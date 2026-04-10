# OpenCV CUDA 包

基于 OpenCV 的图像处理和目标检测包，支持 CUDA 加速，专为 Jetson Nano 优化。

## 功能特性

- 🚀 支持 CUDA GPU 加速
- 🎯 基于 ROS Action 通信机制
- 📊 实时图像处理和目标检测
- 💾 支持多种输入：ROS 话题、图像文件、摄像头、视频文件
- 🎬 图像处理操作：resize、crop、rotate、blur、canny、threshold、color_convert
- 🔍 目标检测：Haar Cascade、HOG、DNN

## 项目结构

```
opencv_cuda_pkg/
├── action/                      # Action 定义
│   ├── ImageProcessing.action   # 图像处理 Action
│   └── OpenCVDetection.action   # 目标检测 Action
├── msg/                         # 消息定义
│   └── DetectionResult.msg      # 检测结果消息
├── models/                      # 模型文件
│   ├── haarcascade_eye.xml      # 眼睛检测模型
│   ├── haarcascade_frontalface_default.xml  # 人脸检测模型
│   └── README.md                # 模型文档
├── scripts/                     # 主要脚本
│   ├── image_processing_server.py    # 图像处理服务器
│   ├── image_processing_client.py    # 图像处理客户端
│   ├── opencv_detection_server.py    # 目标检测服务器
│   └── opencv_detection_client.py    # 目标检测客户端
├── launch/                      # 启动文件
│   ├── image_processing_server.launch
│   └── opencv_detection_server.launch
├── test/                        # 测试文件
│   ├── img/                     # 测试图片
│   │   └── dog.png
│   ├── result/                  # 测试结果
│   └── scripts/                 # 测试脚本
│       ├── test_processing.py   # 图像处理测试
│       ├── test_all.sh          # 批量图像处理测试
│       └── test_detection.sh    # 目标检测测试
├── CMakeLists.txt               # 编译配置
├── package.xml                  # 包配置
└── README.md                    # 本文档
```

## 编译

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make -DCATKIN_WHITELIST_PACKAGES=opencv_cuda_pkg
source devel/setup.bash
```

---

## 图像处理

### Action 定义

#### Goal
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `input_type` | string | - | 输入类型: `topic`, `image_file`, `camera`, `video_file` |
| `input_source` | string | - | 输入源 |
| `operation` | string | - | 操作类型 |
| `params` | string | - | 操作参数（JSON 格式） |
| `use_cuda` | bool | True | 是否使用 CUDA 加速 |
| `publish_processed` | bool | True | 是否发布处理后的图像 |

#### Result
| 参数 | 类型 | 描述 |
|------|------|------|
| `success` | bool | 是否成功 |
| `message` | string | 结果消息 |
| `processing_time` | float64 | 处理时间（秒） |
| `output_info` | string | 输出信息 |

#### Feedback
| 参数 | 类型 | 描述 |
|------|------|------|
| `frame_count` | int32 | 已处理的帧数 |
| `fps` | float64 | 当前帧率 |
| `status` | string | 状态信息 |

### 启动服务器

```bash
roslaunch opencv_cuda_pkg image_processing_server.launch
```

### 使用客户端

#### 1. 调整图像大小
```bash
rosrun opencv_cuda_pkg image_processing_client.py \
  --type image_file \
  --source test/img/dog.png \
  --operation resize \
  --params '{"width": 640, "height": 480}'
```

#### 2. 边缘检测（Canny）
```bash
rosrun opencv_cuda_pkg image_processing_client.py \
  --type image_file \
  --source test/img/dog.png \
  --operation canny \
  --params '{"threshold1": 50, "threshold2": 150}'
```

#### 3. 高斯模糊
```bash
rosrun opencv_cuda_pkg image_processing_client.py \
  --type image_file \
  --source test/img/dog.png \
  --operation gaussian_blur \
  --params '{"ksize": 15, "sigma": 0}'
```

#### 4. 摄像头实时处理
```bash
rosrun opencv_cuda_pkg image_processing_client.py \
  --type camera \
  --source 0 \
  --operation gaussian_blur \
  --params '{"ksize": 15, "sigma": 0}'
```

### 运行测试脚本

```bash
# 批量测试所有图像处理操作
cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/test/scripts
./test_all.sh
```

### 支持的操作

| 操作 | 参数 | 描述 |
|------|------|------|
| `resize` | `width`, `height` | 调整图像大小 |
| `crop` | `x`, `y`, `width`, `height` | 裁剪图像 |
| `rotate` | `angle` | 旋转图像 |
| `blur` | `ksize` | 均值模糊 |
| `gaussian_blur` | `ksize`, `sigma` | 高斯模糊 |
| `canny` | `threshold1`, `threshold2` | 边缘检测 |
| `threshold` | `threshold`, `max_value` | 二值化 |
| `color_convert` | `conversion` | 颜色空间转换 |

---

## 目标检测

### Action 定义

#### Goal
| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `input_type` | string | - | 输入类型 |
| `input_source` | string | - | 输入源 |
| `detection_method` | string | - | 检测方法: `haar_cascade`, `hog`, `dnn` |
| `model_path` | string | - | DNN 模型路径 |
| `cascade_path` | string | - | Cascade 文件路径 |
| `confidence_threshold` | float64 | 0.5 | 置信度阈值 |
| `nms_threshold` | float64 | 0.4 | NMS 阈值 |
| `use_cuda` | bool | True | 是否使用 CUDA 加速 |
| `publish_processed` | bool | True | 是否发布处理后的图像 |

#### Result
| 参数 | 类型 | 描述 |
|------|------|------|
| `num_detections` | int32 | 检测到的目标数量 |
| `inference_time` | float64 | 推理时间（秒） |
| `detections` | DetectionResult[] | 检测结果列表 |
| `frames_processed` | int32 | 处理的帧数 |
| `avg_inference_time` | float64 | 平均推理时间 |

### 启动检测服务器

```bash
roslaunch opencv_cuda_pkg opencv_detection_server.launch
```

### 使用客户端

#### 1. HOG 行人检测
```bash
rosrun opencv_cuda_pkg opencv_detection_client.py \
  --type image_file \
  --source test/img/dog.png \
  --method hog
```

#### 2. Haar Cascade 人脸检测
```bash
rosrun opencv_cuda_pkg opencv_detection_client.py \
  --type image_file \
  --source test/img/dog.png \
  --method haar_cascade \
  --cascade models/haarcascade_frontalface_default.xml
```

#### 3. 摄像头实时检测
```bash
rosrun opencv_cuda_pkg opencv_detection_client.py \
  --type camera \
  --source 0 \
  --method hog
```

### 运行测试脚本

```bash
# 批量测试目标检测
cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/test/scripts
./test_detection.sh
```

### 支持的检测方法

| 方法 | 用途 | 模型文件 |
|------|------|----------|
| `hog` | 行人检测 | 内置（无需文件）|
| `haar_cascade` | 人脸检测 | 需要指定 cascade 文件 |
| `dnn` | 多目标检测 | 需要 pre-trained 模型 |

---

## 输出话题

### /opencv/processed_image
- **类型**: `sensor_msgs/Image`
- **描述**: 处理后的图像

### /opencv/detection_result
- **类型**: `sensor_msgs/Image`
- **描述**: 带检测框的图像

---

## Python API

### 图像处理客户端

```python
import actionlib
from opencv_cuda_pkg.msg import ImageProcessingGoal, ImageProcessingAction
import json

client = actionlib.SimpleActionClient('image_processing', ImageProcessingAction)
client.wait_for_server()

goal = ImageProcessingGoal()
goal.input_type = 'image_file'
goal.input_source = '/path/to/image.jpg'
goal.operation = 'resize'
goal.params = json.dumps({'width': 640, 'height': 480})
goal.use_cuda = True
goal.publish_processed = True

client.send_goal(goal)
client.wait_for_result()

result = client.get_result()

if result.success:
    print(f"处理成功: {result.message}")
    print(f"处理时间: {result.processing_time:.3f}s")
```

### 目标检测客户端

```python
import actionlib
from opencv_cuda_pkg.msg import OpenCVDetectionGoal, OpenCVDetectionAction

client = actionlib.SimpleActionClient('opencv_detection', OpenCVDetectionAction)
client.wait_for_server()

goal = OpenCVDetectionGoal()
goal.input_type = 'image_file'
goal.input_source = '/path/to/image.jpg'
goal.detection_method = 'hog'
goal.confidence_threshold = 0.5
goal.use_cuda = True

client.send_goal(goal)
client.wait_for_result()

result = client.get_result()

print(f"检测到 {result.num_detections} 个目标")
for det in result.detections:
    print(f"{det.class_name}: {det.confidence:.2f}")
```

---

## 故障排除

### CUDA 不可用

```python
import cv2
print(f"CUDA 设备数: {cv2.cuda.getCudaEnabledDeviceCount()}")
```

### 服务器未启动

```bash
rosnode list
rostopic list
```

### 环境变量问题

确保使用正确的 OpenCV 版本（CUDA 支持）：

```bash
export PYTHONNOUSERSITE=1
export PYTHONPATH="/opt/ros/noetic/lib/python3/dist-packages:$PYTHONPATH"
```

---

## 性能对比

在 Jetson Nano 4GB 上的性能对比（640x480 图像）：

| 操作 | CPU 时间 | CUDA 时间 | 加速比 |
|------|---------|----------|--------|
| resize | 5ms | 1ms | 5x |
| gaussian_blur | 15ms | 3ms | 5x |
| canny | 20ms | 5ms | 4x |
| color_convert | 3ms | 1ms | 3x |

---

## 许可证

MIT License