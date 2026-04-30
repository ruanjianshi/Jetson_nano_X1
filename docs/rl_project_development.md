# RL Project 开发流程文档

## 项目概述

**项目名称**: rl_project - Grid World 强化学习
**目标**: 在格子世界环境中实现 6 种强化学习算法
**平台**: Jetson Nano (aarch64) / Linux
**框架**: PyTorch

---

## 项目结构

```
/home/jetson/Desktop/Jetson_Nano/rl_project/
├── Agents/                 # 智能体模块
│   ├── DQNAgent.py        # DQN 智能体 (深度Q网络)
│   ├── PPOAgent.py        # PPO 智能体 (近端策略优化)
│   ├── A2CAgent.py        # A2C 智能体 (同步Actor-Critic)
│   ├── DDPGAgent.py       # DDPG 智能体 (深度确定性策略梯度)
│   ├── SACAgent.py        # SAC 智能体 (软Actor-Critic)
│   └── TD3Agent.py        # TD3 智能体 (双延迟DDPG)
├── Environment/            # 环境模块
│   ├── Action.py          # 9个离散动作
│   ├── GameEnv.py         # 格子世界环境
│   └── State.py           # 33x33窗口状态
├── Utils/                  # 工具模块
│   └── types.py           # 类型定义、常量
├── train-eval/             # 训练与评估
│   ├── train.py           # 训练脚本
│   └── eval.py            # 评估脚本
└── model/                   # 模型保存目录
```

---

## 开发进展

### Phase 1: 项目初始化 ✅

**时间**: 2024-04-27

**完成内容**:
- 创建 Python 项目结构
- 定义核心类型 (`Utils/types.py`):
  - `Position`: 二维坐标
  - `EnvConfig`: 环境配置
  - `Transition`: 经验元组
  - `DQNConfig`: DQN配置
  - 通道常量 (Agent/Goal/Obstacle_N/E/S/W)
  - 奖励常量

**存在的问题**:
- 初始 State.py 只编码了 Agent 位置，没有编码食物和障碍物
- Agent 是"盲"的，无法学习

---

### Phase 2: 状态编码修复 ✅

**时间**: 2024-04-28

**问题**: 原 State.py 只编码 Agent 位置，Agent 无法感知环境

**修复内容** (`Environment/State.py`):
- 实现 6 通道状态编码:
  - Channel 0: Agent 位置 (1.0)
  - Channel 1: Goal/Food 位置 (1.0)
  - Channel 2: Obs_N (北向障碍物)
  - Channel 3: Obs_E (东向障碍物)
  - Channel 4: Obs_S (南向障碍物)
  - Channel 5: Obs_W (西向障碍物)
- 窗口大小: 33x33 (以 Agent 为中心)
- 边界外填充 0.5 (表示未知)
- 总状态维度: 6 × 33 × 33 = 6534

**验证**: Agent 现在可以看到食物和障碍物

---

### Phase 3: DQN 实现 ✅

**时间**: 2024-04-28

**完成内容** (`Agents/DQNAgent.py`):

1. **QNetwork 神经网络**
   - 结构: `[6534] → [256] → [128] → [64] → [9]`
   - ReLU 激活函数
   - 输出 9 个动作的 Q 值

2. **双网络结构**
   - 主网络: 用于选择动作
   - 目标网络: 用于计算目标 Q 值
   - 定期同步 (target_update_freq_v)

3. **Experience Replay**
   - 经验池容量: 50000
   - 批大小: 64
   - 随机采样

4. **Epsilon-Greedy 探索**
   - 初始: 0.1
   - 最终: 0.01
   - 衰减步数: 2000

---

### Phase 4: PPO 实现 ✅

**时间**: 2024-04-28

**完成内容** (`Agents/PPOAgent.py`):

1. **Actor-Critic 架构**
   - PolicyNetwork (Actor): 输出动作概率分布
   - ValueNetwork (Critic): 输出状态价值 V(s)

2. **PPO 核心算法**
   - Clipped Surrogate Objective (clip_epsilon=0.2→0.1)
   - GAE 优势估计 (lambda=0.95)
   - 多次 epoch 更新 (k_epochs=4→10)
   - 熵正则化 (entropy_coef=0.01→0.05)

3. **PPOMemory**
   - 存储单 episode 的轨迹
   - 包含 states, actions, rewards, dones, probs

