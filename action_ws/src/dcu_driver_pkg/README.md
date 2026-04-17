# DCU Driver 开发文档

## 项目概述

本文档记录 Jetson Nano B01 控制智元科技 X1 机器人 DCU (EtherCAT to CANFD 网关) 的开发过程和踩坑经验。

## 目录

- [硬件配置](#硬件配置)
- [架构](#架构)
- [XyberController API](#xybercontroller-api)
- [数据类型](#数据类型)
- [代码结构](#代码结构)
- [运行](#运行)
- [CANFD 报文格式](#canfd-报文格式)
- [踩坑记录](#踩坑记录)
- [维护](#维护)

## 硬件配置

- **平台**: Jetson Nano B01 (4GB RAM)
- **DCU**: 智元科技 X1 机器人控制器
- **电机**: PowerFlow R86
- **通信**: EtherCAT (Jetson Nano) → DCU → CANFD (电机)

## 架构

```
Jetson Nano (EtherCAT)
      ↓
   DCU (网关)
      ↓
CANFD → R86 电机 (CTRL1)
      ↓
CAN 分析仪 (测试用)
```

## XyberController API

XyberController 是单例模式，通过 `GetInstance()` 获取实例。

### 头文件

```cpp
#include "xyber_controller.h"
```

### 核心 API

#### 获取实例

```cpp
xyber::XyberController* ctrl = xyber::XyberController::GetInstance();
```

#### 创建 DCU

```cpp
bool CreateDcu(std::string name, uint8_t ethercat_id);
```

**参数**:
- `name`: DCU 名称 (如 "dcu1")
- `ethercat_id`: EtherCAT 从站 ID (通常为 1)

**示例**:
```cpp
ctrl->CreateDcu("dcu1", 1);
```

#### 挂载执行器

```cpp
bool AttachActuator(std::string dcu_name, CtrlChannel ch, ActuatorType type,
                     std::string actuator_name, uint8_t can_id);
```

**参数**:
- `dcu_name`: DCU 名称
- `ch`: CANFD 通道 (CTRL_CH1, CTRL_CH2, CTRL_CH3)
- `type`: 执行器类型 (POWER_FLOW_R86, POWER_FLOW_R52, etc.)
- `actuator_name`: 执行器名称 (如 "joint1", "joint3")
- `can_id`: CAN 总线上的 ID

**示例**:
```cpp
ctrl->AttachActuator("dcu1", xyber::CtrlChannel::CTRL_CH1,
                     xyber::ActuatorType::POWER_FLOW_R86, "joint3", 3);
```

#### 设置实时参数

```cpp
bool SetRealtime(int rt_priority, int bind_cpu);
```

**参数**:
- `rt_priority`: 线程优先级 [0-99]，99 最高，-1 禁用
- `bind_cpu`: 绑定的 CPU 核心，-1 禁用

**示例**:
```cpp
ctrl->SetRealtime(90, 1);  // 优先级 90，绑定 CPU 1
```

#### 启动 EtherCAT

```cpp
bool Start(std::string ifname, uint64_t cycle_ns, bool enable_dc);
```

**参数**:
- `ifname`: 网卡名称 (如 "eth0")
- `cycle_ns`: 循环周期 (纳秒)，1000000 = 1ms = 1000Hz
- `enable_dc`: 是否启用分布式时钟

**示例**:
```cpp
ctrl->Start("eth0", 1000000, true);  // 1ms 周期，启用 DC
```

#### 停止 EtherCAT

```cpp
void Stop();
```

### 执行器控制 API

#### 使能执行器

```cpp
bool EnableActuator(const std::string& name);
bool EnableAllActuator();
```

#### 禁用执行器

```cpp
bool DisableActuator(const std::string& name);
bool DisableAllActuator();
```

#### 设置模式

```cpp
bool SetMode(const std::string& name, ActautorMode mode);
```

**模式类型**:
| 模式 | 值 | 说明 |
|------|------|------|
| MODE_CURRENT | 0 | 电流模式 |
| MODE_CURRENT_RAMP | 1 | 电流斜坡模式 |
| MODE_VELOCITY | 2 | 速度模式 |
| MODE_VELOCITY_RAMP | 3 | 速度斜坡模式 |
| MODE_POSITION | 4 | 位置模式 |
| MODE_POSITION_RAMP | 5 | 位置斜坡模式 |
| MODE_MIT | 6 | MIT 模式 (力控) |

**示例**:
```cpp
ctrl->SetMode("joint3", xyber::ActautorMode::MODE_MIT);
```

#### 获取状态

```cpp
ActautorState GetPowerState(const std::string& name);
ActautorMode GetMode(const std::string& name);
```

**状态类型**:
| 状态 | 值 | 说明 |
|------|------|------|
| STATE_DISABLE | 0 | 禁用 |
| STATE_ENABLE | 1 | 使能 |
| STATE_CALIBRATION | 2 | 校准中 |

#### 获取位置/速度/力矩

```cpp
float GetPosition(const std::string& name);   // 返回 rad
float GetVelocity(const std::string& name);   // 返回 rad/s
float GetEffort(const std::string& name);    // 返回 Nm
float GetTempure(const std::string& name);   // 返回 温度
```

#### MIT 模式控制 (核心)

```cpp
void SetMitCmd(const std::string& name, float pos, float vel, float effort, float kp, float kd);
```

**参数**:
| 参数 | 单位 | 说明 |
|------|------|------|
| pos | rad | 目标位置 |
| vel | rad/s | 目标速度 |
| effort | Nm | 目标力矩 |
| kp | - | 刚度系数 |
| kd | - | 阻尼系数 |

**示例**:
```cpp
// 位置 3.14rad，刚度 50，阻尼 1
ctrl->SetMitCmd("joint3", 3.14f, 0.0f, 0.0f, 50.0f, 1.0f);
```

#### 设置 MIT 参数

```cpp
void SetMitParam(const std::string& name, MitParam param);
```

**MitParam 结构体**:
```cpp
struct MitParam {
    float pos_min, pos_max;   // 位置限制
    float vel_min, vel_max;   // 速度限制
    float toq_min, toq_max;   // 力矩限制
    float kp_min, kp_max;     // 刚度限制
    float kd_min, kd_max;     // 阻尼限制
};
```

### IMU API

```cpp
DcuImu GetDcuImuData(const std::string& name);
void ApplyDcuImuOffset(const std::string& name);
```

**DcuImu 结构体**:
```cpp
struct DcuImu {
    float acc[3];      // 加速度
    float gyro[3];      // 陀螺仪
    float quat[4];      // 四元数
};
```

### 原始 CANFD 数据

```cpp
void GetRawCanfdData(const std::string& actuator_name, CtrlChannel ch, uint8_t* data, size_t* len);
```

获取指定通道的原始 64 字节 CANFD 数据。

## 数据类型

### CtrlChannel (CANFD 通道)

```cpp
enum class CtrlChannel : uint8_t {
    CTRL_CH1 = 0,   // 通道1
    CTRL_CH2 = 1,    // 通道2
    CTRL_CH3 = 2,    // 通道3
};
```

### ActuatorType (执行器类型)

```cpp
enum class ActuatorType {
    POWER_FLOW_R86,   // R86 电机
    POWER_FLOW_R52,   // R52 电机
    POWER_FLOW_L28,   // L28 电机
    OMNI_PICKER,      //  picker
    UNKOWN,
};
```

### ActautorState (执行器状态)

```cpp
enum ActautorState : uint8_t {
    STATE_DISABLE = 0,
    STATE_ENABLE = 1,
    STATE_CALIBRATION = 2,
};
```

### ActautorMode (控制模式)

```cpp
enum ActautorMode : uint8_t {
    MODE_CURRENT = 0,
    MODE_CURRENT_RAMP = 1,
    MODE_VELOCITY = 2,
    MODE_VELOCITY_RAMP = 3,
    MODE_POSITION = 4,
    MODE_POSITION_RAMP = 5,
    MODE_MIT = 6,       // 力控模式
};
```

## 关键发现

### 1. DCU 的 Cmd 字段控制转发行为

DCU 的 CANFD 转发由 `Cmd` 字段控制：
- `Cmd = 0xFF`: 广播模式，强制转发 64 字节到 CAN ID 0
- `Cmd = 0`: 静默模式，不转发
- `Cmd = bitN`: 单播模式，bit0 对应 CAN ID 1

### 2. CANFD 是查询-响应协议

DCU 不会主动发送 CANFD 报文。需要先发送命令，电机才会回传数据。

### 3. 没有电机时 DCU 行为

- 没有连接电机时，DCU 可能只响应简单的查询命令 (SetMode/Enable)
- 没有电机响应时，DCU 可能停止转发后续的 MIT 控制命令
- 这不是代码问题，是硬件/协议特性

### 4. 持续发送 vs 单次发送

**关键经验**：EtherCAT 需要持续循环发送 PDO 数据才能维持 DCU 的转发状态。

- 预编译测试程序 `canfd_forward_test` 使用 `while(1)` 循环持续发送 MIT 命令，工作正常
- catkin 构建的节点单次调用 `SetMitCmd` 可能无法触发 DCU 转发
- **解决方案**：启动一个后台线程持续发送 MIT 命令，Topic 回调只更新目标值

## 代码结构

```
dcu_driver_pkg/
├── src/
│   ├── dcu_driver_server.cpp      # 主节点 (ROS Action + Topic)
│   └── dcu_control_node.cpp      # 简化版 Topic 节点
├── launch/
│   ├── dcu_driver_server.launch   # 服务端启动
│   └── dcu_driver_client.launch   # 客户端启动
├── action/
│   └── DCUControl.action          # Action 定义
└── CMakeLists.txt
```

## 运行

### 1. 启动服务端

```bash
source /opt/ros/noetic/setup.bash
source devel/setup.bash
roslaunch dcu_driver_pkg dcu_driver_server.launch ethercat_if:=eth0
```

### 2. Topic 控制 (推荐)

```bash
# 格式: [position, kp, kd]
rostopic pub /dcu_cmd std_msgs/Float64MultiArray "data: [3.14, 50, 1]"
```

### 3. Action 控制

```bash
rostopic pub /dcu_control/goal dcu_driver_pkg/DCUControlActionGoal \
  '{goal: {joint_names: ["joint3"], positions: [3.14], velocities: [0], efforts: [0], stiffness: [50], damping: [1]}}' --once
```

### 4. 监控状态

```bash
rostopic echo /joint_states
```

## CANFD 报文格式

### MIT 模式 (8字节)

| 字节 | 名称 | 说明 |
|------|------|------|
| 0-1 | Position | 位置 (float) |
| 2-3 | Velocity/KP | 速度/刚度 |
| 4-5 | Torque/KD | 力矩/阻尼 |
| 6-7 | 保留 | - |

### 常用命令

| 命令 | 数据 | 说明 |
|------|------|------|
| SetMode | `0B 06` | 设置 MIT 模式 |
| Enable | `01 01` | 使能电机 |

## 踩坑记录

### 问题 1: PDO 大小不匹配

**错误信息**:
```
CmdType N5xyber13DcuSendPacketE size does not match. target 240, actual 0
```

**原因**: SOEM 没有正确读取 DCU 的 PDO 配置

**解决**: 
- 确保 DCU 已上电 (48V)
- 检查 EtherCAT 网线连接
- 重启 DCU 和 Jetson Nano

### 问题 2: catkin 构建的库与预编译库行为不同

**现象**: 
- 预编译测试程序 `canfd_forward_test` 能正常工作
- catkin 构建的 `dcu_driver_server` 不能正常发送 MIT 命令

**原因**: 可能与编译选项或内存布局有关

**解决**: 使用持续发送模式，而非单次调用

### 问题 3: 没有电机时 DCU 停止转发

**现象**: 第一次发送命令后能收到，但后续发送无效

**原因**: DCU 需要电机的心跳响应来维持转发状态

**解决**: 连接电机后测试

## 测试工具

### 预编译测试程序

```bash
sudo /home/jetson/Desktop/Jetson_Nano/action_ws/src/dcu_driver_pkg/agibot_x1_infer/src/module/dcu_driver_module/xyber_controller/build/install/bin/canfd_forward_test eth0 joint3 3
```

### CAN 分析仪设置

- 仲裁段波特率: 1M
- 数据段波特率: 5M
- 协议: CANFD

## 维护

### 清理进程

```bash
pkill -9 -f dcu_driver
pkill -9 -f xyber
```

### 清理 ROS 日志

```bash
rm -rf ~/.ros/log/*
```

### 重新构建

```bash
cd ~/Desktop/Jetson_Nano/action_ws
source /opt/ros/noetic/setup.bash
catkin_make --pkg dcu_driver_pkg
```

## 参考

- XyberController SDK
- SOEM (Simple Open EtherCAT Master)
- ROS Action 通信机制
- CANFD 协议