# PC 控制测试

不依赖 QT GUI，通过脚本测试 PC→Jetson 控制链路。

## 测试命令协议

`/pc/command` (std_msgs/String, JSON): `{"cmd":"led_on"}`, `{"cmd":"motor","speed":80}`, ...

`/jetson/telemetry` (std_msgs/String, JSON): `{"cpu_temp":45.2,"led":1,...}`

## 测试步骤

### 1. Jetson 端启动

```bash
roscore &
rosrun distributed_comm jetson_controller
```

### 2. 自动测试（推荐）

```bash
roslaunch distributed_comm control_test.launch mode:=auto
```

### 3. 交互式测试

```bash
rosrun distributed_comm test_commands.py _mode:=interactive
```

交互命令:
- `led_on` / `led_off` — 控制LED
- `motor 80` — 设置电机转速
- `servo 45` — 设置舵机角度
- `status` — 请求遥测
- `{"cmd":"motor","speed":30}` — 原始JSON
- `q` — 退出

### 4. 从任意机器测试

```bash
export ROS_MASTER_URI=http://<Jetson_IP>:11311
export ROS_IP=<LOCAL_IP>
rosrun distributed_comm test_commands.py
```

## 作者

**作者**: Qi Xiao
**邮箱**: 2408128687@qq.com
