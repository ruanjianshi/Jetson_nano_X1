# Balance Control Package

轮腿机器人(Wheeled Legged Robot)平衡控制算法包，基于 `xqrobotV2` URDF 架构，支持 LQR/VMC/MPC/ADP 四种平衡控制算法，提供完整的运动学正逆解接口。

**2026-05-07 修订**: 所有参数和运动学模型已从 `/cfg/robot.urdf` 重新提取。

## 机器人规格 (来自 URDF)

| 参数 | 值 |
|------|-----|
| 机型 | xqrobotV2 |
| 总质量 | 12.59 kg |
| base_link | 5.408 kg |
| 单腿 link_1 | 0.174 kg |
| 单腿 link_2 | 0.673 kg |
| 单腿 link_3 | 0.420 kg |
| 单轮 | 2.323 kg |
| L1 (髋→膝) | 0.0725 m |
| L2 (膝→踝) | 0.301 m |
| 髋偏移 Y | -0.124 m |
| 髋偏移 X | ±0.069 m |
| 轮半径 | 0.10 m |

## 架构

```
IMU (/imu_serial/data) ──┬──> BalanceControlServer ──> MotorCommand (/motor/command)
                          │         │
                          │    Action Server (balance_control)
                          │         │
                          │    ┌────┴────┬────────────┐
                          │    │  LQR    │   VMC      │  MPC
                          │    │         │  ADP       │
                          │    └─────────┴────────────┘
                          │
                          └──  kinematic FK/IK (WheeledLeggedKinematics)
```

## 关节架构 (URDF)

```
base_link
  ├── left_joint_1  (revolute, axis=-X, hip_roll)   → left_link_1
  │    └── left_joint_2  (revolute, axis=+Y, hip_pitch)  → left_link_2
  │         └── left_joint_3  (revolute, axis=-Y, knee_pitch) → left_link_3
  │              └── left_joint_wheel (continuous, axis=+Y) → left_link_wheel
  └── right_joint_1 (revolute, axis=-X, hip_roll)   → right_link_1
       └── right_joint_2 (revolute, axis=-Y, hip_pitch)  → right_link_2
            └── right_joint_3 (revolute, axis=+Y, knee_pitch) → right_link_3
                 └── right_joint_wheel (continuous, axis=-Y) → right_link_wheel
```

传动接口: hip/knee 为 `EffortJointInterface`, wheel 为 `VelocityJointInterface`

## 算法

| 算法 | 说明 | 特点 |
|------|------|------|
| LQR | 线性二次调节器，状态反馈最优控制 | 计算简单，响应快 |
| VMC | 虚拟模型控制，弹簧阻尼器 | 直观易懂，稳定裕度大 |
| MPC | 模型预测控制，有限时域优化 | 能处理约束，多步预测 |
| ADP | 自适应动态规划，在线学习最优策略 | 自适应强，可在线学习 |

## 运动学模型

全部函数位于 `algorithms/wheeled_legged_kinematics.h`，关节轴已匹配 URDF:

| 关节 | 旋转轴 | 影响平面 |
|------|--------|----------|
| hip_roll (joint_1) | ±X | YZ 平面 (前后/上下) |
| hip_pitch (joint_2) | ±Y | XZ 平面 (左右/上下) |
| knee_pitch (joint_3) | ±Y | XZ 平面 (弯曲) |
| wheel (joint_w) | ±Y | 旋转 |

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

// 雅可比矩阵 (3x3, 对 hip_roll/hip_pitch/knee_pitch)
Eigen::Matrix3d J = kinematics::computeJacobian(hip_roll, hip_pitch, knee_pitch, params);

// 逆雅可比 (2D, 对 hip_pitch/knee_pitch)
Eigen::Vector2d qd = kinematics::inverseJacobian(foot_vel, hip_pitch, knee_pitch, params);

// 腿长计算 / 工作空间检查
double length = kinematics::computeLegLength(hip_pitch, knee_pitch, params);
bool ok = kinematics::isInWorkspace(hip_pitch, knee_pitch, params);

