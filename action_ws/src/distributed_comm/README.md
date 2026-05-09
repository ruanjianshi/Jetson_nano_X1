# distributed_comm

**PC (Ubuntu 20.04)** 与 **Jetson Nano B01** 之间的 ROS1 分布式通信桥接包。

## 架构

```
Jetson Nano B01                       PC (Ubuntu 20.04)
┌─────────────────────┐              ┌─────────────────────┐
│  roscore            │              │                     │
│                     │              │                     │
│  jetson_bridge      │              │  pc_bridge          │
│    pub: /jetson/pub  │──────────→  │    sub: /jetson/pub │
│    sub: /pc/pub_data │←──────────  │    pub: /pc/pub     │
│                     │              │                     │
└─────────────────────┘              └─────────────────────┘
```

## 快速开始

### 第1步：代码同步（PC 需要拿到 distributed_comm 包）

```bash
# 方式A：SCP 脚本自动同步（推荐）
bash src/distributed_comm/scripts/scp_transfer.sh config    # 首次配置双方 IP
bash src/distributed_comm/scripts/scp_transfer.sh sync-distributed

# 方式B：手动拷贝
scp -r src/distributed_comm <PC_USER>@<PC_IP>:~/nano_distribute/src/
```

> PC 端需提前安装 SSH 服务：`sudo apt install openssh-server -y && sudo systemctl enable ssh --now`

### 第2步：网络配置（两台机器都要执行）

```bash
# Jetson 和 PC 上分别运行
cd action_ws
bash src/distributed_comm/scripts/network_setup.sh

# Jetson 上选 [j]，PC 上选 [p] 并输入 Jetson 的 IP
```

或手动配置：

```bash
# Jetson
export ROS_IP=<Jetson_IP>
roscore &

# PC
export ROS_MASTER_URI=http://<Jetson_IP>:11311
export ROS_IP=<PC_IP>
```

> **注意：** PC 无法连接时，关闭 Jetson 防火墙：
> ```bash
> sudo ufw disable
> ```

### 第3步：编译

```bash
# Jetson 和 PC 都要做
cd action_ws               # PC 上 cd ~/nano_distribute
catkin_make -DCATKIN_WHITELIST_PACKAGES="distributed_comm"
source devel/setup.bash
```

### 第4步：启动双向桥接

```bash
# Jetson 端
rosrun distributed_comm jetson_bridge _pub_rate:=50

# PC 端
rosrun distributed_comm pc_bridge _pub_rate:=50
```

Jetson 端输出：
```
[Jetson Bridge] started (pub=/jetson/pub_data sub=/pc/pub_data) rate=50 Hz
 Send: 50.0 msg/s | Recv: 50.0 msg/s (111.2 kbps)
```

PC 端输出（含延迟）：
```
[PC Bridge] started (pub=/pc/pub_data sub=/jetson/pub_data) rate=50 Hz
 Send: 50.0 msg/s | Recv: 50.0 msg/s (111.2 kbps) | Latency: 76.0 ms
```

### 第5步：WiFi 吞吐量极限测试

```bash
# Jetson 端：固定高频 200 Hz
rosrun distributed_comm jetson_bridge _pub_rate:=200

# PC 端：自动递进测试，找到最大稳定速率
rosrun distributed_comm rate_tester _start_hz:=50 _step_hz:=50 _interval_s:=5
```

输出示例（ZeroTier 内网穿透）：
```
============================================
  WiFi Throughput Rate Test
  start=50 Hz  step=50  interval=5s
============================================
[ 50 Hz] recv=50  ratio=100%  lat=55.0 ms
[100 Hz] recv=100  ratio=100%  lat=56.1 ms
[200 Hz] recv=200  ratio=100%  lat=56.4 ms
[300 Hz] recv=300  ratio=100%  lat=55.7 ms
[400 Hz] recv=400  ratio=100%  lat=55.8 ms
[450 Hz] recv=400  ratio= 89%  lat=55.6 ms
============================================
  MAX STABLE THROUGHPUT
  Rate:    450 Hz  |  450 msgs/s
  Bandwidth: 922 kbps  |  0.92 Mbps
============================================
```

| 网络 | 最大吞吐量 | 延迟 | 带宽 |
|------|-----------|------|------|
| LAN 局域网 | ~250 Hz | ~76ms | ~410 kbps |
| ZeroTier 内网穿透 | ~450 Hz | ~55ms | ~922 kbps |

## Launch 文件

```bash
# Jetson
roslaunch distributed_comm jetson_server.launch pub_rate:=50

# PC
roslaunch distributed_comm pc_client.launch pub_rate:=50
```

## 文件结构

