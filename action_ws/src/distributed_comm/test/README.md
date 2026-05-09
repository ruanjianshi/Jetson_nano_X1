# 分布式 YOLOv11 推理测试

Jetson Nano 采集图像 → PC 推理 → 结果返回 Jetson 显示

## 架构

```
Jetson Nano B01                          PC (Ubuntu 20.04)
┌──────────────────────┐                ┌──────────────────────┐
│  roscore             │                │                      │
│                      │                │                      │
│  camera_publisher    │   compressed   │ distributed_yolo     │
│    CSI camera        │──────────────→ │   subscribe image    │
│    -> /camera/image  │    JPEG        │   YOLOv11 infer      │
│                      │                │   pub /yolo/result   │
│                      │                │   pub /yolo/detect   │
│  jetson_display      │   compressed   │                      │
│    sub /yolo/result  │←────────────── │                      │
│    show on screen    │    JPEG        │                      │
└──────────────────────┘                └──────────────────────┘
```

## 环境准备

### PC 端

```bash
# 安装依赖
pip3 install ultralytics opencv-python rospy

# 下载模型（或从 Jetson 拷贝）
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt

# 编译 distributed_comm
cd ~/nano_distribute
catkin_make -DCATKIN_WHITELIST_PACKAGES="distributed_comm"
source devel/setup.bash
```

### Jetson 端

```bash
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make -DCATKIN_WHITELIST_PACKAGES="distributed_comm"
source devel/setup.bash

# 验证摄像头可用
ls /dev/video*
```

## 测试步骤

### 1. 配置网络（如果还没配）

```bash
# Jetson: export ROS_IP=<Jetson_IP> && roscore &

# PC: export ROS_MASTER_URI=http://<Jetson_IP>:11311 && export ROS_IP=<PC_IP>
```

### 2. Jetson 端启动（摄像头 + 显示）

```bash
# 方式A：launch 文件
roslaunch distributed_comm camera_bridge.launch width:=640 height:=480 fps:=10 quality:=60

# 方式B：分别启动
rosrun distributed_comm camera_publisher.py _width:=640 _height:=480 _fps:=10 _quality:=60
rosrun distributed_comm jetson_display.py
```

### 3. PC 端启动（YOLO 推理）

```bash
# CPU 推理（默认）
roslaunch distributed_comm pc_yolo.launch

# GPU 推理（如果有 NVIDIA GPU）
roslaunch distributed_comm pc_yolo.launch device:=cuda:0 model_path:=./yolo11n.pt

roslaunch distributed_comm pc_yolo.launch device:=cuda:0 model_path:=$(rospack find distributed_comm)/model/yolo11l.pt
# 提高分辨率
roslaunch distributed_comm pc_yolo.launch imgsz:=640 conf:=0.3
```

## 参数说明

### camera_publisher（Jetson）

| 参数 | 默认 | 说明 |
|------|------|------|
| `_width` | 640 | 图像宽度 |
| `_height` | 480 | 图像高度 |
| `_fps` | 15 | 采集帧率 |
| `_quality` | 70 | JPEG 质量 (1-100)，越低传输量越小 |
| `_camera_index` | 0 | 摄像头设备号 |
| `_flip_method` | 0 | 翻转：0=不翻转，1=水平，-1=垂直 |

### distributed_yolo_server（PC）

| 参数 | 默认 | 说明 |
|------|------|------|
| `_model_path` | yolo11n.pt | 模型文件路径 |
| `_conf` | 0.5 | 置信度阈值 |
| `_iou` | 0.45 | IOU 阈值 |
| `_device` | cpu | cpu / cuda:0 |
| `_imgsz` | 640 | 推理图像尺寸 |

### jetson_display（Jetson）

| 参数 | 默认 | 说明 |
|------|------|------|
| `_show_gui` | true | 是否显示 GUI 窗口 |

## Topic 一览

| Topic | 方向 | 类型 | 说明 |
|-------|------|------|------|
| `/camera/image/compressed` | Jetson→PC | CompressedImage | 原始图像 JPEG |
| `/yolo/result_image/compressed` | PC→Jetson | CompressedImage | 推理结果标注图 |
| `/yolo/detections` | PC→Jetson | String(JSON) | 检测结果列表 |

## 带宽估算

| 分辨率 | JPEG质量 | 帧率 | 单帧大小(约) | 总带宽 |
|--------|----------|------|-------------|--------|
| 640x480 | 60 | 10fps | ~40KB | ~400KB/s |
| 640x480 | 80 | 15fps | ~60KB | ~900KB/s |
| 640x480 | 80 | 30fps | ~60KB | ~1.8MB/s |

双向加倍（Jetson→PC + PC→Jetson），需要保证 WiFi 链路有足够带宽。

## 常见问题

| 现象 | 解决方法 |
|------|----------|
| 摄像头打不开 | `ls /dev/video*` 确认摄像头存在；CSI 摄像头需要先用 `nvargus-daemon` |
| PC 收不到图像 | 检查 `ROS_MASTER_URI`，`rostopic list` 确认 topic |
| PC 推理很慢 | 用 `device:=cuda:0`；或降低 `_imgsz:=320` |
| 显示窗口打不开 | Jetson 需要插显示器，或用 `_show_gui:=false` 关闭 GUI |
| 图像卡顿 | 降低 `_fps` 或 `_quality` |
| `ultralytics not found` | `pip3 install ultralytics` |

## 作者

**作者**: Qi Xiao  
**邮箱**: 2408128687@qq.com
