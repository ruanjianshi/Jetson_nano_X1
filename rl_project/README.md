# RL Project - Grid World Reinforcement Learning

基于 PyTorch 的强化学习项目，实现 6 种强化学习算法在格子世界环境中的训练与评估。

## 项目结构

```
rl_project/
├── Agents/                 # 智能体模块
│   ├── __init__.py
│   ├── DQNAgent.py        # DQN 智能体 (深度Q网络)
│   ├── PPOAgent.py        # PPO 智能体 (近端策略优化)
│   ├── A2CAgent.py        # A2C 智能体 (同步Actor-Critic)
│   ├── DDPGAgent.py       # DDPG 智能体 (深度确定性策略梯度)
│   ├── SACAgent.py        # SAC 智能体 (软Actor-Critic)
│   └── TD3Agent.py        # TD3 智能体 (双延迟DDPG)
├── Environment/            # 环境模块
│   ├── __init__.py
│   ├── Action.py          # 动作定义 (9个离散动作)
│   ├── GameEnv.py         # 格子世界环境
│   └── State.py           # 状态表示 (6通道33x33窗口)
├── Utils/                  # 工具模块
│   ├── __init__.py
│   └── types.py           # 类型定义和常量
├── train-eval/             # 训练与评估脚本
│   ├── train.py           # 训练脚本
│   └── eval.py            # 评估脚本
├── model/                   # 模型保存目录
└── README.md              # 本文档
```

## 环境配置

```
Python >= 3.8
PyTorch >= 1.8 (支持CUDA)
NumPy
```

安装依赖:
```bash
pip3 install torch numpy
```

## 快速开始

### 训练

```bash
# DQN 训练 (默认100回合)
python3 train-eval/train.py --agent dqn

# PPO 训练
python3 train-eval/train.py --agent ppo -e 200

# A2C 训练
python3 train-eval/train.py --agent a2c -e 200

# DDPG 训练
python3 train-eval/train.py --agent ddpg -e 200

# SAC 训练
python3 train-eval/train.py --agent sac -e 200

# TD3 训练
python3 train-eval/train.py --agent td3 -e 200
```

### 评估

```bash
# 评估 DQN (自动加载最新模型)
python3 train-eval/eval.py --agent dqn -e 50

# 评估 PPO
python3 train-eval/eval.py --agent ppo -e 50
```

---

## 算法原理详解

### 1. DQN (Deep Q-Network)

**类型**: Value-Based / Off-Policy

**核心思想**: 通过神经网络逼近Q值函数 Q(s, a)，选择Q值最大的动作。

**Q值函数**: Q(s, a) 表示在状态s下执行动作a的预期累积奖励。

**更新公式**:
```
Q(s, a) ← Q(s, a) + α * (r + γ * max_a' Q(s', a') - Q(s, a))
```

