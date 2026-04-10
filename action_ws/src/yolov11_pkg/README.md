# YOLOv11 推理包

基于 ROS Action 通信的 YOLOv11 目标检测推理包，用于在 Jetson Nano 上进行实时目标检测。

## 功能特性

- 🎯 YOLOv11 预训练模型推理
- 🤝 基于 ROS Action 通信机制
- 📊 实时目标检测和位置信息输出
- 🚀 GPU 加速推理 (CUDA 10.2)
- 💾 模型文件已包含在包内
- 🎬 支持多种输入：ROS话题、图像文件、摄像头、视频文件
- 💾 保存推理结果图片（可选）
- 📤 实时摄像头推理时发布推理结果到话题

## 包结构

```
yolov11_pkg/
├── action/
│   └── Yolov11Inference.action    # Action 定义
├── msg/
│   └── DetectionResult.msg        # 检测结果消息
├── scripts/
│   ├── yolov11_inference_server.py # Action 服务器（集成推理引擎）
│   └── yolov11_inference_client.py # Action 客户端
├── models/
│   └── yolo11n.pt                 # YOLOv11 模型
├── img/
│   └── dog.png                    # 测试图片
└── launch/
    └── yolov11_inference_server.launch
```

## Action 定义

### Goal

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `model_path` | string | '' | 模型文件路径（可选，默认使用包内模型） |
| `input_type` | string | - | 输入类型: `topic`, `image_file`, `camera`, `video_file` |
| `input_source` | string | - | 输入源: 话题名、文件路径、摄像头索引（如 0）、视频文件路径 |
| `confidence_threshold` | float64 | 0.5 | 置信度阈值（可选） |
| `iou_threshold` | float64 | 0.45 | IOU阈值（可选） |
| `device` | string | 'cuda:0' | 设备: `cuda:0` 或 `cpu`（可选） |
| `save_image_path` | string | '' | 保存推理结果图片的路径（可选） |

### Result

| 参数 | 类型 | 描述 |
|------|------|------|
| `num_detections` | int32 | 检测到的目标数量 |
| `inference_time` | float64 | 推理时间（秒） |
| `detections[]` | DetectionResult[] | 检测结果列表 |
| `frames_processed` | int32 | 处理的帧数（视频/摄像头模式下） |
| `avg_inference_time` | float64 | 平均推理时间 |

### Feedback

| 参数 | 类型 | 描述 |
|------|------|------|
| `frame_count` | int32 | 已处理的帧数 |
| `fps` | float64 | 当前帧率 |
| `status` | string | 状态信息 |

## 输出话题

### /yolov11/inference_result

- **类型**: `sensor_msgs/Image`
- **描述**: 摄像头实时推理时，发布带有检测框的图像
- **使用场景**: 实时摄像头推理模式下，其他节点可以订阅此话题获取实时检测结果

### 订阅示例

```bash
# 使用 image_view 订阅
rosrun image_view image_view image:=/yolov11/inference_result
```

```python
# Python 订阅示例
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

def callback(msg):
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(msg, "bgr8")
    cv2.imshow('YOLOv11 推理结果', cv_image)
    cv2.waitKey(1)

rospy.init_node('inference_viewer')
rospy.Subscriber('/yolov11/inference_result', Image, callback)
rospy.spin()
```

## DetectionResult 消息

DetectionResult.msg 包含目标的详细位置信息：

| 字段 | 类型 | 描述 |
|------|------|------|
| `class_id` | int32 | 类别 ID |
| `class_name` | string | 类别名称 |
| `confidence` | float64 | 置信度 |
| `x1` | float64 | 边界框左上角 x |
| `y1` | float64 | 边界框左上角 y |
| `x2` | float64 | 边界框右下角 x |
| `y2` | float64 | 边界框右下角 y |
| `center_x` | float64 | 中心点 x |
| `center_y` | float64 | 中心点 y |
| `area` | float64 | 边界框面积 |

## 编译

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make -DCATKIN_WHITELIST_PACKAGES=yolov11_pkg
source devel/setup.bash
```

## 使用方法

### 启动推理服务器

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source devel/setup.bash
roslaunch yolov11_pkg yolov11_inference_server.launch
```

### 使用客户端进行推理

#### 1. 从图像文件推理（保存结果图片）

```bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type image_file \
  --source action_ws/src/yolov11_pkg/img/dog.png \
  --save action_ws/src/yolov11_pkg/result/dog_result.jpg
```

#### 2. 从摄像头实时推理（发布到话题）

```bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type camera \
  --source 0
```

在另一个终端订阅推理结果：

```bash
rosrun image_view image_view image:=/yolov11/inference_result
```

#### 3. 从 ROS 话题推理

```bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type topic \
  --source /camera/image_raw
```

#### 4. 从视频文件推理

```bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type video_file \
  --source /path/to/video.mp4
```

### 使用自定义模型和参数

```bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type image_file \
  --source /path/to/image.jpg \
  --model /path/to/custom_model.pt \
  --conf 0.6 \
  --iou 0.5 \
  --device cuda:0 \
  --save /path/to/result.jpg
```

## Python API

### 发送推理目标（图像文件，保存结果）

