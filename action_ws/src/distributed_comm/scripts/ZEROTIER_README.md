# ZeroTier 内网穿透分布式通信

## 原理

```
                         ZeroTier 虚拟网络
           10.9.225.0/24
┌──────────────────────────────────────────────┐
│  ┌──────────────┐       ┌──────────────┐     │
│  │ Jetson Nano  │ ←───→ │   PC Laptop  │     │
│  │ 10.9.225.7   │  P2P  │ 10.9.225.55  │     │
│  └──────────────┘       └──────────────┘     │
└──────────────────────────────────────────────┘
```

## 快速配置

### 1. 两台机器安装 ZeroTier

```bash
cd action_ws
bash src/distributed_comm/scripts/zerotier_setup.sh install
```

### 2. 加入网络

```bash
bash src/distributed_comm/scripts/zerotier_setup.sh join
```

### 3. 网页授权

打开 https://my.zerotier.com/network/f3797ba7a828a818 → 勾选两台设备的 **Auth**

### 4. 配置 IP（两台都要）

```bash
bash src/distributed_comm/scripts/zerotier_setup.sh config
```

按提示输入 LAN IP 和 ZT IP。PC 端还需输入 Jetson 的两种 IP。

### 5. 切换到 ZeroTier 模式

```bash
# 两台都执行（source 方式，当前终端自动刷新）
. ./zerotier_setup.sh switch zt
```

### 6. 启动测试

```bash
# Jetson
source ~/.bashrc
roscore &
rosrun distributed_comm jetson_bridge _pub_rate:=50

# PC
source ~/.bashrc
rosrun distributed_comm pc_bridge _pub_rate:=50
```

## 一键切换

```bash
# source 执行（推荐，当前终端自动刷新）
. ./zerotier_setup.sh switch lan
. ./zerotier_setup.sh switch zt

# 或直接执行（需手动 source ~/.bashrc）
./zerotier_setup.sh switch lan
source ~/.bashrc

# 查看当前模式
. ./zerotier_setup.sh status
```

每次 `switch` 会：
1. 删除 `~/.bashrc` 中旧的 ROS 网络配置行
2. 追加新模式到末尾
3. source 执行时自动刷新当前终端环境

## 脚本命令

| 命令 | 说明 |
|------|------|
| `install` | 安装 ZeroTier |
| `join` | 加入网络 |
| `config` | 配置 LAN/Z IP |
| `switch lan` | 切换到局域网 |
| `switch zt` | 切换到 ZeroTier |
| `status` | 显示当前模式和连接状态 |
| `test` | Ping 对面机器 |

## 网络信息

| 项目 | LAN | ZeroTier |
|------|-----|----------|
| Jetson IP | 10.88.168.44 | 10.9.225.7 |
| PC IP | 10.88.168.60 | 10.9.225.55 |
| ROS Master | http://10.88.168.44:11311 | http://10.9.225.7:11311 |

## 常见问题

| 现象 | 解决方法 |
|------|----------|
| `zerotier-cli` 不存在 | 执行 `install` |
| 虚拟 IP 为空 | 网页后台未授权 Auth |
| 切换后不生效 | 重新 `source ~/.bashrc` 或开新终端 |
| 防火墙拦截 | `sudo ufw disable` |
| 切换时 LAN IP 变了 | 重新 `config` 修改 |

## 性能参考 (实测)

| 场景 | 最大吞吐量 | 延迟 | 带宽 |
|------|-----------|------|------|
| 局域网直连 | ~250 Hz | ~76ms | ~410 kbps |
| **ZeroTier 内网穿透** | **~450 Hz** | **~55ms** | **~922 kbps** |
| ZeroTier 跨省 | ~100 Hz | ~100ms | ~200 kbps |

> ZeroTier 在同网段内自动走直连并优化路由，实测比直接局域网更稳定、吞吐量更高。
