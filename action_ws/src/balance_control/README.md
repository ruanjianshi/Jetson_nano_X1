# Balance Control Package

轮腿机器人(Wheeled Legged Robot)平衡控制算法包，支持LQR、VMC、MPC、ADP四种平衡控制算法，提供完整的运动学正逆解接口。

## 架构

```
IMU (/imu_serial/data) ──┬──> BalanceControlServer ──> MotorCommand (/motor/command)
                          │
                          └── Action Server (balance_control)
                                └── robot_command_client (客户端)
```

## 算法

| 算法 | 说明 | 特点 |
|------|------|------|
| LQR | 线性二次调节器，状态反馈最优控制 | 计算简单，响应快 |
| VMC | 虚拟模型控制，弹簧阻尼器 | 直观易懂，稳定裕度大 |
| MPC | 模型预测控制，有限时域优化 | 能处理约束，多步预测 |
| ADP | 自适应动态规划，在线学习最优策略 | 自适应强，可在线学习 |

## 运动学模型

提供完整的轮腿机器人运动学正逆解算法。

### 头文件
`algorithms/wheeled_legged_kinematics.h`

### 主要接口

```cpp
#include "wheeled_legged_kinematics.h"

kinematics::KinematicsParams params;

// 从YAML加载参数
kinematics::loadFromYaml("/path/to/config.yaml", params);

// 打印参数
kinematics::printParams(params);

// 正向运动学 (关节角度 -> 足端位置)
FootPose foot = kinematics::forwardKinematics(hip_roll, hip_pitch, knee_pitch, LegSide::LEFT, params);

// 逆向运动学 (足端位置 -> 关节角度)
Vec3 target_pos = {0, -0.3, 0.25};
LegJoints joints = kinematics::inverseKinematics(target_pos, LegSide::LEFT, params);

// 基于高度的反向运动学
LegJoints joints = kinematics::inverseKinematicsForHeight(body_height, body_pitch, LegSide::LEFT, params);

// 雅可比矩阵
Eigen::Matrix3d J = kinematics::computeJacobian(hip_pitch, knee_pitch, params);

// 腿长计算
double length = kinematics::computeLegLength(hip_pitch, knee_pitch, params);

// 工作空间检查
bool ok = kinematics::isInWorkspace(hip_pitch, knee_pitch, params);

// 关节角度插值
LegJoints interp = kinematics::interpolateJoints(pose_a, pose_b, 0.5, params);
```

### 运动学配置文件
`config/wheeled_legged_kinematics.yaml`

包含参数：
- 腿部长度 (L1, L2)
- 髋关节偏移
- 轮子参数
- 关节限位
- 步态参数

### 编译运动学测试程序

```bash
cd /home/jetson/Desktop/Jetson_Nano
g++ -std=c++17 -DUSE_YAML_CPP \
    -Iaction_ws/src/balance_control/algorithms \
    -I/usr/include/eigen3 \
    action_ws/src/balance_control/algorithms/kinematics_test.cpp \
    -lyaml-cpp -o kinematics_test

./kinematics_test
```

## ADP算法说明

ADP (Adaptive Dynamic Programming，自适应动态规划) 是一种基于强化学习的自适应控制算法。

### 核心组件

1. **Critic Network (评价网络)**
   - 近似最优价值函数 V(s)
   - 通过TD学习更新权重
   - 学习率: 0.005

2. **Action Network (动作网络)**
   - 近似最优策略 π(s)
   - 根据评价网络梯度更新
   - 学习率: 0.01

### 特性

- 在线自适应学习
- 无需精确系统模型
- 通过与环境交互学习最优控制策略
- 折扣因子 γ = 0.99

### 使用方法

```cpp
// 算法ID为3选择ADP
balance_control::BalanceControlGoal goal;
goal.algorithm_id = 3;  // ADP
goal.enable_control = true;

// 或通过命令行
rosrun balance_control robot_command_client _algorithm:=3
```

## Action 接口

**Action名称**: `balance_control`

**Goal**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `algorithm_id` | uint8 | 0=LQR, 1=VMC, 2=MPC |
| `enable_control` | bool | true=启用, false=停用控制 |
| `target_roll` | float64 | 目标横滚角 (rad) |
| `target_pitch` | float64 | 目标俯仰角 (rad) |
| `target_yaw` | float64 | 目标偏航角 (rad) |

**Feedback**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `current_roll/pitch/yaw` | float64 | 当前姿态 |
| `joint_positions` | float64[] | 关节位置 |
| `torques` | float64[] | 输出力矩 |
| `algorithm_name` | string | 当前算法 |
| `control_enabled` | bool | 控制状态 |
| `status_message` | string | 状态信息 |

**Result**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 执行结果 |
| `message` | string | 结果消息 |

## 硬件参数

配置文件位于 `config/robot_hardware_params.yaml`，包含：