```python
import actionlib
from yolov11_pkg.msg import Yolov11InferenceGoal, Yolov11InferenceAction

client = actionlib.SimpleActionClient('yolov11_inference', Yolov11InferenceAction)
client.wait_for_server()

goal = Yolov11InferenceGoal()
goal.input_type = 'image_file'
goal.input_source = '/path/to/image.jpg'
goal.confidence_threshold = 0.6
goal.save_image_path = '/path/to/result.jpg'

client.send_goal(goal)
client.wait_for_result()

result = client.get_result()

# 使用检测结果
for det in result.detections:
    print(f"{det.class_name}: ({det.center_x:.0f}, {det.center_y:.0f})")
```

### 发送推理目标（摄像头实时推理）

```python
import actionlib
from yolov11_pkg.msg import Yolov11InferenceGoal, Yolov11InferenceAction

client = actionlib.SimpleActionClient('yolov11_inference', Yolov11InferenceAction)
client.wait_for_server()

goal = Yolov11InferenceGoal()
goal.input_type = 'camera'
goal.input_source = '0'
goal.confidence_threshold = 0.6
goal.device = 'cuda:0'

client.send_goal(goal)
client.wait_for_result()

result = client.get_result()
```

### 订阅实时推理结果

```python
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

def inference_callback(msg):
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(msg, "bgr8")
    cv2.imshow('YOLOv11 推理结果', cv_image)
    cv2.waitKey(1)

rospy.init_node('inference_subscriber')
rospy.Subscriber('/yolov11/inference_result', Image, inference_callback)
rospy.spin()
```

## 测试示例

### 测试 1: 使用测试图片

```bash
# 终端 1: 启动 roscore
roscore

# 终端 2: 启动推理服务器
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source devel/setup.bash
roslaunch yolov11_pkg yolov11_inference_server.launch

# 终端 3: 推理测试图片并保存结果
source /home/jetson/Desktop/Jetson_Nano/action_ws/devel/setup.bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type image_file \
  --source /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/img/dog.png \
  --save /home/jetson/Desktop/Jetson_Nano/dog_result.jpg
```
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source devel/setup.bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type image_file \
  --source /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/img/dog.png \
  --save /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/result/dog_result.jpg

### 测试 2: 摄像头实时推理

```bash
# 终端 1: 启动 roscore
roscore

# 终端 2: 启动推理服务器
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source devel/setup.bash
roslaunch yolov11_pkg yolov11_inference_server.launch

# 终端 3: 启动摄像头推理
source /home/jetson/Desktop/Jetson_Nano/action_ws/devel/setup.bash
rosrun yolov11_pkg yolov11_inference_client.py \
  --type camera \
  --source 0

# 终端 4: 查看实时推理结果
source /home/jetson/Desktop/Jetson_Nano/action_ws/devel/setup.bash
rosrun image_view image_view image:=/yolov11/inference_result
```

## 性能优化

### 启用 MAXN 性能模式

```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

### 监控性能

```bash
sudo jtop
```

## 故障排除

### 模型加载失败

```bash
ls /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/models/yolo11n.pt
```

### CUDA 不可用

```bash
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 摄像头访问失败

```bash
ls /dev/video*
```

### 保存路径权限

确保对保存路径有写权限，或者程序会自动创建目录。

## 性能参考

在 Jetson Nano 4GB 上的典型性能 (yolo11n, 640x640):

- 单帧推理时间: ~50-100ms
- 摄像头实时推理 FPS: ~10-20
- 显存使用: ~800MB

## 许可证

MIT License


[INFO] [1775184316.013886]: 🎯 推理请求: 类型=image_file, 源=/home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/img/dog.png
[INFO] [1775184316.019212]: 💾 保存路径: /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/result/dog_result.jpg
[INFO] [1775184316.024321]: 📦 模型: /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/models/yolo11n.pt
[INFO] [1775184316.029005]: ⚙️  参数: conf=0.5, iou=0.45, device=cuda:0
[INFO] [1775184316.034012]: 📦 使用已加载的模型
[INFO] [1775184316.039437]: 📄 从文件读取图像: /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/img/dog.png
WARNING ⚠️ NMS time limit 2.050s exceeded
[INFO] [1775184697.686572]: ✅ 推理结果已保存到: /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/result/dog_result.jpg
[INFO] [1775184698.606671]: ✅ 推理完成: 3 个目标, 耗时 378.718s

>   --save /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/result/dog_result.jpg
[INFO] [1775184315.896140]: 🔍 等待服务器启动...
[INFO] [1775184315.918431]: ✅ 服务器已连接
[INFO] [1775184315.924599]: 📤 发送推理目标:
[INFO] [1775184315.929795]:   类型: image_file
[INFO] [1775184315.934544]:   源: /home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/img/dog.png
[INFO] [1775184315.939052]:   参数: conf=0.5, iou=0.45, device=cuda:0

============================================================
📊 YOLOv11 推理结果
============================================================
检测到的目标数量: 3
推理时间: 378.718 秒

检测结果详情:
------------------------------------------------------------

  [1] dog (置信度: 0.92)
      边界框: (17, 154) -> (129, 355)
      中心点: (73, 254)
      面积: 22315 像素²

  [2] bicycle (置信度: 0.91)
      边界框: (12, 99) -> (292, 279)
      中心点: (152, 189)
      面积: 50298 像素²

  [3] car (置信度: 0.52)
      边界框: (230, 61) -> (369, 122)
      中心点: (300, 91)
      面积: 8484 像素²
============================================================

[INFO] [1775184698.724617]: ✅ 推理成功完成