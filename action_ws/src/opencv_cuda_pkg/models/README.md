# 模型文件说明

此目录包含 OpenCV 目标检测所需的预训练模型文件。

## Haar Cascade 模型

| 文件 | 用途 | 检测对象 |
|------|------|----------|
| `haarcascade_frontalface_default.xml` | 人脸检测 | 正面人脸 |
| `haarcascade_eye.xml` | 眼睛检测 | 人眼 |
| `haarcascade_fullbody.xml` | 全身检测 | 完整个人体 |
| `haarcascade_upperbody.xml` | 上半身检测 | 人体上半部分 |
| `haarcascade_smile.xml` | 微笑检测 | 微笑表情 |

### 系统中的更多模型

```bash
ls /usr/share/opencv4/haarcascades/
```

常用模型：
- `haarcascade_lowerbody.xml` - 下半身检测
- `haarcascade_profileface.xml` - 侧面人脸检测
- `haarcascade_frontalcatface.xml` - 猫脸检测
- `haarcascade_licence_plate_rus_16stages.xml` - 车牌检测

## DNN 模型

### 目录结构
```
dnn/
├── res10_300x300_ssd_iter_140000.caffemodel  # MobileNet-SSD 人脸检测模型
├── deploy.prototxt                           # MobileNet-SSD 配置文件
└── README.md                                 # DNN 模型文档
```

### 人脸检测模型 (MobileNet-SSD)

**模型文件**:
- `res10_300x300_ssd_iter_140000.caffemodel` - 预训练权重
- `deploy.prototxt` - 网络配置

**下载方法**:

方法1: 使用提供的下载脚本
```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg
./scripts/download_models.sh
```

方法2: 手动下载
```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/models/dnn
wget https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel
wget https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt
```

### 其他 DNN 模型（可选）

#### YOLOv4 目标检测
```bash
wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights
wget https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4.cfg
```

#### MobileNet-SSD COCO 目标检测
```bash
wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz
tar -xzf ssd_mobilenet_v2_coco_2018_03_29.tar.gz
```

## 使用方法

### Haar Cascade 人脸检测

```bash
rosrun opencv_cuda_pkg opencv_detection_client.py \
  --type image_file \
  --source test/img/dog.png \
  --method haar_cascade \
  --cascade models/haarcascade_frontalface_default.xml
```

### DNN 人脸检测

```bash
rosrun opencv_cuda_pkg opencv_detection_client.py \
  --type image_file \
  --source test/img/dog.png \
  --method dnn \
  --model models/dnn/res10_300x300_ssd_iter_140000.caffemodel \
  --conf 0.7
```

### Python API - Haar Cascade

```python
from opencv_cuda_pkg.msg import OpenCVDetectionGoal
import actionlib

client = actionlib.SimpleActionClient('opencv_detection', OpenCVDetectionAction)
client.wait_for_server()

goal = OpenCVDetectionGoal()
goal.input_type = 'image_file'
goal.input_source = '/path/to/image.jpg'
goal.detection_method = 'haar_cascade'
goal.cascade_path = '/home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/models/haarcascade_frontalface_default.xml'
goal.use_cuda = True

client.send_goal(goal)
client.wait_for_result()
```

### Python API - DNN

```python
from opencv_cuda_pkg.msg import OpenCVDetectionGoal
import actionlib

client = actionlib.SimpleActionClient('opencv_detection', OpenCVDetectionAction)
client.wait_for_server()

goal = OpenCVDetectionGoal()
goal.input_type = 'image_file'
goal.input_source = '/path/to/image.jpg'
goal.detection_method = 'dnn'
goal.model_path = '/home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/models/dnn/res10_300x300_ssd_iter_140000.caffemodel'
goal.confidence_threshold = 0.7
goal.use_cuda = True

client.send_goal(goal)
client.wait_for_result()
```

## 模型性能对比

在 Jetson Nano 4GB 上的性能对比（640x480 图像）：

| 模型 | 方法 | 检测对象 | CPU 时间 | CUDA 时间 | 精度 |
|------|------|----------|---------|----------|------|
| HOG | 传统方法 | 行人 | ~100ms | ~50ms | 中等 |
| Haar Cascade | 传统方法 | 人脸 | ~50ms | ~20ms | 中等 |
| MobileNet-SSD | DNN | 人脸 | ~200ms | ~80ms | 高 |
| YOLOv4 | DNN | 80类对象 | ~500ms | ~150ms | 很高 |

## 注意事项

1. **DNN 模型需要额外下载** - Haar Cascade 模型已从系统复制
2. **模型文件较大** - DNN 模型可能需要较长时间下载
3. **首次使用较慢** - 模型加载需要时间，之后会缓存
4. **CUDA 加速** - DNN 模型在 CUDA 下运行更快

## 故障排除

### 模型文件未找到

```bash
# 检查模型文件是否存在
ls -lh /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/models/
```

### DNN 模型加载失败

1. 确认模型文件完整下载
2. 检查文件路径是否正确
3. 查看 OpenCV DNN 后端是否支持该格式

### 检测效果不佳

1. 调整置信度阈值 (`--conf`)
2. 尝试不同的检测方法
3. 使用更高质量的输入图像