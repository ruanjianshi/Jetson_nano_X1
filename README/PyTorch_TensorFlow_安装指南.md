# Jetson Nano B01 PyTorch & TensorFlow 安装指南

> 基于 Q-engineering 官方安装指南
> 最后更新: 2026-03-24

## 版本兼容性确认

您的系统信息:
- **操作系统**: Ubuntu 20.04 focal ✅
- **Python版本**: Python 3.8.10 ✅
- **JetPack**: 4.6.2 [L4T 32.7.2]
- **CUDA版本**: 10.2.300

✅ **您的系统支持以下高级版本** (感谢Ubuntu 20.04 + Python 3.8):
- PyTorch 1.13.0 + TorchVision 0.14.0 ✅
- PyTorch 1.12.0 + TorchVision 0.13.0 ✅
- PyTorch 1.11.0 + TorchVision 0.12.0 ✅

---

## 方案一: 安装 PyTorch 1.13.0 + TorchVision 0.14.0 (推荐)

### 安装步骤

```bash
# 1. 安装依赖
sudo apt-get install python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
sudo -H pip3 install future
sudo pip3 install -U --user wheel mock pillow
sudo -H pip3 install testresources
sudo -H pip3 install setuptools==58.3.0
sudo -H pip3 install Cython

# 2. 安装gdown (用于从Google Drive下载)
sudo -H pip3 install gdown

# 3. 下载PyTorch 1.13.0 wheel
gdown https://drive.google.com/uc?id=1e9FDGt2zGS5C5Pms7wzHYRb0HuupngK1

# 4. 安装PyTorch
sudo -H pip3 install torch-1.13.0a0+git7c98e70-cp38-cp38-linux_aarch64.whl

# 5. 清理临时文件
rm torch-1.13.0a0+git7c98e70-cp38-cp38-linux_aarch64.whl

# 6. 安装TorchVision依赖
sudo apt-get install libjpeg-dev zlib1g-dev libpython3-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev
sudo pip3 install -U pillow

# 7. 下载TorchVision 0.14.0
gdown https://drive.google.com/uc?id=19UbYsKHhKnyeJ12VPUwcSvoxJaX7jQZ2

# 8. 安装TorchVision
sudo -H pip3 install torchvision-0.14.0a0+5ce4506-cp38-cp38-linux_aarch64.whl

# 9. 清理临时文件
rm torchvision-0.14.0a0+5ce4506-cp38-cp38-linux_aarch64.whl

# 10. 更新protobuf (Caffe2需要)
sudo -H pip3 install -U protobuf
```

### 验证安装

```bash
# 验证PyTorch
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA版本: {torch.version.cuda}')"

# 验证TorchVision
python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')"

# 验证Caffe2
python3 -c "from caffe2.python import workspace; print('Caffe2可用')"
```

---

## 方案二: 安装 PyTorch 1.12.0 + TorchVision 0.13.0

```bash
# 安装依赖
sudo apt-get install python3-pip libjpeg-dev libopenblas-dev libopenmpi-dev libomp-dev
sudo -H pip3 install future
sudo pip3 install -U --user wheel mock pillow
sudo -H pip3 install testresources
sudo -H pip3 install setuptools==58.3.0
sudo -H pip3 install Cython
sudo -H pip3 install gdown

# 下载并安装PyTorch 1.12.0
gdown https://drive.google.com/uc?id=1MnVB7I4N8iVDAkogJO76CiQ2KRbyXH_e
sudo -H pip3 install torch-1.12.0a0+git67ece03-cp38-cp38-linux_aarch64.whl
rm torch-1.12.0a0+git67ece03-cp38-cp38-linux_aarch64.whl

# 安装TorchVision依赖
sudo apt-get install libjpeg-dev zlib1g-dev libpython3-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev
sudo pip3 install -U pillow

# 下载并安装TorchVision 0.13.0
gdown https://drive.google.com/uc?id=11DPKcWzLjZa5kRXRodRJ3t9md0EMydhj
sudo -H pip3 install torchvision-0.13.0a0+da3794e-cp38-cp38-linux_aarch64.whl
rm torchvision-0.13.0a0+da3794e-cp38-cp38-linux_aarch64.whl

# 更新protobuf
sudo -H pip3 install -U protobuf
```

---

