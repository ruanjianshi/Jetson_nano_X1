# DCU Driver 开发文档

## 项目概述

本项目实现 Jetson Nano B01 通过 EtherCAT 控制智元科技 PowerFlow R 系列执行器的驱动框架。

**参考协议**: [智元 PowerFlow R 系列执行器产品手册](https://www.agibot.com.cn/DOCS/PM/PFR)

## 目录

- [硬件配置](#硬件配置)
- [协议参数](#协议参数)
- [架构](#架构)
- [SDK API](#sdk-api)
- [消息格式](#消息格式)
- [控制方式](#控制方式)
- [数据类型](#数据类型)
- [代码结构](#代码结构)
- [运行](#运行)
- [CANFD 报文格式](#canfd-报文格式)
- [踩坑记录](#踩坑记录)
- [维护](#维护)

## 硬件配置

- **平台**: Jetson Nano B01 (4GB RAM, aarch64)
- **DCU**: 智元科技 X1 域控制器 (EtherCAT to CANFD 网关)
- **电机**: PowerFlow R86-2 (x2) + R52 (x2)
- **通信**: EtherCAT (Jetson Nano) → DCU → CANFD (电机)

### 硬件连接

```
DCU CTRL1 通道 → 串联 R86-2 #1 (CAN ID=3) + R86-2 #2 (CAN ID=2)
DCU CTRL2 通道 → 串联 R52 #1 (CAN ID=3) + R52 #2 (CAN ID=5)
```

### 电机参数

| 参数 | R86-2 | R52 |
|------|-------|-----|
| 减速比 | 16 | 36 |
| 极对数 | 14 | 7 |
| 力矩系数 | 1.366 Nm/A | 2.040 Nm/A |
| 额定转矩 | 20 Nm | 6 Nm |
| 峰值转矩 | 80 Nm | 19 Nm |
| 电流限幅 | 20 A | 8 A |
| 速度限幅 | 37.7 rad/s | 25.1 rad/s |
| 力矩限幅 | ±100 Nm | ±50 Nm |

## 协议参数

智元 PowerFlow R 系列执行器协议关键参数：

| 参数 | 最小值 | 最大值 | 单位 |
|------|--------|--------|------|
| Position | -6.28 | 6.28 | rad |
| Velocity | -12.56 | 12.56 | rad/s |
| Torque (R86) | -100 | 100 | Nm |
| Torque (R52) | -50 | 50 | Nm |
| Kp (刚度) | 0 | 500 | - |
| Kd (阻尼) | 0 | 8 | - |

**CANFD 通信参数**:
- 仲裁段波特率: 1Mbps
- 数据段波特率: 5Mbps
- 采样点: 80% (仲裁段) / 75% (数据段)

### 电机实际参数 (joint3 - PowerFlow R)

通过 Python SDK 读取的电机实际参数：

**基本信息**:
| 参数 | 值 |
|------|-----|
| device_type | 4 |
| serial_number | 0000395A464D |
| fw_version | 329 |
| can_node_id | 3 |
| encoder_type | 3 |

**MIT 协议限制**:
| 参数 | 最小值 | 最大值 | 单位 |
|------|--------|--------|------|
| pos_min | -6.283 | 6.283 | rad |
| pos_max | ±6.283 | ±6.283 | rad |
| vel_min | -12.566 | 12.566 | rad/s |
| vel_max | ±12.566 | ±12.566 | rad/s |
| tor_min | -100 | 100 | Nm |
| tor_max | ±100 | ±100 | Nm |
| kp_min | 0 | 500 | - |
| kp_max | 0 | 500 | - |
| kd_min | 0 | 8 | - |
| kd_max | 0 | 8 | - |

**控制参数**:
| 参数 | 值 |
|------|-----|
| ctrl_mode | 6 (MIT) |
| current_ctrl_bandwidth | 1000 Hz |
| current_limit | 20 A |
| velocity_limit | 37.7 rad/s |
| protect_over_speed | 62.83 rad/s |
| protect_over_heat | 80°C |
| protect_over_current | 15 A |

**电机特性**:
| 参数 | 值 |
|------|-----|
| reduction | 16.0 |
| polar_pair | 14 |
| phase_resistance | 0.08 Ω |
| phase_inductance | 80 µH |
| inertia | 0.000159 kg·m² |

## 架构

```
Jetson Nano (EtherCAT)
       ↓
    DCU (网关)
       ↓
CANFD → PowerFlow R 执行器 (ID 1-8)
```

## SDK API (XyberController)

**头文件**: `xyber_controller.h`

### 执行器控制

```cpp
// 使能/禁能
bool EnableActuator(const std::string& name);
bool DisableActuator(const std::string& name);

// 设置控制模式
bool SetMode(const std::string& name, ActautorMode mode);

// MIT 模式控制 (唯一的控制指令)
void SetMitCmd(const std::string& name, float pos, float vel, float effort, float kp, float kd);
```

### 状态读取

```cpp
float GetPosition(const std::string& name);   // rad
float GetVelocity(const std::string& name);   // rad/s
float GetEffort(const std::string& name);     // Nm
ActautorState GetPowerState(const std::string& name);
ActautorMode GetMode(const std::string& name);
```

## 消息格式

### MotorCommand.msg

```bash
# 使能电机 (指定通道和型号)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 3, channel: 1, motor_type: 'POWER_FLOW_R86'}"

# 设置MIT模式
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 3, channel: 1, mode: 6}"

# MIT控制
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 3, channel: 1, q: 0.5, kp: 20.0, kd: 2.0}"
```

| 字段 | 类型 | 说明 |
|------|------|------|
| cmd | uint8 | 1=使能, 2=禁能, 3=设置模式, 4=MIT控制 |
| motor_id | uint8 | 电机 CAN ID (1-8) |
| channel | uint8 | CAN通道: 1=CTRL1, 2=CTRL2, 3=CTRL3 |
| motor_type | string | 电机型号: POWER_FLOW_R86/R52/R28 (可选,用于校验) |
| mode | uint8 | 控制模式 (仅cmd=3时) |
| q | float32 | 目标位置 (rad), MIT控制 |
| dq | float32 | 目标速度 (rad/s), MIT控制 |
| tau | float32 | 目标力矩 (Nm), MIT控制 |
| kp | float32 | 刚度 (0-500), MIT控制 |
| kd | float32 | 阻尼 (0-8), MIT控制 |

### CAN通道常量

| 常量 | 值 | 说明 |
|------|---|------|
| CHANNEL_CTRL1 | 1 | CTRL1通道 (连接R86-2) |
| CHANNEL_CTRL2 | 2 | CTRL2通道 (连接R52) |
| CHANNEL_CTRL3 | 3 | CTRL3通道 |

### 电机定位

电机通过 `channel + motor_id` 组合精确定位，支持型号校验：

```bash
# CTRL1通道 R86-2电机 (motor_id=3)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 3, channel: 1, motor_type: 'POWER_FLOW_R86', q: 0.5, kp: 20.0, kd: 2.0}"

# CTRL2通道 R52电机 (motor_id=5)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 5, channel: 2, motor_type: 'POWER_FLOW_R52', q: 0.0, kp: 10.0, kd: 1.0}"
```

### 控制模式 (通过 SetMode 设置)

| Mode | 名称 | 说明 |
|------|------|------|
| 0 | MODE_CURRENT | 电流环模式 |
| 1 | MODE_CURRENT_RAMP | 电流环梯形加减速 |
| 2 | MODE_VELOCITY | 速度环模式 |
| 3 | MODE_VELOCITY_RAMP | 速度环梯形加减速 |
| 4 | MODE_POSITION | 位置环模式 |
| 5 | MODE_POSITION_RAMP | 位置环梯形加减速 |
| 6 | MODE_MIT | MIT混合控制模式 (默认) |

## 控制方式

### Topic 控制

**控制流程**: 使能 → 设置模式 → MIT控制

```bash
# Step 1: 使能电机 (指定通道+型号)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 2, channel: 1, motor_type: 'POWER_FLOW_R86'}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 3, channel: 1, motor_type: 'POWER_FLOW_R86'}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 3, channel: 2, motor_type: 'POWER_FLOW_R52'}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 5, channel: 2, motor_type: 'POWER_FLOW_R52'}" -1

# Step 2: 设置模式为 MIT (mode=6)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 2, channel: 1, mode: 6}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 3, channel: 1, mode: 6}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 3, channel: 2, mode: 6}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 5, channel: 2, mode: 6}" -1

# Step 3: MIT 控制 (持续发送)
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 2, channel: 1, q: 0.0, kp: 10.0, kd: 1.0}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 3, channel: 1, q: 0.0, kp: 10.0, kd: 1.0}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 3, channel: 2, q: 0.0, kp: 10.0, kd: 1.0}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 5, channel: 2, q: 0.0, kp: 10.0, kd: 1.0}" -1


rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 3, channel: 2, q: 0.0, dq: 5.0, tau: 0.0, kp: 0.0, kd: 1.0}" -1
# 禁能电机
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 2, motor_id: 2, channel: 1}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 2, motor_id: 3, channel: 1}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 2, motor_id: 3, channel: 2}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 2, motor_id: 5, channel: 2}" -1
```

### 电机通道映射

| 通道 | 电机类型 | motor_id | 名称 |
|------|---------|----------|------|
| CTRL1 (1) | R86-2 #1 | 3 | joint1 |
| CTRL1 (1) | R86-2 #2 | 2 | joint2 |
| CTRL2 (2) | R52 #1 | 3 | joint3 |
| CTRL2 (2) | R52 #2 | 5 | joint4 |

**MIT控制参数说明**:
- `q`: 目标位置 (rad)
- `dq`: 目标速度 (rad/s)
- `tau`: 目标力矩 (Nm)
- `kp`: 刚度 (位置环增益)
- `kd`: 阻尼 (速度环增益)

### Action 控制 (多电机)

```bash
rostopic pub /dcu_control/goal dcu_driver_pkg/DCUControlActionGoal \
  '{goal: {joint_names: ["joint1", "joint2"], positions: [1.0, 2.0], velocities: [0, 0], efforts: [0, 0], stiffness: [10, 10], damping: [1, 1]}}' --once
```

### 订阅话题

```bash
# 电机状态
rostopic echo /joint_states

# 查看所有话题
rostopic list | grep dcu
rostopic list | grep motor
```

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
    OMNI_PICKER,      // OmniPicker
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

### ActautorMode (SDK定义)

```cpp
enum ActautorMode : uint8_t {
    MODE_CURRENT = 0,
    MODE_CURRENT_RAMP = 1,
    MODE_VELOCITY = 2,
    MODE_VELOCITY_RAMP = 3,
    MODE_POSITION = 4,
    MODE_POSITION_RAMP = 5,
    MODE_MIT = 6,
};
```

## 代码结构

```
dcu_driver_pkg/
├── src/
│   ├── dcu_driver_server.cpp      # 主节点 (多圈累加/持续发送)
│   ├── dcu_driver_client.cpp       # 测试客户端
│   ├── dcu_control_node.cpp       # 简化版 Topic 节点
│   ├── ethercat_scan.cpp          # EtherCAT 总线扫描
│   └── dcu_can_test.cpp           # CAN 通信测试
├── msg/
│   └── MotorCommand.msg           # 电机控制消息 (cmd/motor_id/q/dq/tau/kp/kd)
├── action/
│   └── DCUControl.action          # Action 定义 (多电机控制)
├── launch/
│   ├── dcu_driver_server.launch   # 服务端启动
│   └── dcu_driver_client.launch   # 客户端启动
├── cfg/
│   └── dcu_cfg.yaml               # 配置文件
├── agibot_x1_infer/               # 嵌入式 RL 控制模块
│   └── src/module/dcu_driver_module/
│       └── xyber_controller/      # XyberController SDK
└── CMakeLists.txt
```

### 功能特性

#### 多圈位置累加

驱动层实现了多圈位置累加功能，通过检测过零点自动计数圈数：

```
[joint3] pos=25.132 rad (raw=3.142), vel=0.003 rad/s, state=1, mode=6, revolutions=4
```

- `pos`: 累加后的多圈位置 (25.132 rad = 4圈 × 2π + 3.142 rad)
- `raw`: 电机原始单圈位置 (±6.283 rad)
- `revolutions`: 已转过的圈数

**注意**: 给定目标位置 `q` 仍受电机固件限制 (±6.283 rad)，累加功能仅影响状态输出。

## 运行

### 1. 编译

```bash
cd ~/Desktop/Jetson_Nano/action_ws
source /opt/ros/noetic/setup.bash
catkin_make --pkg dcu_driver_pkg
```

### 2. 配置电机参数

在 launch 文件或 ROS param 中配置电机列表：

```yaml
motors:
  - name: "joint1"
    ethercat_id: 1
    can_node_id: 1
    can_channel: "CTRL1"
    actuator_type: "POWER_FLOW_R86"
  - name: "joint2"
    ethercat_id: 1
    can_node_id: 2
    can_channel: "CTRL1"
    actuator_type: "POWER_FLOW_R86"
```

### 3. 启动服务端

**推荐配置** (关闭 DC 时钟提高稳定性):

```bash
source devel/setup.bash
roslaunch dcu_driver_pkg dcu_driver_server.launch ethercat_if:=eth0 enable_dc:=false
```

**高速模式** (启用 DC 时钟，周期 1ms):

```bash
roslaunch dcu_driver_pkg dcu_driver_server.launch ethercat_if:=eth0 enable_dc:=true cycle_ns:=1000000
```

### 4. 配置电机参数

在 launch 文件或 ROS param 中配置电机列表：

```yaml
motors:
  - name: "joint1"
    ethercat_id: 1
    can_node_id: 3
    can_channel: "CTRL1"
    actuator_type: "POWER_FLOW_R86"
    torque_limit: 100.0
    velocity_limit: 37.7
  - name: "joint2"
    ethercat_id: 1
    can_node_id: 2
    can_channel: "CTRL1"
    actuator_type: "POWER_FLOW_R86"
    torque_limit: 100.0
    velocity_limit: 37.7
  - name: "joint3"
    ethercat_id: 1
    can_node_id: 3
    can_channel: "CTRL2"
    actuator_type: "POWER_FLOW_R52"
    torque_limit: 50.0
    velocity_limit: 25.1
  - name: "joint4"
    ethercat_id: 1
    can_node_id: 5
    can_channel: "CTRL2"
    actuator_type: "POWER_FLOW_R52"
    torque_limit: 50.0
    velocity_limit: 25.1
```

### 5. 验证

```bash
# 查看话题
rostopic list | grep -E "(motor|joint|dcu)"

# 监控状态
rostopic echo /joint_states

# 完整控制流程示例
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 2, channel: 1}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 2, channel: 1, mode: 6}" -1
rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 2, channel: 1, q: 0.0, kp: 10.0, kd: 1.0}" -r 10
```

## CANFD 报文格式

### 使能/失能帧

| 字段 | 值 |
|------|-----|
| MSG ID | motor_id (1-8) |
| DLC | 2 |
| D0 | 0x01 (Cmd) |
| D1 | 0x00 (失能) / 0x01 (使能) |

### MIT 模式广播帧

| 字段 | 值 |
|------|-----|
| MSG ID | 0 (广播) |
| DLC | 64 字节 |

每个电机根据 ID 取对应的 8 字节：

| 字节 | 内容 |
|------|------|
| D0-D1 | Position [15:8][7:0] |
| D2-D3 | Velocity [11:4][3:0] + Kp [11:8] |
| D4-D5 | Kp [7:0] + Kd [11:8] |
| D6-D7 | Kd [3:0] + Torque [11:8] |
| D8-D15 | 电机 ID=2 的数据... |

### 上行状态帧

| 字段 | 值 |
|------|-----|
| MSG ID | motor_id |
| DLC | 8 字节 |
| D0-D1 | Position |
| D2-D3 | Velocity + Current |
| D4-D5 | Error Code + State + Heartbeat |

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

### 5. 分布式时钟 (DC) 导致 EtherCAT 通信不稳定

**现象**:
```
[WARN] wkc < expected_wkc , wkc: -1, expected_wkc: 3
```

**原因**: Jetson Nano 与 DCU 之间的 DC 时钟同步不稳定，导致 EtherCAT 通信周期性中断。

**解决**: 关闭 DC 时钟同步

```bash
roslaunch dcu_driver_pkg dcu_driver_server.launch ethercat_if:=eth0 enable_dc:=false
```

**推荐配置**:
```bash
# 关闭 DC 时钟 + 降低循环频率 (2ms)
roslaunch dcu_driver_pkg dcu_driver_server.launch cycle_ns:=2000000 enable_dc:=false
```

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

### 问题 4: EtherCAT DC 时钟同步导致通信不稳定

**现象**:
```
[WARN] wkc < expected_wkc , wkc: -1, expected_wkc: 3
[ERROR] Failed to disable motor_id: 3
```

**原因**: Jetson Nano 与 DCU 之间的分布式时钟 (DC) 同步不稳定，导致 EtherCAT 周期性中断。

**解决**: 关闭 DC 时钟同步

```bash
roslaunch dcu_driver_pkg dcu_driver_server.launch ethercat_if:=eth0 enable_dc:=false
```

**推荐配置**:
```bash
# 关闭 DC 时钟 + 降低循环频率 (2ms)
roslaunch dcu_driver_pkg dcu_driver_server.launch cycle_ns:=2000000 enable_dc:=false
```

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

### 编译

```bash
# 编译整个工作空间
cd ~/Desktop/Jetson_Nano/action_ws
source /opt/ros/noetic/setup.bash
catkin_make

# 只编译本包
catkin_make --pkg dcu_driver_pkg
```

### 清理进程

```bash
pkill -9 -f dcu_driver
pkill -9 -f xyber
```

### 清理 ROS 日志

```bash
rm -rf ~/.ros/log/*
```

## 参考

- [智元 PowerFlow R 系列执行器产品手册](https://www.agibot.com.cn/DOCS/PM/PFR)
- XyberController SDK (agibot_x1_infer/)
- SOEM (Simple Open EtherCAT Master)
- ROS Action 通信机制
- CANFD 协议



## 实时测试

jetson@nano:~/Desktop/Jetson_Nano/action_ws$ sudo nvpmodel -m 0 # 切换到最大性能模式 (MAXN)
clocks # 锁定CPU、GPU频率到最高[sudo] password for jetson: 
Sorry, try again.
[sudo] password for jetson: 
jetson@nano:~/Desktop/Jetson_Nano/action_ws$ sudo jetson_clocks
jetson@nano:~/Desktop/Jetson_Nano/action_ws$ sudo cyclictest -t1 -p 99 -i 1000 -l 100000 -m -q
WARN: cyclictest was not built with the numa option
# /dev/cpu_dma_latency set to 0us
T: 0 (33915) P:99 I:1000 C: 100000 Min:      5 Act:    7 Avg:    7 Max:      98
jetson@nano:~/Desktop/Jetson_Nano/action_ws$ 