# 系统架构文档

## 架构概述

本项目采用模块化设计，基于ROS Noetic构建的Jetson Nano B01综合控制系统，使用C++和Python混合语言架构。

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Qt5 GUI Layer                             │
│              (状态监控 + 控制面板)                            │
└────────────────────┬────────────────────────────────────────┘
                     │ ROS Topics/Services
┌────────────────────┴────────────────────────────────────────┐
│                   ROS Communication Layer                    │
│                  (话题发布/订阅 + 服务调用)                   │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
┌──────────┴──────────┐          ┌──────────┴──────────┐
│   Python Modules    │          │    C++ Modules      │
├─────────────────────┤          ├─────────────────────┤
│  • OpenCV Processing│          │  • GPIO Control     │
│  • RL Environment   │          │  • Communication    │
│  • RL Agent         │          │  • Common Utils     │
└──────────┬──────────┘          └──────────┬──────────┘
           │                                 │
           └──────────┬──────────────────────┘
                      │
┌─────────────────────┴──────────────────────────────────────┐
│                  Hardware Layer                            │
│  • Jetson Nano B01  • GPIO 40-Pin  • Camera  • Sensors   │
└────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. GPIO控制模块 (gpio_control)

#### 功能特性
- GPIO引脚读写控制
- 多线程安全设计
- ROS服务接口
- 支持BOARD/BCM/TEGRA_SOC模式
- 实时状态监控

#### 技术实现
- **C++**: 高性能GPIO操作
- **Python**: ROS节点封装
- **通信方式**: ROS话题 + 服务

#### 接口设计
```
话题:
- /gpio/write (Int32)          # 写入GPIO
- /gpio/toggle (Int32)         # 切换GPIO状态
- /gpio/set_input (Int32)      # 设置为输入
- /gpio/set_output (Int32)     # 设置为输出
- /gpio/state (Int32)          # GPIO状态

服务:
- /gpio_control (GPIOControl)  # GPIO控制服务
```

### 2. 通信模块 (communication)

#### 功能特性
- 串口通信 (Boost.Asio)
- 网络TCP/IP通信
- 异步IO操作
- ROS桥接功能

#### 技术实现
- **C++**: Boost.Asio异步通信
- **Python**: ROS桥接节点
- **通信协议**: 自定义协议 + ROS标准

#### 接口设计
```
话题:
- /serial_tx (String)          # 串口发送
- /serial_rx (String)          # 串口接收
- /network_tx (String)         # 网络发送
- /network_rx (String)         # 网络接收

服务:
- /serial_connect (SerialConnect)
- /network_connect (NetworkConnect)
```

### 3. OpenCV处理模块 (opencv_processing)

#### 功能特性
- 摄像头图像采集
- 图像处理和分析
- 边缘检测和识别
- 实时图像发布

#### 技术实现
- **Python**: OpenCV + ROS
- **图像处理**: 灰度化、边缘检测、轮廓识别
- **性能优化**: 多线程处理

#### 接口设计
```
话题:
- /camera/image_raw (sensor_msgs/Image)  # 原始图像
- /camera/image_processed (sensor_msgs/Image)  # 处理后图像
- /camera/camera_info (sensor_msgs/CameraInfo)  # 相机信息
```

### 4. 强化学习模块 (reinforcement_learning)

#### 功能特性
- 环境模拟
- Q-learning算法
- 模型训练和保存
- 策略部署

#### 技术实现
- **Python**: numpy + ROS
- **算法**: Q-learning、DQN
- **模型保存**: pickle/h5py

#### 接口设计
```
话题:
- /rl/state (Float32MultiArray)      # 状态
- /rl/action (Int32)                 # 动作
- /rl/reward (Float32)               # 奖励
- /rl/episode_done (Bool)            # 回合结束
```

### 5. Qt5 GUI模块 (qt5_gui)

#### 功能特性
- 系统状态监控
- GPIO控制面板
- 实时数据显示
- 图形化配置

#### 技术实现
- **Python**: PyQt5 + ROS
- **UI设计**: 模块化组件
- **数据绑定**: ROS话题订阅

#### 接口设计
```
订阅话题:
- /gpio/state
- /camera/image_raw
- /rl/state

发布话题:
- /gui/command
- /gpio/write
```

### 6. 公共工具模块 (common_utils)

#### 功能特性
- 统一日志系统
- 配置管理
- 工具函数库
- 错误处理

#### 技术实现
- **C++**: 工具类库
- **Python**: 工具模块
- **日志**: 文件 + 控制台

## 数据流设计

### GPIO控制数据流
```
Qt5 GUI → /gpio/write → GPIO Control Node → Hardware
          ↑
          │
    /gpio/state ← GPIO Control Node ← Hardware
```

### 图像处理数据流
```
Camera → Camera Node → /camera/image_raw → Processor Node → /camera/image_processed
                                      ↓
                                   Qt5 GUI
```

### 强化学习数据流
```
Environment Node → /rl/state → Agent Node → /rl/action → Environment Node
                       ↓                      ↓
                  /rl/reward             更新策略
```

## 通信机制

### ROS话题 (Topics)
用于节点间异步通信：
- 发布/订阅模式
- 支持多种消息类型
- 适合高频数据传输

### ROS服务 (Services)
用于同步请求/响应：
- 请求/响应模式
- 适合控制命令
- 支持参数传递

### Boost.Asio
用于底层通信：
- 异步IO操作
- 高性能串口/网络通信
- C++实现

## 性能优化

### C++优化
- 多线程处理
- 内存池管理
- 零拷贝通信

### Python优化
- 异步IO
- 进程池
- NumPy加速

### ROS优化
- 消息队列优化
- 节点分离
- 参数服务器

## 扩展性设计

### 模块化
- 每个模块独立开发和测试
- 清晰的接口定义
- 松耦合设计

### 可配置
- YAML配置文件
- 参数服务器
- 动态参数调整

### 可扩展
- 插件架构
- 自定义消息/服务
- 模块热加载

## 安全性设计

### 硬件安全
- GPIO电流限制
- 短路保护
- 隔离设计

### 软件安全
- 错误处理
- 异常捕获
- 日志记录

### 通信安全
- 数据校验
- 超时处理
- 重连机制

## 故障处理

### 故障检测
- 心跳检测
- 状态监控
- 异常捕获

### 故障恢复
- 自动重连
- 状态恢复
- 降级运行

### 故障日志
- 错误日志
- 性能日志
- 调试日志

## 部署架构

### 开发环境
- Jetson Nano B01
- Ubuntu 18.04/20.04
- ROS Noetic
- Python 3.6+

### 生产环境
- 独立部署
- Docker容器化
- 系统服务
- 自动启动

## 监控和维护

### 系统监控
- 资源监控
- 性能监控
- 日志监控

### 维护策略
- 定期备份
- 版本管理
- 文档更新
- 测试覆盖