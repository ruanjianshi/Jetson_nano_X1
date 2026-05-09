# PC Control — 分布式控制框架

通过 QT5 UI 从 PC 远程控制 Jetson Nano，实时接收遥测反馈。

## 架构

```
PC (Ubuntu 20.04)                       Jetson Nano B01
┌─────────────────────────┐            ┌──────────────────────────┐
│  PC Control UI (QT5)    │            │  roscore                 │
│                         │  command   │                          │
│  /pc/command ──────────→│───────────→│ /pc/command → controller │
│                         │            │                          │
│  /jetson/telemetry ←────│←───────────│ /jetson/telemetry        │
│                         │ telemetry  │                          │
│  [LED] [Motor] [Servo]  │            │  [LED sim] [Motor sim]   │
│  [CPU: 45°C] [Mem: 1G]  │            │  [CPU temp] [Uptime]     │
└─────────────────────────┘            └──────────────────────────┘
```

## 命令协议 (JSON via /pc/command)

| 命令 | JSON | 说明 |
|------|------|------|
| LED ON | `{"cmd":"led_on"}` | 打开 LED |
| LED OFF | `{"cmd":"led_off"}` | 关闭 LED |
| Motor | `{"cmd":"motor","speed":80}` | 设置电机转速 0-100 |
| Servo | `{"cmd":"servo","angle":45}` | 设置舵机角度 0-180 |
| Status | `{"cmd":"status"}` | 请求遥测数据 |

## 遥测协议 (JSON via /jetson/telemetry)

```json
{
  "cpu_temp": 45.2, "cpu_percent": 25, "uptime": 3600,
  "mem_used": 1.2, "mem_total": 3.8,
  "led": 1, "motor": 80, "servo": 90
}
```

## 编译

### 前置依赖

```bash
sudo apt install qt5-default libjsoncpp-dev
```

### Jetson 端（build controller node）

```bash
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make -DCATKIN_WHITELIST_PACKAGES="distributed_comm"
source devel/setup.bash
```

### PC 端（build QT UI）

```bash
cd ~/Desktop/Jetson_Nano/action_ws/src/distributed_comm/pc_control
mkdir build && cd build
cmake ..
make -j$(nproc)

# 或者整个 workspace build 包含 controller
cd ~/Desktop/Jetson_Nano/action_ws
catkin_make -DCATKIN_WHITELIST_PACKAGES="distributed_comm"
source devel/setup.bash
```

## 运行

### 1. Jetson 端启动

```bash
roscore &
# 新终端
rosrun distributed_comm jetson_controller _telemetry_rate:=2
# 或
roslaunch distributed_comm jetson_control.launch
```

### 2. PC 端启动 QT UI

```bash
export ROS_MASTER_URI=http://<Jetson_IP>:11311
export ROS_IP=<PC_IP>

# 如果已经 catkin_make 并构建了 QT binary
rosrun distributed_comm pc_control_ui

# 或者直接运行
cd ~/nano_distribute/devel/lib/distributed_comm
./pc_control_ui
```

### 3. 测试（从任何机器发送命令）

```bash
rosrun distributed_comm test_commands.py
```

## 扩展

框架支持扩展更多硬件：

1. **jetson_controller.cpp** — 添加 GPIO/I2C/SPI 实际硬件驱动
2. **main_window.cpp** — 添加更多 UI 控件（传感器图表、摄像头预览等）
3. 可替换 `std_msgs/String` 为自定义 ROS message 类型

## 作者

**作者**: Qi Xiao
**邮箱**: 2408128687@qq.com