```
distributed_comm/
├── CMakeLists.txt
├── package.xml
├── README.md
├── launch/
│   ├── jetson_server.launch    # Jetson 端启动文件
│   └── pc_client.launch        # PC 端启动文件
├── scripts/
│   ├── network_setup.sh        # ROS_IP / ROS_MASTER_URI 自动配置脚本
│   └── scp_transfer.sh         # PC <-> Jetson SCP 文件传输脚本
├── src/
│   ├── jetson_bridge.cpp        # Jetson 端：发布 + 订阅双向通信节点
│   ├── pc_bridge.cpp            # PC 端：发布 + 订阅 + 延迟测量节点
│   └── rate_tester.cpp          # PC 端：自动递进吞吐量极限测试节点
├── test/                        # 分布式 YOLO 推理测试
│   ├── README.md
│   ├── camera_bridge.launch
│   ├── pc_yolo.launch
│   └── scripts/
│       ├── camera_publisher.py
│       ├── distributed_yolo_server.py
│       └── jetson_display.py
└── model/                       # YOLO 模型文件
```

## 工具脚本

### network_setup.sh — 网络配置

```bash
bash scripts/network_setup.sh
```

交互式配置 `ROS_MASTER_URI` / `ROS_IP` / `ROS_HOSTNAME`，自动写入 `~/.bashrc`。根据 hostname 自动识别运行在 Jetson 还是 PC 上。

### scp_transfer.sh — 文件传输

```bash
bash scripts/scp_transfer.sh config              # 首次：配置双方 IP
bash scripts/scp_transfer.sh sync-distributed    # 同步 distributed_comm 包
bash scripts/scp_transfer.sh push <文件> <远程路径>   # 推送到对面
bash scripts/scp_transfer.sh pull <远程文件> <本地路径> # 从对面拉取
```

根据 hostname 自动识别当前机器：
- 在 **PC** 上执行 → 自动推送到 Jetson
- 在 **Jetson** 上执行 → 自动推送到 PC

> PC 端需安装 SSH server：`sudo apt install openssh-server -y`

## 节点与参数

### jetson_bridge（Jetson 端）

| 参数 | 类型 | 默认值 | 说明 |
|-------|------|---------|-------------|
| `_pub_rate` | double | 50 | 每秒发布消息数 |
| `_msg_size` | int | 256 | 每条消息负载字节数 |

Topic：
- **发布：** `/jetson/pub_data` (std_msgs/String)  格式 `"序号,时间戳,负载..."`
- **订阅：** `/pc/pub_data` (std_msgs/String)

### pc_bridge（PC 端）

| 参数 | 类型 | 默认值 | 说明 |
|-------|------|---------|-------------|
| `_pub_rate` | double | 50 | 每秒发布消息数 |
| `_msg_size` | int | 256 | 每条消息负载字节数 |

Topic：
- **发布：** `/pc/pub_data` (std_msgs/String)  格式 `"序号,时间戳,负载..."`
- **订阅：** `/jetson/pub_data` (std_msgs/String)

### rate_tester（PC 端吞吐量测试）

| 参数 | 类型 | 默认值 | 说明 |
|-------|------|---------|-------------|
| `_start_hz` | double | 10 | 起始发布频率 (Hz) |
| `_step_hz` | double | 20 | 每次递增步长 (Hz) |
| `_interval_s` | double | 5 | 每档持续时长 (秒) |
| `_unstable_ratio` | double | 0.85 | 接收/期望比值低于此值判定不稳定 |
| `_msg_size` | int | 256 | 每条消息负载字节数 |

## 原理

ROS1 分布式通信的核心是两个环境变量：

- `ROS_MASTER_URI`：指定 ROS Master 地址（所有节点注册到同一个 Master）
- `ROS_IP` / `ROS_HOSTNAME`：本机 IP，供其他节点建立 TCP 连接

Jetson Nano 运行 `roscore`，PC 设置 `ROS_MASTER_URI` 指向 Jetson。两端节点自动通过同一个 Master 发现彼此，Topic 数据通过 TCPROS 协议直接点对点传输。

## 常见问题

| 现象 | 解决方法 |
|---------|----------|
| `[rospack] Error: package not found` | 先执行 `source devel/setup.bash` |
| PC 无法连接 Jetson | Jetson 上执行 `sudo ufw disable` |
| 两端 Recv 都为 0 | 检查 PC 的 `ROS_MASTER_URI` 和 `ROS_IP` 是否正确 |
| 延迟高 / 吞吐量低 | 靠近路由器，减少 WiFi 干扰 |
| PC 编译失败 | PC 只需拷贝 `distributed_comm` 目录，无 Jetson 特有依赖 |
| SCP 传输 Connection refused | PC 端 `sudo apt install openssh-server -y` |
  | SCP 路径不存在 | 先执行 `./scp_transfer.sh config` 配置 IP 和用户名 |

## 分布式 YOLO 推理测试

PC 远程推理 Jetson 摄像头图像，详见 [test/README.md](test/README.md)。

```
Jetson: 摄像头采集 ──→ PC: YOLO 推理 ──→ Jetson: 显示结果
   publisher             server               display
```

```bash
# Jetson
roslaunch distributed_comm camera_bridge.launch

# PC (需安装 ultralytics + 下载模型)
roslaunch distributed_comm pc_yolo.launch device:=cuda:0
```


## 作者

**作者**: Qi Xiao  
**邮箱**: 2408128687@qq.com