**优化**: 修复 compute_gae 中 `advantages.insert(0, gae)` 的 O(n²) 问题，改为 append + reverse

---

### Phase 5: 训练脚本 ✅

**时间**: 2024-04-28

**完成内容** (`train-eval/train.py`):

- 支持 `--agent dqn/ppo` 选择智能体类型
- 支持 `-e/--episodes` 指定训练回合数
- 每 10 回合输出平均奖励
- 每 50 回合渲染环境
- 自动保存模型到 `train-eval/{agent}_model_{episodes}ep.pt`

**默认配置**:
```python
EnvConfig(height=32, width=32, obstacle_prob=0.03, obstacle_freq=999, food_count=15)
```

---

### Phase 6: 评估脚本 ✅

**时间**: 2024-04-28

**完成内容** (`train-eval/eval.py`):

- 支持 `--agent dqn/ppo` 选择智能体类型
- 支持 `-e/--episodes` 指定评估回合数
- 自动加载最新的模型文件
- 输出详细统计: Reward, Steps, Food/Ep
- DQN 使用纯 exploitation (epsilon=0)
- PPO 使用随机策略

---

### Phase 7: 问题诊断与优化尝试 ⚠️

**时间**: 2024-04-30

**问题现象**:
- 训练 100 回合后，Agent 仍然吃不到食物 (Food/Ep = 0)
- Agent 能存活一段时间，但不会主动寻找食物
- Avg Steps = 35.3, Avg Reward = 1.624 (来自存活，非食物)

**根本原因分析**:
1. **奖励结构不合理**
   - 吃食物: +1.5
   - 靠近食物: +0.05~0.1
   - 差异不够大，Agent 没有足够动力去吃食物

2. **障碍物密度太高**
   - 32x32 网格，3% 障碍物概率 ≈ 30 个障碍物
   - Agent 容易死亡，没有机会学习

3. **边界陷阱**
   - 边界是障碍物出生点
   - Agent 贴边移动容易死亡

**优化尝试**:

1. **PPO 超参数调优** (已实施)
   - clip_epsilon: 0.2 → 0.1 (更保守的策略更新)
   - k_epochs: 4 → 10 (更多数据利用)
   - entropy_coef: 0.01 → 0.05 (更多探索)
   - 缺点: 训练时间变长

2. **奖励工程** (建议实施)
   - K_REWARD_FOOD: 1 → 10 (显著提高食物奖励)
   - K_REWARD_OBSTACLE: -1 → -0.1 (降低死亡惩罚)
   - K_REWARD_OUT_OF_BOUNDS: -2 → -0.1

3. **环境简化** (建议实施)
   - obstacle_prob: 0.03 → 0.01
   - food_count: 15 → 10
   - obstacle_freq: 999 → 50 (定期刷新障碍物)

---

### Phase 8: 新增 A2C, DDPG, SAC, TD3 算法 ✅

**时间**: 2024-04-30

**完成内容**:

#### A2C (Advantage Actor-Critic) - `Agents/A2CAgent.py`

- **类型**: Policy Gradient / On-Policy
- **架构**: Actor-Critic (N-step returns)
- **特点**:
  - 比 PPO 更简单
  - 使用 N-step returns 而非 GAE
  - 单次策略更新
  - 内存效率高

**神经网络结构**:
```
PolicyNetwork: [6534] → [256] → [128] → [64] → [9] + Softmax
ValueNetwork: [6534] → [256] → [128] → [64] → [1]
```

#### DDPG (Deep Deterministic Policy Gradient) - `Agents/DDPGAgent.py`

- **类型**: Actor-Critic / Off-Policy
- **架构**: 确定性策略 + 双网络
- **特点**:
  - 输出确定性动作
  - 使用 Ornstein-Uhlenbeck 噪声探索
  - Soft target update (τ=0.001)
  - 适合连续动作空间

**改进**: 适配离散动作空间 (输出Q值，选择最大Q的动作)

#### SAC (Soft Actor-Critic) - `Agents/SACAgent.py`

- **类型**: Actor-Critic / Off-Policy / 最大熵
- **架构**: 随机策略 + Twin Q + 自动温度
- **特点**:
  - 最大化熵加权回报
  - 自动调节探索 (熵作为奖励)
  - Twin Q-Networks 减少过估计
  - Off-policy 样本效率高