**关键组件**:
- **双网络结构**: 主网络 + 目标网络，减少训练振荡
- **Experience Replay**: 存储(s, a, r, s', terminal)经验，随机采样打破相关性
- **Epsilon-Greedy**: ε概率随机选择，1-ε概率选择最大Q值

**优点**: 样本效率高，可以复用历史数据
**缺点**: 容易Q值过估计，策略是间接的

---

### 2. PPO (Proximal Policy Optimization)

**类型**: Policy Gradient / On-Policy

**核心思想**: 通过限制策略更新幅度，保证训练稳定。

**Clipped Surrogate Objective**:
```
L^CLIP(θ) = E[min(r(θ) * A, clip(r(θ), 1-ε, 1+ε) * A)]

其中 r(θ) = π_θ(a|s) / π_θ_old(a|s) 是概率比
```

**GAE (广义优势估计)**:
```
A^GAE_t = Σ_{l=0}^{∞} (γλ)^l * δ_{t+l}
δ_t = r_t + γV(s_{t+1}) - V(s_t) 是TD误差
```

**关键组件**:
- **Actor-Critic**: Policy网络(Actor) + Value网络(Critic)
- **Clipped Loss**: 防止策略更新过大
- **GAE**: 更稳定优势估计
- **多次Epoch更新**: 充分利用每个batch数据

**优点**: 训练稳定，适合连续动作
**缺点**: 样本效率低（on-policy）

---

### 3. A2C (Advantage Actor-Critic)

**类型**: Policy Gradient / On-Policy

**核心思想**: 简化版PPO，使用N-step returns而非GAE。

**与PPO的区别**:
| 特性 | A2C | PPO |
|------|-----|-----|
| 策略更新 | 单次 | 多次epoch |
| 约束 | 无 | Clipped surrogate |
| 优势估计 | N-step | GAE |
| 复杂度 | 更简单 | 更复杂 |

**N-step Return**:
```
G_t = r_t + γ*r_{t+1} + ... + γ^{n-1}*r_{t+n-1} + γ^n*V(s_{t+n})
A_t = G_t - V(s_t)
```

**优点**: 简单高效，内存效率高
**缺点**: 没有PPO稳定

---

### 4. DDPG (Deep Deterministic Policy Gradient)

**类型**: Actor-Critic / Off-Policy

**核心思想**: 学习确定性策略，直接输出动作值。

**更新公式**:
```
Actor: μ(s) ← argmax Q(s, a)
Critic: Q(s, a) ← r + γ * Q(s', μ(s'))
```

**关键组件**:
- **确定性策略**: 输出直接是动作值
- ** Ornstein-Uhlenbeck噪声**: 时间相关的探索噪声
- **Soft Target Update**: τ=0.001，比硬更新更稳定

**优点**: 适合连续动作，样本效率高
**缺点**: 容易Q值过估计

---

### 5. SAC (Soft Actor-Critic)

**类型**: Actor-Critic / Off-Policy / 最大熵

**核心思想**: 最大化熵加权回报，自动调节探索。

**目标函数**:
```
π* = argmax E[Σ r(s,a)] + α * H(π)

其中 H(π) = -Σ π(a|s) log π(a|s) 是策略熵
```

**关键组件**:
- **随机策略**: π(a|s) 是概率分布
- **Twin Q-Networks**: 两个Q网络，取较小值减少过估计
- **自动温度调节**: 熵作为额外奖励

**优点**: 自动平衡探索与利用，样本效率高
**缺点**: 熵系数需要调节

---

### 6. TD3 (Twin Delayed DDPG)

**类型**: Actor-Critic / Off-Policy

**核心思想**: DDPG的改进版本，通过三重技巧解决Q值过估计。

**三大技巧**:

1. **Twin Q-Networks**: 使用两个Q网络，取较小值
2. **Delayed Policy Updates**: 策略网络延迟更新（每隔2步）
3. **Target Policy Smoothing**: 目标动作添加小噪声

**与DDPG对比**:
| 特性 | DDPG | TD3 |
|------|------|-----|
| Q网络 | 1个 | 2个(Twin) |
| 策略延迟更新 | 无 | 有 |
| 目标策略平滑 | 无 | 有 |
| Q值过估计 | 严重 | 较轻 |
| 性能 | 一般 | 更好 |

**优点**: 比DDPG更稳定，性能更好
**缺点**: 训练时间更长

---

## 算法对比总结

| 算法 | 类型 | 策略 | 探索方式 | 样本效率 | 适用场景 |
|------|------|------|----------|----------|----------|
| **DQN** | Value | 间接(Q值贪婪) | ε-greedy | 高 | 离散动作 |
| **PPO** | PG | 随机(softmax) | 熵正则化 | 中 | 离散/连续 |
| **A2C** | PG | 随机(softmax) | 熵正则化 | 中 | 离散/连续 |
| **DDPG** | AC | 确定性 | OU噪声 | 高 | 连续动作 |
| **SAC** | AC | 随机(softmax) | 最大熵 | 高 | 连续动作 |
| **TD3** | AC | 确定性 | 噪声+延迟 | 高 | 连续动作 |

---

## 格子世界环境 (GameEnv)

### 网格结构

- 默认尺寸: 32x32 (可配置)
- 位掩码存储多通道信息:
  - Channel 0: 智能体位置
  - Channel 1: 食物/目标位置
  - Channel 2-5: 四方向障碍物 (N/E/S/W)

### 障碍物系统

- 障碍物沿网格四边生成
- 每隔 `obstacle_freq` 步重新生成边缘障碍物
- 障碍物持续向对应方向移动:
  - N通道: 向北移动
  - E通道: 向东移动
  - S通道: 向南移动
  - W通道: 向西移动

### 奖励机制

| 事件 | 奖励 |
|------|------|
| 吃食物 | +1.5 |
| 靠近食物 | +0.05~0.1 |
| 撞障碍物 | -1 (终止) |
| 出界 | -2 (终止) |

### 状态表示

- 观测窗口: 33x33 以智能体为中心
- 6通道 tensor: `[Agent, Goal, Obs_N, Obs_E, Obs_S, Obs_W]`
- 状态维度: 6 × 33 × 33 = 6534

### 动作空间

9个离散动作 (8方向 + 原地不动):

```
7  0  1      ↖ ↑ ↗
6  8  2      ← □ →
5  4  3      ↙ ↓ ↘
```

---

## 训练输出

```
==================================================
       DQN Training - Grid World (PyTorch)
==================================================
Device: CUDA
==================================================
Episode    10 | Avg Reward:     0.03 | Epsilon: 0.0995 | Steps: 67
Episode    20 | Avg Reward:    -1.04 | Epsilon: 0.0993 | Steps: 5
...
Training Complete!
Model saved to: dqn_model_100ep.pt
```

## 评估输出

```
==================================================
       DQN Evaluation - Grid World
==================================================
Episode    | Reward     | Steps    | Food
--------------------------------------------------
1          | 1.800      | 38       | 0
2          | 3.100      | 62       | 0
...
Avg Reward:      1.624
Avg Steps:       35.3
Avg Food/Ep:     0.0
```

## 模型文件

训练后的模型保存在 `train-eval/` 目录下:
- `dqn_model_{episodes}ep.pt`
- `ppo_model_{episodes}ep.pt`
- `a2c_model_{episodes}ep.pt`
- `ddpg_model_{episodes}ep.pt`
- `sac_model_{episodes}ep.pt`
- `td3_model_{episodes}ep.pt`

加载模型进行推理或继续训练。

---

## 改进方向

### 短期优化

1. **奖励工程** - 调整奖励结构使吃食物更rewarding
2. **环境简化** - 减少障碍物密度、降低难度

### 中期目标

1. **Double DQN** - 减少Q值过估计
2. **优先经验回放 (PER)** - 优先学习重要样本
3. **网络架构调整** - 尝试CNN或更大的网络

### 长期目标

1. **迁移到ROS** - 与robotics项目结合
2. **实机控制** - 在真实机器人上部署

---

## 依赖

```bash
pip3 install torch numpy
```

验证CUDA可用性:
```bash
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```