// 关节插值
LegJoints interp = kinematics::interpolateJoints(pose_a, pose_b, 0.5, params);
```

### 编译运动学测试

```bash
cd /home/jetson/Desktop/Jetson_Nano
g++ -std=c++17 -DUSE_YAML_CPP \
    -Iaction_ws/src/balance_control/algorithms \
    -I/usr/include/eigen3 \
    action_ws/src/balance_control/algorithms/kinematics_test.cpp \
    -lyaml-cpp -o kinematics_test

./kinematics_test
```

## ADP算法

ADP (Adaptive Dynamic Programming) 是一种基于强化学习的自适应控制算法，包含三个神经网络:

1. **Critic Network** - 近似价值函数 V(s)，TD学习更新，学习率 0.005
2. **Action Network** - 近似最优策略 π(s)，学习率 0.01
3. **Target Critic Network** - 目标网络，稳定训练

特点: 在线自适应学习，无需精确模型，折扣因子 γ = 0.99

```bash
rosrun balance_control robot_command_client _algorithm:=3
```

## Action 接口

**Action名称**: `balance_control`

**Goal**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `command` | uint8 | 0=STOP, 1=ENABLE, 2=DISABLE, 3=SWITCH_ALGO, 4=SET_TARGET |
| `algorithm` | uint8 | 0=LQR, 1=VMC, 2=MPC, 3=ADP |
| `target_roll` | float64 | 目标横滚角 (rad) |
| `target_pitch` | float64 | 目标俯仰角 (rad) |
| `target_yaw` | float64 | 目标偏航角 (rad) |
| `target_speed` | float64 | 目标速度 m/s (预留) |
| `target_yaw_rate` | float64 | 目标偏航率 rad/s (预留) |

**Feedback**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_roll/pitch/yaw` | float64 | 当前姿态 |
| `joint_positions` | float64[] | 关节位置 |
| `joint_torques` | float64[] | 输出力矩 |
| `algorithm_name` | string | 当前算法 |
| `control_enabled` | bool | 控制状态 |
| `status_message` | string | 状态信息 |

**Result**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 执行结果 |
| `message` | string | 结果消息 |

## 硬件参数

配置文件:

| 文件 | 内容 |
|------|------|
| `config/robot_hardware_params.yaml` | 质量/几何/电机ID/限幅/PID/控制频率 |
| `config/robot_config.yaml` | 电机详细参数 (ethercat_id, can_node_id, torque_limit) |
| `config/wheeled_legged_kinematics.yaml` | 运动学参数 (L1/L2/偏移/限位/步态) |
| `cfg/robot.urdf` | 原始URDF模型 (xqrobotV2, 9个link, 8个joint) |

电机参数 (URDF提取):

| 电机型号 | 最大力矩 | 最大速度 | 使用关节 |
|----------|----------|----------|----------|
| R86 | 80 Nm | 27.23 rad/s | hip_roll, hip_pitch |
| R52 | 19 Nm | 13.61 rad/s | knee_pitch, wheel |

关节软限位 (URDF提取):

| 关节 | 最小 | 最大 |
|------|------|------|
| hip_roll | -3.1416 | 3.1416 |
| hip_pitch | -2.0944 | 2.0944 |
| knee_pitch | -0.8727 | 0.8727 |
| wheel | -50.0 | 50.0 |

## 客户端

### C++ 客户端 (`robot_command_client`)

```bash
rosrun balance_control robot_command_client _command:=1 _speed:=0.5
rosrun balance_control robot_command_client _command:=3 _yaw_rate:=1.0
rosrun balance_control robot_command_client _continuous:=true
```

### Python 客户端

```bash
# 高层命令客户端
rosrun balance_control robot_command_client.py _command:=1 _speed:=0.5

# 键盘遥控 (WASD移动, QE转向, 空格跳跃)
rosrun balance_control robot_keyboard_teleop.py

# 命令行接口
rosrun balance_control robot_cli.py move forward 0.5
rosrun balance_control robot_cli.py turn left 1.0
rosrun balance_control robot_cli.py stop
```

## 启动

```bash
# catkin_make 编译后启动
cd ~/Desktop/Jetson_Nano/action_ws
source devel/setup.bash

# 方式1: 直接启动服务器
rosrun balance_control balance_control_server

# 方式2: launch文件 (含IMU/DCU驱动)
roslaunch balance_control balance_control.launch

# 发送模拟IMU数据 (无硬件时)
rostopic pub /imu_serial/data sensor_msgs/Imu "{orientation: {x: 0, y: 0, z: 0, w: 1}}" -r 50
```