## 方案三: 安装 TensorFlow 2.7.0 (NVIDIA官方版本)

JetPack 4.6官方支持的TensorFlow版本是2.7.0，不是2.4.1。

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install python3-pip libhdf5-serial-dev hdf5-tools libhdf5-dev zlib1g-dev zip libjpeg8-dev liblapack-dev libblas-dev gfortran

# 安装TensorFlow 2.7.0 (JetPack 4.6官方版本)
pip3 install --pre --extra-index-url https://developer.download.nvidia.com/compute/redist/jp/v461/tensorflow tensorflow==2.7.0

# 验证安装
python3 -c "import tensorflow as tf; print(f'TensorFlow版本: {tf.__version__}'); print(f'GPU可用: {tf.test.is_gpu_available()}')"
```

**注意**: TensorFlow 2.7.0需要CUDA 11.2，可能与系统的CUDA 10.2不兼容。建议优先使用PyTorch。

---

## 版本对照表

| 软件包 | 版本 | 状态 | 说明 |
|--------|------|------|------|
| **PyTorch** | 1.13.0 | ✅ 推荐 | 最新稳定版本，支持Ubuntu 20.04 |
| | 1.12.0 | ✅ 可用 | 稳定版本 |
| | 1.11.0 | ✅ 可用 | 稳定版本 |
| | 1.10.0 | ✅ 可用 | JetPack 4.6官方推荐 |
| **TorchVision** | 0.14.0 | ✅ 推荐 | 配合PyTorch 1.13.0 |
| | 0.13.0 | ✅ 可用 | 配合PyTorch 1.12.0 |
| | 0.12.0 | ✅ 可用 | 配合PyTorch 1.11.0 |
| | 0.11.0 | ✅ 可用 | 配合PyTorch 1.10.0 |
| **TensorFlow** | 2.7.0 | ⚠️ 需要CUDA 11.2 | 可能不兼容 |
| | 2.4.1 | ❌ 不推荐 | 无官方Jetson版本 |

---

## 常见问题

### Q: 为什么不能安装PyTorch 2.0+?
A: PyTorch 2.0需要CUDA 11，但Jetson Nano只有CUDA 10.2。需要升级到JetPack 5.0+（仅支持Xavier系列）。

### Q: 安装失败，提示"wheel not supported"?
A: 确保pip版本是最新的:
```bash
sudo -H pip3 install --upgrade pip
```

### Q: 下载速度慢或无法连接Google Drive?
A: 可以使用代理或从GitHub仓库下载:
```bash
git clone https://github.com/Qengineering/PyTorch-Jetson-Nano.git
```

### Q: 内存不足导致安装失败?
A: 建议在安装前关闭不必要的程序，或增加swap:
```bash
# 查看当前swap
free -h

# 增加swap (如果需要)
sudo dd if=/dev/zero of=/swapfile bs=1G count=4
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 性能优化建议

1. **设置最大性能模式**:
```bash
sudo nvpmodel -m 0  # MAXN模式
sudo jetson_clocks  # 启用最大时钟频率
```

2. **监控GPU使用**:
```bash
sudo jtop          # 完整监控
tegrastats         # 命令行监控
```

3. **调整风扇速度** (如果过热):
```bash
sudo sh -c 'echo 255 > /sys/class/hwmon/hwmon0/pwm1'
```

---

## 卸载方法

```bash
# 卸载PyTorch和TorchVision
pip3 uninstall torch torchvision -y

# 卸载TensorFlow
pip3 uninstall tensorflow -y

# 清理缓存
rm -rf ~/.cache/pip
```

---

## 参考资源

- [Q-engineering PyTorch安装指南](https://qengineering.eu/install-pytorch-on-jetson-nano.html)
- [Q-engineering GitHub](https://github.com/Qengineering/PyTorch-Jetson-Nano)
- [NVIDIA JetPack 4.6](https://developer.nvidia.com/embedded/jetpack-sdk-462)
- [PyTorch官方文档](https://pytorch.org/docs/stable/index.html)

---

**安装前请确保**:
- ✅ 网络连接正常
- ✅ 至少5GB可用磁盘空间
- ✅ 系统已更新到最新版本
- ✅ 拥有sudo权限

**安装时间估计**: 约15-30分钟（取决于网络速度）

祝安装顺利！🚀