- **机器人基本参数**: 质量、重力加速度
- **腿部几何参数**: 大腿/小腿长度、髋关节偏移
- **轮子参数**: 轮子半径、轮距、最大轮速
- **IMU配置**: 安装位置、旋转偏移、中性姿态、平衡角度限制
- **电机配置**: 8个电机的ID、通道、类型、方向
- **电机限幅**: R86/R52型号的最大力矩、速度、位置限制
- **关节软限位**: 各关节的位置软限制
- **标零位置**: 各关节的零位偏移
- **PID参数**: Roll/Pitch/Yaw的PID增益
- **控制参数**: 控制频率、EtherCAT配置

## 客户端

### C++ 客户端 (robot_command_client)

高层命令客户端，支持前进、后退、转向、跳跃等命令。

```bash
# 前进 0.5m/s
rosrun balance_control robot_command_client _command:=1 _speed:=0.5

# 左转 1.0 rad/s
rosrun balance_control robot_command_client _command:=3 _yaw_rate:=1.0

# 持续模式 (订阅 /cmd_vel)
rosrun balance_control robot_command_client _continuous:=true
```

### Python 客户端

#### robot_command_client.py
高层命令客户端。

```bash
rosrun balance_control robot_command_client.py _command:=1 _speed:=0.5
```

#### robot_keyboard_teleop.py
键盘遥控，支持 WASD 移动、QE 转向，空格跳跃。

```bash
rosrun balance_control robot_keyboard_teleop.py

# 键盘控制:
# W/S: 前进/后退
# A/D: 左/右转向
# Q/E: 原地左/右转
# 空格: 跳跃
# X: 停止
# 1-9: 速度等级
```

#### robot_cli.py
命令行接口，适合脚本和调试。

```bash
rosrun balance_control robot_cli.py move forward 0.5
rosrun balance_control robot_cli.py turn left 1.0
rosrun balance_control robot_cli.py stop
rosrun balance_control robot_cli.py balance
```

## 文件结构

```
balance_control/
├── algorithms/
│   ├── balance_algorithm_base.h      # 算法基类接口
│   ├── lqr_controller.h/cpp           # LQR控制器
│   ├── vmc_controller.h/cpp           # VMC控制器
│   ├── mpc_controller.h/cpp           # MPC控制器
│   ├── adp_controller.h/cpp           # ADP控制器
│   ├── wheeled_legged_kinematics.h    # 运动学模型 (正逆解)
│   └── kinematics_test.cpp            # 运动学测试程序
├── action/
│   └── BalanceControl.action          # Action定义
├── include/
│   ├── robot_command_client.h         # C++命令客户端
│   └── robot_hardware_params.h        # 硬件参数类
├── src/
│   ├── balance_control_server.cpp     # Action服务器 (主节点)
│   ├── robot_command_client.cpp       # C++命令客户端
│   ├── robot_hardware_params.cpp      # 硬件参数实现
│   └── balance_control_test.cpp       # 测试节点
├── scripts/
│   ├── robot_command_client.py        # Python命令客户端
│   ├── robot_keyboard_teleop.py       # 键盘遥控
│   └── robot_cli.py                   # 命令行接口
├── config/
│   ├── robot_hardware_params.yaml     # 硬件参数配置
│   └── wheeled_legged_kinematics.yaml # 运动学参数配置
├── launch/
│   ├── balance_control.launch         # 主启动文件
│   └── balance_control_test.launch    # 测试启动文件
├── msg/
│   └── RobotCommand.msg               # 机器人命令消息
└── package.xml
```

## 启动

### 主服务器

```bash
rosrun balance_control balance_control_server
```

启动时自动加载 `config/robot_hardware_params.yaml` 配置。

参数:
- `hardware_params_file`: 硬件参数YAML文件路径 (可选)

### 测试节点

```bash
rosrun balance_control balance_control_test
```

### 发送模拟IMU数据

```bash
rostopic pub /imu_serial/data sensor_msgs/Imu "{orientation: {x: 0, y: 0, z: 0, w: 1}}" -r 50
```

## 坐标系定义

```
Body Frame (机体坐标系):
  Z (上)
  ^   Y (后/前进方向)
  |  /
  | /
  +----> X (右)

腿部关节:
  髋横滚 (Hip Roll)  - 绕Y轴旋转，控制腿部外展/内收
  髋俯仰 (Hip Pitch) - 绕X轴旋转，控制大腿前摆/后摆
  膝俯仰 (Knee Pitch) - 绕X轴旋转，控制小腿后摆/前摆
  轮子 (Wheel)       - 绕X轴旋转，驱动轮子转动
```

## 依赖

- ROS Noetic
- Eigen3
- yaml-cpp
- dcu_driver_pkg (电机驱动)
- yb_imu_driver (IMU驱动)

## 开发

### 编译

```bash
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make
```

### 运行测试

```bash
# 终端1: 启动roscore
roscore

# 终端2: 启动平衡控制服务器
source devel/setup.bash
rosrun balance_control balance_control_server

# 终端3: 发送命令
source devel/setup.bash
rostopic pub /imu_serial/data sensor_msgs/Imu "{orientation: {x: 0, y: 0, z: 0, w: 1}}" -r 50
```