**核心公式**:
```
π* = argmax E[Σ r(s,a)] + α * H(π)
```

#### TD3 (Twin Delayed DDPG) - `Agents/TD3Agent.py`

- **类型**: Actor-Critic / Off-Policy
- **架构**: DDPG 改进版 + 三重技巧
- **特点**:
  - Twin Q-Networks (减少过估计)
  - Delayed Policy Updates (每隔2步更新策略)
  - Target Policy Smoothing (目标动作添加噪声)

**DDPG vs TD3**:
| 特性 | DDPG | TD3 |
|------|------|-----|
| Q网络 | 1个 | 2个(Twin) |
| 策略延迟更新 | 无 | 有 |
| 目标策略平滑 | 无 | 有 |
| Q值过估计 | 严重 | 较轻 |

---

### Phase 9: 更新训练/评估脚本 ✅

**时间**: 2024-04-30

**完成内容**:

1. **更新 `train-eval/train.py`**
   - 支持 6 种算法: `--agent dqn/ppo/a2c/ddpg/sac/td3`
   - 每种算法独立的训练函数

2. **更新 `train-eval/eval.py`**
   - 支持 6 种算法的评估
   - 交互式选择 (输入1-6)

3. **更新 `Agents/__init__.py`**
   - 导出所有 6 种智能体

---

## 算法原理对比

### Value-Based vs Policy Gradient

| 特性 | Value-Based (DQN) | Policy Gradient (PPO/A2C) |
|------|------------------|---------------------------|
| 策略 | 间接 (通过Q值) | 直接 (输出动作概率) |
| 动作 | 离散 | 离散/连续 |
| 探索 | ε-greedy | 熵正则化 |
| 收敛 | 较快 | 较慢 |
| 样本效率 | 高 | 低 |

### On-Policy vs Off-Policy

| 特性 | On-Policy (PPO/A2C) | Off-Policy (DQN/SAC/TD3) |
|------|---------------------|---------------------------|
| 数据来源 | 当前策略 | 历史策略 |
| 样本复用 | 一次 | 多次 |
| 稳定性 | 较稳定 | 可能不稳定 |
| 样本效率 | 低 | 高 |

### Actor-Critic 架构

```
        ┌─────────────┐
        │   State     │
        └──────┬──────┘
               │
     ┌─────────┴─────────┐
     │                   │
     ▼                   ▼
┌─────────┐        ┌──────────┐
│  Actor  │        │  Critic  │
│ (策略)  │        │  (价值)  │
│ π(a|s) │        │  V(s)    │
└────┬────┘        └────┬─────┘
     │                   │
     ▼                   │
┌─────────┐             │
│ Action  │             │
└────┬────┘             │
     │                   │
     ▼                   │
  Environment ◄─────────┘
     │                   │
     ▼                   │
  Reward, NextState ─────┘
```

---

## 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| 环境实现 | ✅ 完成 | GameEnv 完整实现 |
| 状态编码 | ✅ 完成 | 6通道33x33窗口 |
| DQN Agent | ✅ 完成 | PyTorch实现 |
| PPO Agent | ✅ 完成 | PyTorch实现 |
| A2C Agent | ✅ 完成 | PyTorch实现 |
| DDPG Agent | ✅ 完成 | PyTorch实现 |
| SAC Agent | ✅ 完成 | PyTorch实现 |
| TD3 Agent | ✅ 完成 | PyTorch实现 |
| 训练脚本 | ✅ 完成 | 支持 6 种算法 |
| 评估脚本 | ✅ 完成 | 支持 6 种算法 |
| 文档 | ✅ 完成 | README.md |
| 开发流程 | ✅ 完成 | 本文档 |
| 学习效果 | ⚠️ 待改进 | Food/Ep = 0 |

---

## 技术细节

### 通道定义 (`Utils/types.py`)

```python
K_AGENT_CHANNEL = 0          # 智能体
K_GOAL_CHANNEL = 1           # 食物/目标
K_OBSTACLE_N_CHANNEL = 2     # 北向障碍物 (从北向南移动)
K_OBSTACLE_E_CHANNEL = 3     # 东向障碍物 (从东向西移动)
K_OBSTACLE_S_CHANNEL = 4     # 南向障碍物 (从南向北移动)
K_OBSTACLE_W_CHANNEL = 5     # 西向障碍物 (从西向东移动)
```

### 动作定义 (`Environment/Action.py`)

