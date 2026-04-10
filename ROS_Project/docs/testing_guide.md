# 测试文档

## 概述

本项目提供完整的测试套件，包括单元测试、集成测试和模块测试。所有测试脚本已整合并优化，避免冗余。

## 测试脚本说明

### 1. 项目级测试脚本

#### `test.sh` - 项目统一测试脚本
整合所有模块的测试功能，支持多种测试模式。

**使用方法：**
```bash
# 测试所有模块
./scripts/test.sh

# 快速测试（仅语法检查）
./scripts/test.sh quick

# 仅测试GPIO模块
./scripts/test.sh gpio

# 仅测试通信模块
./scripts/test.sh communication

# 仅测试OpenCV模块
./scripts/test.sh opencv

# 仅测试强化学习模块
./scripts/test.sh rl

# 仅测试Qt5 GUI模块
./scripts/test.sh gui

# 仅运行单元测试
./scripts/test.sh unit

# 仅运行集成测试
./scripts/test.sh integration

# 显示帮助
./scripts/test.sh help
```

**测试内容：**
- 环境检查（ROS、Python依赖）
- GPIO控制模块测试
- 通信模块测试
- OpenCV处理模块测试
- 强化学习模块测试
- Qt5 GUI模块测试
- 公共工具模块测试
- 单元测试
- 集成测试

### 2. GPIO测试脚本

#### `test_gpio.sh` - GPIO控制模块测试脚本
专门用于测试GPIO控制模块的Shell脚本。

**使用方法：**
```bash
# 完整测试（默认）
./scripts/test_gpio.sh

# 快速测试（跳过性能测试）
./scripts/test_gpio.sh quick

# 硬件测试（包含GPIO库测试）
./scripts/test_gpio.sh hardware

# 显示帮助
./scripts/test_gpio.sh help
```

**测试内容：**
- 环境检查
- ROS Master启动
- GPIO节点启动
- 话题接口测试
- 服务接口测试
- GPIO方向控制测试
- GPIO状态读取测试
- 硬件GPIO测试（可选）
- 性能测试（可选）

#### `test_gpio.py` - GPIO统一测试脚本
Python实现的GPIO测试脚本，支持硬件测试和ROS测试。

**使用方法：**
```bash
# 测试所有内容
python3 scripts/test_gpio.py

# 仅硬件测试
python3 scripts/test_gpio.py --mode hardware

# 仅ROS测试
python3 scripts/test_gpio.py --mode ros

# 设置超时时间（默认30秒）
python3 scripts/test_gpio.py --timeout 60
```

**测试内容：**
- GPIO模式设置测试
- GPIO初始化测试
- GPIO输出功能测试
- GPIO脉冲功能测试
- GPIO输入功能测试
- GPIO PWM功能测试
- 多GPIO同时操作测试
- ROS话题测试
- ROS服务测试

#### `test_jetson_gpio.py` - Jetson GPIO库测试
专门测试Jetson.GPIO库的独立脚本。

**使用方法：**
```bash
python3 scripts/test_jetson_gpio.py
```

**测试内容：**
- GPIO模式设置
- GPIO引脚初始化
- 输出功能测试
- 脉冲功能测试
- 输入功能测试
- PWM功能测试

### 3. 辅助脚本

#### `setup_jetson_gpio.sh` - GPIO环境设置
设置Jetson GPIO环境的脚本。

**使用方法：**
```bash
./scripts/setup_jetson_gpio.sh
```

**功能：**
- 安装Jetson.GPIO库
- 设置GPIO权限
- 配置GPIO组

#### `gpio_40pins_info.sh` - GPIO信息显示
显示Jetson Nano 40引脚GPIO信息。

**使用方法：**
```bash
./scripts/gpio_40pins_info.sh
```

**功能：**
- 显示40引脚完整分布
- 显示GPIO功能分类
- 显示推荐配置

#### `gpio_quick_start.sh` - GPIO快速启动
快速启动GPIO控制节点的脚本。

**使用方法：**
```bash
./scripts/gpio_quick_start.sh
```

**功能：**
- 激活ROS环境
- 启动GPIO控制节点
- 提供控制示例

#### `build.sh` - 项目构建脚本
构建所有ROS包的脚本。

