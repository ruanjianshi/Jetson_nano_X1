# Jetson Nano ROS项目 - 完整架构指南

## 项目概述

基于ROS Noetic的Jetson Nano B01综合控制系统，采用C++和Python混合语言架构，提供GPIO控制、通信、图像处理、强化学习和图形界面等完整功能。

## 项目架构

### 技术栈
- **C++**: ROS C++ API, Boost.Asio, STL
- **Python**: rospy, cv2, numpy, PyQt5, Jetson.GPIO
- **通信**: ROS话题/服务、Boost.Asio、串口/TCP/IP
- **构建**: catkin, CMake
- **平台**: Jetson Nano B01, Ubuntu 18.04/20.04, ROS Noetic

### 混合语言架构
- **C++模块** (高性能实时控制): GPIO、通信、公共工具
- **Python模块** (灵活开发): OpenCV、强化学习、Qt5 GUI

## 完整项目树

```
ROS_Project/
├── .catkin_workspace                       # Catkin工作空间标记
├── README.md                               # 项目说明（本文件）
│
├── src/                                    # ROS包源代码
│   ├── gpio_control/                       # GPIO控制包
│   │   ├── include/gpio_control/           # C++头文件
│   │   ├── src/                            # C++源文件
│   │   ├── scripts/                        # Python ROS节点
│   │   │   ├── gpio_control_node.py        # GPIO控制节点（通用）
│   │   │   ├── gpio_control_node_jetson.py # GPIO控制节点（Jetson专用）
│   │   │   ├── universal_gpio_control_node.py # 通用GPIO控制节点
│   │   │   ├── gpio_test_node.py           # GPIO测试节点
│   │   │   ├── gpio_publisher_example.py   # 话题发布示例
│   │   │   ├── gpio_subscriber_example.py  # 话题订阅示例
│   │   │   ├── gpio_service_client_example.py # 服务客户端示例
│   │   │   └── gpio_info_query.py          # GPIO信息查询工具
│   │   ├── srv/                            # ROS服务定义
│   │   │   └── GPIOControl.srv
│   │   ├── launch/                         # 包特定launch文件
│   │   │   ├── gpio_control.launch
│   │   │   └── universal_gpio.launch
│   │   ├── config/                         # 包特定配置文件
│   │   ├── CMakeLists.txt                  # 构建配置
│   │   └── package.xml                     # 包元数据
│   │
│   ├── communication/                      # 通信模块包
│   │   ├── include/communication/          # C++头文件
│   │   ├── src/                            # C++源文件
│   │   ├── scripts/                        # Python ROS节点
│   │   │   ├── serial_comm_node.py         # 串口通信节点
│   │   │   ├── network_comm_node.py        # 网络通信节点
│   │   │   └── ros_bridge_node.py          # ROS桥接节点
│   │   ├── srv/                            # ROS服务定义
│   │   ├── CMakeLists.txt
│   │   └── package.xml
│   │
│   ├── opencv_processing/                  # OpenCV图像处理包
│   │   ├── scripts/                        # Python ROS节点
│   │   │   ├── camera_node.py              # 摄像头节点
│   │   │   └── image_processor_node.py     # 图像处理节点
│   │   ├── launch/                         # 包特定launch文件
│   │   ├── CMakeLists.txt
│   │   └── package.xml
│   │
│   ├── reinforcement_learning/             # 强化学习包
│   │   ├── scripts/                        # Python ROS节点
│   │   │   ├── rl_environment_node.py      # 强化学习环境节点
│   │   │   ├── rl_agent_node.py            # 强化学习智能体节点
│   │   │   └── rl_trainer_node.py          # 训练节点
│   │   ├── CMakeLists.txt
│   │   └── package.xml
│   │
│   ├── qt5_gui/                            # Qt5图形界面包
│   │   ├── scripts/                        # Python ROS节点
│   │   │   ├── main_gui_node.py            # 主GUI节点
│   │   │   ├── status_monitor.py           # 状态监控模块
│   │   │   └── control_panel.py            # 控制面板模块
│   │   ├── launch/                         # 包特定launch文件
│   │   ├── CMakeLists.txt
│   │   └── package.xml
│   │
│   └── common_utils/                       # 公共工具包
│       ├── include/common_utils/           # C++头文件
│       ├── src/                            # C++源文件
│       ├── scripts/                        # Python工具库
│       │   ├── logger_utils.py             # 日志工具
│       │   ├── config_loader.py            # 配置加载工具
│       │   ├── logger_utils_lib.py         # 日志工具库
│       │   └── config_loader_lib.py        # 配置加载工具库
│       ├── CMakeLists.txt
│       └── package.xml
│
├── scripts/                                # 项目级脚本（构建、测试、工具）
│   ├── build.sh                            # 构建所有ROS包
│   ├── test.sh                             # 运行所有测试
│   ├── setup_jetson_gpio.sh                # Jetson GPIO环境设置
│   ├── gpio_40pins_info.sh                 # 显示40引脚GPIO信息
│   ├── gpio_quick_start.sh                 # GPIO快速启动脚本
│   ├── test_gpio.sh                        # GPIO测试脚本
│   ├── test_gpio_simple.sh                 # GPIO简单测试
│   ├── test_gpio_advanced.sh               # GPIO高级测试
│   ├── test_universal_gpio.sh              # 通用GPIO测试
│   ├── test_jetson_gpio.py                 # Jetson GPIO测试（Python）
│   └── test_simple_gpio.py                 # 简单GPIO测试（Python）
│
├── launch/                                 # 全局launch文件
│   └── all_nodes.launch                    # 启动所有节点
│
├── config/                                 # 全局配置文件
│   └── default_config.yaml                 # 默认配置
│
├── models/                                 # 训练模型存储
│   └── .gitkeep                            # 占位文件
│
├── docs/                                   # 文档系统
│   ├── architecture.md                     # 系统架构文档
│   ├── gpio_guide.md                       # GPIO使用指南
│   └── development_guide.md                # 开发指南
│
├── logs/                                   # 日志系统
│   ├── daily/                              # 每日开发日志
│   │   └── 20250327_dev_log.md
│   └── progress/                           # 进度跟踪
│       └── progress_tracking.md
│
├── tests/                                  # 测试系统
│   ├── unit/                               # 单元测试
│   │   └── .gitkeep
│   ├── integration/                        # 集成测试
│   │   └── .gitkeep
│   └── gpio_test_report.md                 # GPIO测试报告
│
├── env/                                    # 环境配置脚本
│   └── setup_env.sh                        # 环境设置脚本
│
├── build/                                  # Catkin构建输出（自动生成）
├── devel/                                  # Catkin开发环境（自动生成）
│
└── CMakeLists.txt                          # 工作空间顶层CMake配置
```