```
索引:  0   1   2   3   4   5   6   7   8
方向:  ↑   ↗   →   ↘   ↓   ↙   ←   ↖   □
行:   -1  -1   0   1   1   1   0  -1   0
列:    0   1   1   1   0  -1  -1  -1   0
```

### 神经网络结构 (所有算法共用基础架构)

**Policy/Actor Networks (PPO, A2C, SAC)**:
```
Input:  [6534]
  → Linear(6534, 256) + ReLU
  → Linear(256, 128) + ReLU
  → Linear(128, 64) + ReLU
  → Linear(64, 9) + Softmax   # 动作概率
```

**Value/Critic Networks**:
```
Input:  [6534]
  → Linear(6534, 256) + ReLU
  → Linear(256, 128) + ReLU
  → Linear(128, 64) + ReLU
  → Linear(64, 1)            # 状态价值
```

**Q-Network (DQN, DDPG, TD3)**:
```
Input:  [6534]
  → Linear(6534, 256) + ReLU
  → Linear(256, 128) + ReLU
  → Linear(128, 64) + ReLU
  → Linear(64, 9)            # 各动作Q值
```

---

## 问题记录

### Q: 为什么 Agent 吃不到食物?

**A**: 根本原因是奖励结构。吃食物 +1.5 vs 靠近食物 +0.05，差异不够大。Agent 发现存活就能获得奖励（通过 proximity reward 累积），而冒险去吃食物反而容易死亡。建议大幅提高食物奖励到 +10。

### Q: PPO 训练为什么比 DQN 慢?

**A**: 因为 PPO 使用 k_epochs=10 进行多次更新，每个 episode 的数据被重复学习多次。另外 GAE 计算也是 O(n) 复杂度。

### Q: A2C 和 PPO 有什么区别?

**A**: A2C 是 PPO 的简化版本，主要区别:
- A2C 单次更新，PPO 多次 epoch 更新
- A2C 使用 N-step returns，PPO 使用 GAE
- A2C 更简单，PPO 更稳定

### Q: DDPG 和 TD3 有什么区别?

**A**: TD3 是 DDPG 的改进版本:
- TD3 使用 Twin Q-networks，DDPG 使用单个 Q 网络
- TD3 延迟更新策略网络，DDPG 每步更新
- TD3 使用目标策略平滑，DDPG 不使用

### Q: SAC 的最大熵是什么意思?

**A**: SAC 最大化 `奖励 + α * 熵`，其中熵 H(π) = -Σ π(a|s) log π(a|s)。这鼓励策略保持随机，从而自动调节探索程度。

---

## 相关文件路径

| 文件 | 路径 |
|------|------|
| 项目根目录 | `/home/jetson/Desktop/Jetson_Nano/rl_project/` |
| 主文档 | `/home/jetson/Desktop/Jetson_Nano/rl_project/README.md` |
| 开发文档 | `/home/jetson/Desktop/Jetson_Nano/docs/rl_project_development.md` |
| 类型定义 | `/home/jetson/Desktop/Jetson_Nano/rl_project/Utils/types.py` |
| 环境 | `/home/jetson/Desktop/Jetson_Nano/rl_project/Environment/GameEnv.py` |
| 状态 | `/home/jetson/Desktop/Jetson_Nano/rl_project/Environment/State.py` |
| DQN Agent | `/home/jetson/Desktop/Jetson_Nano/rl_project/Agents/DQNAgent.py` |
| PPO Agent | `/home/jetson/Desktop/Jetson_Nano/rl_project/Agents/PPOAgent.py` |
| A2C Agent | `/home/jetson/Desktop/Jetson_Nano/rl_project/Agents/A2CAgent.py` |
| DDPG Agent | `/home/jetson/Desktop/Jetson_Nano/rl_project/Agents/DDPGAgent.py` |
| SAC Agent | `/home/jetson/Desktop/Jetson_Nano/rl_project/Agents/SACAgent.py` |
| TD3 Agent | `/home/jetson/Desktop/Jetson_Nano/rl_project/Agents/TD3Agent.py` |
| 训练脚本 | `/home/jetson/Desktop/Jetson_Nano/rl_project/train-eval/train.py` |
| 评估脚本 | `/home/jetson/Desktop/Jetson_Nano/rl_project/train-eval/eval.py` |

---

*最后更新: 2024-04-30*
