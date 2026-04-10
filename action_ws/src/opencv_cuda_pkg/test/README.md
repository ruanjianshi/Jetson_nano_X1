# 测试文件说明

此目录包含用于测试 OpenCV CUDA 包的测试文件。

## 目录结构

```
test/
├── img/                         # 测试图片
│   └── dog.png                  # 示例图片
├── result/                      # 测试结果输出
├── scripts/                     # 测试脚本
│   ├── test_processing.py       # 图像处理测试脚本
│   ├── test_all.sh              # 批量图像处理测试
│   └── test_detection.sh        # 目标检测测试
└── README.md                    # 本文档
```

## 使用方法

### 1. 图像处理测试

运行所有图像处理操作测试：

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/test/scripts
./test_all.sh
```

测试包括：
- Resize (640x480)
- Gaussian Blur
- Canny Edge Detection
- Color Convert (BGR to Gray)

结果将保存在 `test/result/` 目录。

### 2. 目标检测测试

运行目标检测测试：

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws/src/opencv_cuda_pkg/test/scripts
./test_detection.sh
```

测试包括：
- HOG 行人检测
- Haar Cascade 人脸检测

### 3. 单个测试

运行单个图像处理测试：

```bash
python3 test_processing.py \
    --source test/img/dog.png \
    --operation resize \
    --params '{"width": 640, "height": 480}' \
    --save test/result/dog_resize.jpg
```

运行单个目标检测测试：

```bash
python3 ../../scripts/opencv_detection_client.py \
    --type image_file \
    --source ../img/dog.png \
    --method hog
```

## 注意事项

1. **服务器必须先启动**：在运行测试之前，确保相应的服务器正在运行
2. **环境变量**：测试脚本已包含正确的环境变量设置
3. **测试图片**：可以替换 `test/img/` 目录中的图片进行自定义测试

## 测试结果

测试结果会保存在 `test/result/` 目录，包括：
- `dog_resize.jpg` - 调整大小后的图像
- `dog_blur.jpg` - 模糊后的图像
- `dog_canny.jpg` - 边缘检测结果
- `dog_gray.jpg` - 灰度图像