**使用方法：**
```bash
./scripts/build.sh
```

## 测试流程

### 完整测试流程

1. **环境准备**
```bash
cd /home/jetson/Desktop/Jetson_Nano/ROS_Project
source devel/setup.bash
```

2. **运行完整测试**
```bash
./scripts/test.sh all
```

3. **查看测试结果**
测试结果会显示：
- 通过/失败的测试数量
- 各模块的测试状态
- 详细的错误信息（如果有）

### 快速测试流程

1. **语法检查**
```bash
./scripts/test.sh quick
```

2. **仅GPIO测试**
```bash
./scripts/test.sh gpio
```

### 硬件测试流程

1. **GPIO硬件测试**
```bash
python3 scripts/test_jetson_gpio.py
```

2. **GPIO ROS测试**
```bash
./scripts/test_gpio.sh quick
```

## 测试报告

测试完成后，会生成测试报告，包括：

- 测试统计（总计、通过、失败）
- 测试时长
- 各模块测试状态
- 详细的测试结果

## 测试目录结构

```
tests/
├── unit/              # 单元测试
│   └── .gitkeep
├── integration/       # 集成测试
│   └── .gitkeep
└── gpio_test_report.md # GPIO测试报告
```

## 编写测试

### 单元测试示例

在 `tests/unit/` 目录下创建测试文件：

```python
#!/usr/bin/env python3
import unittest
import sys
sys.path.append('../../src/<package_name>/scripts')

class TestClassName(unittest.TestCase):
    def test_method(self):
        """测试方法"""
        result = some_function()
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
```

### 集成测试示例

在 `tests/integration/` 目录下创建测试文件：

```python
#!/usr/bin/env python3
import rospy
import unittest

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rospy.init_node('test_node')
    
    def test_topic_communication(self):
        """测试话题通信"""
        pass

if __name__ == '__main__':
    unittest.main()
```

## 常见问题

### 1. 测试失败：GPIO节点未启动
**解决方案：**
```bash
# 手动启动GPIO节点
roslaunch gpio_control universal_gpio.launch

# 或在另一个终端运行测试
./scripts/test_gpio.sh
```

### 2. 测试失败：ROS环境未激活
**解决方案：**
```bash
source /opt/ros/noetic/setup.bash
source devel/setup.bash
```

### 3. 测试失败：权限不足
**解决方案：**
```bash
# 添加GPIO权限
sudo usermod -a -G gpio jetson

# 设置脚本执行权限
chmod +x scripts/*.sh scripts/*.py
```

### 4. 测试失败：依赖未安装
**解决方案：**
```bash
# 安装Python依赖
pip3 install Jetson.GPIO opencv-python PyQt5 numpy pyyaml
```

## 最佳实践

1. **测试前准备**
   - 确保ROS环境已激活
   - 确保工作空间已构建
   - 确保所有依赖已安装

2. **测试执行**
   - 从快速测试开始
   - 逐步扩展到完整测试
   - 保存测试日志

3. **测试后处理**
   - 检查测试结果
   - 分析失败原因
   - 更新代码或测试

4. **持续集成**
   - 定期运行测试
   - 自动化测试流程
   - 记录测试历史

## 测试覆盖率

当前测试覆盖：

- ✅ GPIO控制模块：100%
- ✅ 通信模块：语法检查
- ✅ OpenCV处理模块：语法检查
- ✅ 强化学习模块：语法检查
- ✅ Qt5 GUI模块：语法检查
- ✅ 公共工具模块：语法检查

## 扩展测试

### 添加新模块测试

1. 在 `scripts/test.sh` 中添加测试函数：
```bash
test_new_module() {
    print_header "测试新模块"
    # 测试逻辑
}
```

2. 在 `main()` 函数中调用：
```bash
case "$TEST_MODE" in
    all)
        test_new_module
        ;;
    new_module)
        test_new_module
        ;;
esac
```

### 添加新测试类型

1. 创建新的测试脚本
2. 集成到现有测试框架
3. 更新文档

## 参考资源

- [ROS测试教程](http://wiki.ros.org/rospy/Tutorials/UnitTesting)
- [Python unittest文档](https://docs.python.org/3/library/unittest.html)
- [Jetson GPIO文档](https://github.com/NVIDIA/jetson-gpio)