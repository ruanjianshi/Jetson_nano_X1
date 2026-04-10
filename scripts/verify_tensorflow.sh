#!/bin/bash
# TensorFlow 2.4.1 简化安装脚本
# 跳过问题依赖，直接验证TensorFlow可用性

echo "=========================================="
echo "TensorFlow 2.4.1 简化验证"
echo "=========================================="
echo ""

echo "[检查] 当前已安装的依赖..."
echo ""

python3 << 'EOF'
import sys

# 检查关键包
packages = {
    'absl-py': '>=0.10',
    'flatbuffers': '~=1.12.0',
    'gast': '==0.3.3',
    'numpy': '~=1.19.2',
    'opt-einsum': '~=3.3.0',
    'six': '~=1.15.0',
    'typing-extensions': '~=3.7.4'
}

for pkg, req in packages.items():
    try:
        module = __import__(pkg.replace('-', '_'))
        version = getattr(module, '__version__', 'unknown')
        print(f"{pkg}: {version}")
    except ImportError:
        print(f"{pkg}: 未安装")
EOF
echo ""

echo "[验证] TensorFlow是否可用..."
echo ""

python3 << 'EOF'
try:
    import tensorflow as tf
    print(f"✓ TensorFlow版本: {tf.__version__}")
    print(f"  CUDA支持: {tf.test.is_built_with_cuda()}")
    
    # 尝试GPU测试（这可能触发错误）
    try:
        print(f"  GPU可用: {tf.test.is_gpu_available()}")
    except Exception as e:
        print(f"  GPU测试跳过: {str(e)[:50]}")
    
    # 简单的TensorFlow测试
    print("\n[测试] 简单TensorFlow操作...")
    import numpy as np
    a = tf.constant([[1, 2], [3, 4]])
    b = tf.constant([[5, 6], [7, 8]])
    c = tf.matmul(a, b)
    print(f"✓ 矩阵乘法测试通过: {c}")
    
except Exception as e:
    print(f"✗ TensorFlow错误: {e}")
    sys.exit(1)
EOF
echo ""

echo "=========================================="
echo "TensorFlow 2.4.1 状态"
echo "=========================================="
echo ""

echo "注意："
echo "  1. grpcio、tensorboard、termcolor、wrapt 可能有兼容性问题"
echo "  2. TensorFlow核心功能可能正常"
echo "  3. 如果需要这些包，可以单独安装"
echo ""
echo "建议："
echo "  - 如果TensorFlow核心工作正常，可以忽略警告"
echo "  - 如果遇到具体错误，再针对性解决"
echo ""