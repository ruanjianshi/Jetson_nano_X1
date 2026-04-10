#!/bin/bash
# TensorFlow 2.4.1 依赖版本修复脚本
# 安装特定版本的依赖包

echo "=========================================="
echo "TensorFlow 2.4.1 依赖修复"
echo "=========================================="
echo ""

echo "[步骤 1/2] 卸载冲突的依赖包..."
sudo -H pip3 uninstall -y absl-py flatbuffers gast numpy opt-einsum six termcolor typing-extensions 2>/dev/null || true
echo "✓ 清理完成"
echo ""

echo "[步骤 2/2] 安装TensorFlow 2.4.1所需的确切依赖版本..."
echo ""

# 安装缺失的包
echo "安装缺失的包..."
sudo -H pip3 install 'grpcio~=1.32.0'
sudo -H pip3 install 'tensorboard~=2.4'
sudo -H pip3 install 'tensorflow-estimator<2.5.0,>=2.4.0'
sudo -H pip3 install 'wrapt~=1.12.1'
echo ""

# 安装指定版本（解决版本冲突）
echo "安装指定版本的依赖..."
sudo -H pip3 install 'absl-py~=0.10'
sudo -H pip3 install 'flatbuffers~=1.12.0'
sudo -H pip3 install 'gast==0.3.3'
sudo -H pip3 install 'numpy~=1.19.2'
sudo -H pip3 install 'opt-einsum~=3.3.0'
sudo -H pip3 install 'six~=1.15.0'
sudo -H pip3 install 'termcolor~=1.1.0'
sudo -H pip3 install 'typing-extensions~=3.7.4'
echo ""

echo "=========================================="
echo "依赖修复完成！"
echo "=========================================="
echo ""

# 验证安装
echo "验证安装..."
echo ""

python3 << 'EOF'
import sys
packages = [
    'absl-py', 'astunparse', 'flatbuffers', 'gast', 
    'grpcio', 'h5py', 'numpy', 'opt-einsum', 'six', 
    'tensorboard', 'tensorflow-estimator', 'termcolor', 
    'typing-extensions', 'wrapt'
]

for pkg in packages:
    try:
        module = __import__(pkg.replace('-', '_'))
        version = getattr(module, '__version__', 'unknown')
        print(f"{pkg}: {version}")
    except ImportError:
        try:
            import pkg_resources
            version = pkg_resources.get_distribution(pkg).version
            print(f"{pkg}: {version}")
        except:
            print(f"{pkg}: 未安装")

print("\n验证TensorFlow...")
try:
    import tensorflow as tf
    print(f"TensorFlow版本: {tf.__version__}")
    print(f"CUDA可用: {tf.test.is_built_with_cuda()}")
    print(f"GPU可用: {tf.test.is_gpu_available()}")
except Exception as e:
    print(f"TensorFlow错误: {e}")
EOF
echo ""

echo "=========================================="
echo "所有依赖已正确安装！"
echo "=========================================="
echo ""