## 目录职责说明

### src/ - ROS包源代码
存放所有ROS包的源代码，每个ROS包都是独立的软件单元：
- **include/**: C++头文件
- **src/**: C++源文件
- **scripts/**: Python ROS节点和工具库
- **srv/**: ROS服务定义
- **launch/**: 包特定的launch文件
- **config/**: 包特定的配置文件

### scripts/ - 项目级脚本
存放项目级的构建、测试、工具脚本：
- **构建脚本**: build.sh（编译所有ROS包）
- **测试脚本**: test.sh（运行测试）
- **设置脚本**: setup_jetson_gpio.sh（环境设置）
- **工具脚本**: GPIO信息查询、测试等

### docs/ - 文档系统
存放项目文档，统一管理：
- **architecture.md**: 系统架构设计
- **gpio_guide.md**: GPIO使用指南（合并原有多个GPIO文档）
- **development_guide.md**: 开发指南

### logs/ - 日志系统
- **daily/**: 每日开发日志
- **progress/**: 进度跟踪记录

### tests/ - 测试系统
- **unit/**: 单元测试
- **integration/**: 集成测试
- **report/**: 测试报告

## 模块功能详解

### C++模块

#### 1. GPIO控制模块 (gpio_control)
- GPIO引脚读写控制
- 多线程安全设计
- ROS服务接口
- 支持BOARD/BCM/TEGRA_SOC模式

#### 2. 通信模块 (communication)
- 串口通信 (Boost.Asio)
- 网络TCP/IP通信
- 异步IO操作
- ROS桥接功能

#### 3. 公共工具模块 (common_utils)
- 统一日志系统
- 配置管理
- 通用工具函数库

### Python模块

#### 1. OpenCV处理模块 (opencv_processing)
- 摄像头图像采集
- 图像处理和分析
- 边缘检测和识别

#### 2. 强化学习模块 (reinforcement_learning)
- 环境模拟
- Q-learning算法
- 模型训练和保存

#### 3. Qt5图形界面模块 (qt5_gui)
- 系统状态监控
- GPIO控制面板
- 实时数据显示

## 快速开始

### 1. 环境配置
```bash
cd ROS_Project
source env/setup_env.sh
```

### 2. 构建项目
```bash
./scripts/build.sh
source devel/setup.bash
```

### 3. 启动系统
```bash
# 启动所有节点
roslaunch launch/all_nodes.launch

# 或单独启动GPIO节点
roslaunch gpio_control universal_gpio.launch
```

### 4. GPIO控制示例
```bash
# 激活ROS环境
source devel/setup.bash

# 控制GPIO
rostopic pub /gpio/write std_msgs/Int32 "data: 0"

# 查询GPIO信息
python3 src/gpio_control/scripts/gpio_info_query.py
```

## 开发规范

### 文件命名规范
- **ROS节点**: `<功能>_node.py`
- **工具库**: `<功能>_utils.py`
- **示例**: `<功能>_example.py`
- **测试**: `test_<功能>.py`
- **Shell脚本**: `<功能>.sh`

### 代码组织原则
- ROS包代码放在src/
- 每个ROS包有独立的scripts/目录
- 项目级脚本放在根目录scripts/
- 文档统一放在docs/目录

### Git忽略规则
```
build/
devel/
*.pyc
__pycache__/
*.log
```

## 文档索引

- [系统架构](docs/architecture.md)
- [GPIO使用指南](docs/gpio_guide.md)
- [开发指南](docs/development_guide.md)
- [每日日志](logs/daily/)
- [进度跟踪](logs/progress/)

## 测试

### 运行所有测试
```bash
./scripts/test.sh
```

### GPIO测试
```bash
./scripts/test_gpio.sh
python3 scripts/test_jetson_gpio.py
```

## 常见问题

### 权限问题
```bash
sudo usermod -a -G gpio jetson
sudo chmod g+rw /sys/class/gpio/export
```

### GPIO初始化失败
1. 检查引脚是否被占用
2. 确认引脚编号正确
3. 检查系统权限

### 环境变量
```bash
source /opt/ros/noetic/setup.bash
source devel/setup.bash
```

## 许可证
MIT License

## 联系方式
- 开发者: Jetson Nano Developer
- 邮箱: user@jetsonnano