# Action 串口通信项目

## 📋 项目概述

本项目基于 ROS Action 实现串口通信功能，演示如何使用 ROS Action 框架进行串口数据的发送和接收。项目使用 Jetson Nano 的 `/dev/ttyTHS1` 串口（8号和10号引脚），并通过回环测试验证通信功能。

## 🏗️ 项目结构

```
action_ws/
├── src/
│   └── my_action_pkg/
│       ├── action/                    # Action 定义文件
│       │   ├── Fibonacci.action      # Fibonacci 序列计算 Action
│       │   └── SerialComm.action     # 串口通信 Action (新增)
│       ├── launch/                   # Launch 文件
│       │   ├── fibonacci.launch
│       │   └── serial_comm.launch    # 串口通信启动文件 (新增)
│       ├── scripts/                  # Python 脚本
│       │   ├── fibonacci_server.py
│       │   ├── fibonacci_client.py
│       │   ├── serial_comm_server.py    # 串口通信服务器 (新增)
│       │   └── serial_comm_client.py    # 串口通信客户端 (新增)
│       ├── CMakeLists.txt
│       └── package.xml
├── test_serial_comm_action.sh       # 测试脚本
└── SERIAL_COMM_README.md            # 本文档
```

## 🔧 Action 定义 (SerialComm.action)

### Goal - 发送目标
```yaml
std_msgs/String data  # 要通过串口发送的数据
```

### Result - 返回结果
```yaml
std_msgs/String received_data  # 从串口接收到的数据
bool success                   # 操作是否成功
```

### Feedback - 进度反馈
```yaml
std_msgs/String partial_data  # 部分数据（正在发送的数据）
```

## 💡 代码注释说明

### Server 端 (serial_comm_server.py)

代码包含详细的中文注释，分为以下几个部分：

1. **文件头部文档** - 说明文件功能、使用方法和作者信息
2. **导入模块** - 解释每个导入模块的用途
3. **类定义** - 说明类的职责和功能
4. **构造函数** - 详细注释初始化过程的每个步骤
5. **串口连接函数** - 解释串口参数配置和异常处理
6. **Action 执行回调** - 说明 Goal 处理流程
7. **主函数** - 解释程序入口和异常处理

### Client 端 (serial_comm_client.py)

代码包含详细的中文注释，分为以下几个部分：

1. **文件头部文档** - 说明文件功能、使用方法和示例
2. **导入模块** - 解释每个导入模块的用途
3. **类定义** - 说明类的职责和通信流程
4. **构造函数** - 详细注释客户端初始化和通信流程
5. **反馈回调函数** - 说明 Feedback 处理机制
6. **主函数** - 解释参数获取和异常处理

## 🚀 使用方法

### 1. 编译项目

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make
catkin_make install
```

### 2. 启动 Server (需要 sudo 权限)

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash
sudo roslaunch my_action_pkg serial_comm.launch
```

### 3. 发送数据 (Client)

打开新终端，执行：

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash
rosrun my_action_pkg serial_comm_client.py _data:="Hello"
```

### 4. 使用测试脚本

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
./test_serial_comm_action.sh
```

## ⚙️ 参数配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `serial_port` | `/dev/ttyTHS1` | 串口设备路径 |
| `baud_rate` | `115200` | 波特率 (bps) |
| `timeout` | `1.0` | 超时时间 (秒) |
| `enable_echo` | `true` | 是否打印日志 |

### 修改参数方法

#### 方法 1: 通过 launch 文件
```xml
<launch>
  <node name="serial_comm_server" pkg="my_action_pkg" type="serial_comm_server.py">
    <param name="serial_port" value="/dev/ttyTHS1" />
    <param name="baud_rate" value="115200" />
    <param name="timeout" value="1.0" />
    <param name="enable_echo" value="true" />
  </node>
</launch>
```

#### 方法 2: 通过命令行参数
```bash
rosrun my_action_pkg serial_comm_client.py _data:="Hello"
```

## 🔌 硬件连接

### Jetson Nano 串口引脚

| 物理引脚 | 设备 | GPIO (BCM) | 功能 |
|---------|------|-----------|------|
| **8** | `/dev/ttyTHS1` | GPIO14 | TXD0 (发送数据) |
| **10** | `/dev/ttyTHS1` | GPIO15 | RXD0 (接收数据) |

### 回环测试

将 8 号引脚和 10 号引脚用跳线短接，实现数据回环：
- 发送的数据从 TXD0 (8号引脚) 发出
- 通过回环跳线传输到 RXD0 (10号引脚)
- Server 从串口接收回环数据并返回给 Client

## 📊 工作流程

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │────────▶│   Server    │────────▶│  串口设备   │
│             │  Goal   │             │  Write  │  /dev/...  │
│             │         │             │         │             │
│   Client    │◀────────│   Server    │◀────────│  串口设备   │
│             │  Result │             │  Read   │  /dev/...  │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ▼
                      Feedback (可选)