launch参数:

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `hardware_params_file` | `$(find balance_control)/config/robot_hardware_params.yaml` | 配置文件路径 |
| `algorithm` | 0 | 算法选择 (0=LQR, 1=VMC, 2=MPC, 3=ADP) |
| `target_roll/pitch/yaw` | 0.0 | 初始目标姿态 rad |
| `control_frequency` | 500 | 控制频率 Hz |

## 坐标系定义

```
Body Frame (机体坐标系):
  Z (上)
  ↑   Y (后方)
  │  ↗
  └──→ X (右)

关节旋转轴 (严格匹配 URDF):
  hip_roll  (joint_1)  - 绕 ±X 轴 → 腿在 YZ 平面摆动
  hip_pitch (joint_2)  - 绕 ±Y 轴 → 腿在 XZ 平面摆动
  knee_pitch(joint_3)  - 绕 ±Y 轴 → 小腿弯曲
  wheel     (joint_w)  - 绕 ±Y 轴 → 轮子转动

平衡姿态:
  Roll (横滚)  = 绕 X 轴 (左右倾斜, hip_roll 修正)
  Pitch (俯仰) = 绕 Y 轴 (前后倾斜, hip_pitch 修正)
  Yaw (偏航)   = 绕 Z 轴 (转向, 差速轮控制)
```

## 文件结构

```
balance_control/
├── algorithms/
│   ├── balance_algorithm_base.h        # 算法基类
│   ├── lqr_controller.h/cpp            # LQR
│   ├── vmc_controller.h/cpp            # VMC
│   ├── mpc_controller.h/cpp            # MPC
│   ├── adp_controller.h/cpp            # ADP
│   ├── wheeled_legged_kinematics.h     # 运动学 (正逆解/雅可比)
│   └── kinematics_test.cpp             # 运动学测试
├── action/
│   └── BalanceControl.action           # Action 定义
├── include/
│   ├── robot_command_client.h          # C++ 客户端
│   └── robot_hardware_params.h         # 硬件参数类
├── src/
│   ├── balance_control_server.cpp      # Action 服务器 (主节点)
│   ├── robot_command_client.cpp        # C++ 客户端实现
│   ├── robot_hardware_params.cpp       # 硬件参数加载
│   └── balance_control_test.cpp        # 测试节点
├── scripts/
│   ├── robot_command_client.py         # Python 客户端
│   ├── robot_keyboard_teleop.py        # 键盘遥控
│   └── robot_cli.py                    # 命令行接口
├── config/
│   ├── robot_hardware_params.yaml      # 硬件参数 (URDF提取)
│   ├── robot_config.yaml               # 电机详细参数
│   └── wheeled_legged_kinematics.yaml  # 运动学参数 (URDF提取)
├── cfg/
│   ├── robot.urdf                      # xqrobotV2 URDF 模型
│   └── BalanceControl.cfg              # 动态参数配置
├── launch/
│   ├── balance_control.launch           # 主启动文件
│   └── balance_control_test.launch      # 测试启动文件
├── msg/
│   └── RobotCommand.msg                # 机器人命令消息
└── package.xml
```

## 依赖

- ROS Noetic
- Eigen3
- yaml-cpp
- dcu_driver_pkg (电机驱动)
- yb_imu_driver (IMU驱动)

## 开发

```bash
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make

# 终端1: roscore
roscore

# 终端2: 启动服务器
source devel/setup.bash
rosrun balance_control balance_control_server

# 终端3: 模拟IMU + 发送命令
source devel/setup.bash
rostopic pub /imu_serial/data sensor_msgs/Imu "{orientation: {x: 0, y: 0, z: 0, w: 1}}" -r 50
```

## 修订记录

| 日期 | 修订内容 |
|------|----------|
| 2026-05-06 | 初始版本 |
| 2026-05-07 | URDF匹配: 运动学关节轴修正 (hip_pitch/knee/wheel 绕Y轴), 几何参数从URDF提取, 质量/限幅修正, 关节命名统一为 left_joint_*/right_joint_*, Action字段重构 (command/algorithm), 算法output统一8维, 各算法实现精度修正 |
