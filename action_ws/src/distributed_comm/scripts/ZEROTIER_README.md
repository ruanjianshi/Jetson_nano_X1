# ZeroTier 内网穿透分布式通信

## 原理

```
                         ZeroTier 虚拟网络
Internet           10.9.225.0/24
┌──────────────────────────────────────────────┐
│                                              │
│  ┌──────────────┐       ┌──────────────┐     │
│  │ Jetson Nano  │ ←───→ │   PC Laptop  │     │
│  │ 10.9.225.7   │  P2P  │ 10.9.225.55  │     │
│  │  roscore     │       │  rosrun ...  │     │
│  └──────────────┘       └──────────────┘     │
│         ↕                      ↕             │
└─────────┼──────────────────────┼─────────────┘
          │       Internet       │
     ┌────┴────┐            ┌────┴────┐
     │  WiFi/  │            │  WiFi/  │
     │  4G/5G  │            │ 有线/4G │
     └─────────┘            └─────────┘
```

ZeroTier 为所有设备分配虚拟 IP，组成二层虚拟网络。ROS 节点使用虚拟 IP 通信，物理网络对 ROS 完全透明。

## 快速配置

### 1. 两台机器都安装 ZeroTier

```bash
cd action_ws
bash src/distributed_comm/scripts/zerotier_setup.sh install
```

### 2. 加入同一个网络

```bash
bash src/distributed_comm/scripts/zerotier_setup.sh join
```

### 3. 网页后台授权

打开 https://my.zerotier.com/network/f3797ba7a828a818

- 找到两台设备 → 勾选 **Auth** 复选框
- 记下各自的虚拟 IP（如 `10.9.225.7` / `10.9.225.55`）

### 4. 配置 ROS 环境变量

```bash
# Jetson 先执行
bash src/distributed_comm/scripts/zerotier_setup.sh config

# PC 后执行
bash src/distributed_comm/scripts/zerotier_setup.sh config
```

脚本会自动检测机器类型，写入 `~/.bashrc`：

```bash
# Jetson 侧
export ROS_MASTER_URI=http://10.9.225.7:11311
export ROS_IP=10.9.225.7
export ROS_HOSTNAME=10.9.225.7

# PC 侧
export ROS_MASTER_URI=http://10.9.225.7:11311
export ROS_IP=10.9.225.55
export ROS_HOSTNAME=10.9.225.55
```

### 5. 启动测试

```bash
# Jetson
source ~/.bashrc
roscore &
rosrun distributed_comm jetson_bridge _pub_rate:=50

# PC
source ~/.bashrc
rosrun distributed_comm pc_bridge _pub_rate:=50
```

### 6. 验证

```bash
# 查看 ZeroTier 状态
bash src/distributed_comm/scripts/zerotier_setup.sh status

# 连通性测试
bash src/distributed_comm/scripts/zerotier_setup.sh test

# PC 端验证能否看到 Jetson 的 topic
rostopic list
```

## 脚本命令一览

| 命令 | 说明 |
|------|------|
| `install` | 安装 ZeroTier |
| `join` | 加入网络 `f3797ba7a828a818` |
| `status` | 查看连接状态和 IP |
| `config` | 配置 ROS 环境变量 |
| `test` | Ping Jetson 测试连通性 |

## 当前网络信息

| 项目 | 值 |
|------|-----|
| Network ID | `f3797ba7a828a818` |
| 管理后台 | https://my.zerotier.com/network/f3797ba7a828a818 |
| Jetson IP | `10.9.225.7` |
| PC IP | `10.9.225.55` |
| ROS Master | `http://10.9.225.7:11311` |

## 常见问题

| 现象 | 解决方法 |
|------|----------|
| `zerotier-cli` 不存在 | 执行 `install` 命令 |
| 虚拟 IP 为 0 或空 | 网页后台未授权 Auth，去 my.zerotier.com 勾选 |
| `rostopic list` 为空 | 检查 `ROS_MASTER_URI` 是否指向 Jetson 虚拟 IP |
| 延迟高 | 物理距离决定，ZeroTier 走最短路径 |
| 切回局域网 | `source ~/.bashrc` 会覆盖，手动 export 局域网 IP 即可 |
| 防火墙拦截 | `sudo ufw disable` |

## 性能参考

| 场景 | 延迟 | 带宽 |
|------|------|------|
| 同城 WiFi | +2~5ms | ~300 kbps |
| 跨省 4G | +30~80ms | ~150 kbps |
| 跨国 | +150~500ms | ~50 kbps |
| 局域网直连 | 0ms (不经过 ZT) | 同上 |

> ZeroTier 在同局域网内会自动走直连，不经过服务器转发。