```

### 详细步骤

1. **Client 发送 Goal**
   - Client 创建 `SerialCommGoal` 对象
   - 设置 `goal.data` 为要发送的数据
   - 通过 Action Client 发送 Goal 到 Server

2. **Server 处理 Goal**
   - Server 接收 Goal，触发 `execute()` 回调
   - 发送 Feedback 给 Client（告知正在处理的数据）
   - 通过串口发送数据
   - 等待并接收回环数据
   - 返回 Result 给 Client

3. **Client 接收 Result**
   - Client 等待 Server 返回结果
   - 接收并显示 Result（接收的数据 + 成功状态）

## 🐛 故障排除

### 1. 权限错误

**问题**: `Permission denied: '/dev/ttyTHS1'`

**解决方法**: 使用 sudo 运行 Server
```bash
sudo roslaunch my_action_pkg serial_comm.launch
```

### 2. 未找到 launch 文件

**问题**: `RLException: [serial_comm.launch] is neither a launch file`

**解决方法**: 
```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
source install/setup.bash  # 注意使用 install 而不是 devel
```

### 3. 未接收到回环数据

**问题**: 接收数据为空

**可能原因**:
- 8 号和 10 号引脚未正确短接
- 串口设备未正确打开
- 波特率设置不匹配

**解决方法**:
```bash
# 检查引脚连接
# 确认 8 号引脚 (TXD0) 和 10 号引脚 (RXD0) 已短接

# 测试串口
sudo python3 -c "
import serial
ser = serial.Serial('/dev/ttyTHS1', 115200, timeout=1.0)
ser.write(b'TEST')
import time
time.sleep(0.3)
if ser.in_waiting > 0:
    print('接收:', ser.read(ser.in_waiting).decode())
else:
    print('未接收到数据')
"
```

## 📚 ROS Action 通信机制

### Action vs Service vs Topic

| 特性 | Topic | Service | Action |
|------|-------|---------|--------|
| 通信模式 | 发布/订阅 | 请求/响应 | 目标/结果/反馈 |
| 适用场景 | 实时数据流 | 简单同步操作 | 长时间异步任务 |
| 反馈机制 | 无 | 无 | 支持进度反馈 |
| 可取消性 | 无 | 无 | 支持取消任务 |
| 双向通信 | 单向 | 请求-响应 | 持续通信 |

### Action 优势

1. **进度反馈**: 可以持续向客户端报告任务进度
2. **可取消**: 客户端可以主动取消正在执行的任务
3. **长时间任务**: 适合执行耗时的操作（如串口通信、路径规划等）
4. **双向通信**: Server 和 Client 可以持续交换信息

## 🔍 代码分析

### Server 核心代码

```python
# 创建 Action Server
self.server = actionlib.SimpleActionServer(
    'serial_comm',           # Action 名称
    SerialCommAction,        # Action 类型
    self.execute,            # 执行回调
    False                    # 不自动启动
)
self.server.start()

# 执行 Goal
def execute(self, goal):
    data_to_send = goal.data.data
    
    # 发送 Feedback
    feedback = SerialCommFeedback()
    feedback.partial_data = String(data=data_to_send)
    self.server.publish_feedback(feedback)
    
    # 通过串口发送数据
    self.ser.write(data_to_send.encode('utf-8'))
    
    # 接收回环数据
    rospy.sleep(0.3)
    if self.ser.in_waiting > 0:
        received = self.ser.read(self.ser.in_waiting)
        result = SerialCommResult()
        result.received_data = String(data=received.decode())
        result.success = True
        self.server.set_succeeded(result)
```

### Client 核心代码

```python
# 创建 Action Client
self.client = actionlib.SimpleActionClient('serial_comm', SerialCommAction)
self.client.wait_for_server()

# 创建并发送 Goal
goal = SerialCommGoal()
goal.data = String(data=data)
self.client.send_goal(goal, feedback_cb=self.feedback_cb)

# 等待结果
if self.client.wait_for_result(rospy.Duration(5.0)):
    result = self.client.get_result()
    if result.success:
        print(f"成功: {result.received_data.data}")
```

## 📝 扩展建议

### 1. 添加取消功能

```python
def execute(self, goal):
    while not self.server.is_preempt_requested():
        # 执行任务
        rospy.sleep(0.1)
    
    # 检测到取消请求
    rospy.loginfo("任务被取消")
    self.server.set_preempted()
```

### 2. 添加错误重试

```python
def execute(self, goal):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 执行串口通信
            break
        except serial.SerialException as e:
            if attempt < max_retries - 1:
                rospy.logwarn(f"重试 {attempt + 1}/{max_retries}")
                rospy.sleep(1.0)
            else:
                self.server.set_aborted()
```

### 3. 支持二进制数据

```python
# Action 定义
# goal
std_msgs/String mode  # "text" 或 "binary"
std_msgs/String data  # 文本数据或 Base64 编码的二进制数据

# Server 处理
if mode == "binary":
    import base64
    binary_data = base64.b64decode(data)
    self.ser.write(binary_data)
```

## 🎯 总结

本项目演示了如何使用 ROS Action 框架实现串口通信功能。Action 相比 Topic 和 Service，更适合这种需要进度反馈和长时间操作的通信场景。

### 关键点

1. ✅ 使用 Action 框架实现服务器-客户端通信
2. ✅ 通过串口发送和接收数据
3. ✅ 支持进度反馈机制
4. ✅ 详细的代码注释便于学习和维护
5. ✅ 使用 launch 文件简化启动过程

## 📞 联系方式

如有问题或建议，请联系项目维护者。

---

**作者**: Jetson Nano Developer  
**日期**: 2026-03-30  
**版本**: 1.0.0