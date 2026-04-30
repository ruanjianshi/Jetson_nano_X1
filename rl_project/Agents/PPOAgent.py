# -*- coding: utf-8 -*-
"""
@file PPOAgent.py
@brief PPO (Proximal Policy Optimization) 智能体实现
@note 位于 rl_project/Agents/ 目录下

PPO 是一种 Policy Gradient 算法，通过限制策略更新幅度来保证训练稳定。

## PPO 算法原理

PPO 是策略梯度算法的改进版本, 通过限制策略更新幅度来避免崩溃。

### 核心组件
1. **Actor-Critic 架构**: Policy网络(Actor) + Value网络(Critic)
2. **Clipped Surrogate Objective**: 限制策略更新幅度
3. **GAE (广义优势估计)**: 更稳定优势函数估计
4. **多次 epoch 更新**: 充分利用每个 batch 的数据

### Clipped Surrogate Objective
L^CLIP(θ) = E[min(r_t(θ) * A_t, clip(r_t(θ), 1-ε, 1+ε) * A_t)]

其中 r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t) 是概率比
- 如果 A_t > 0 (好动作): 鼓励增加该动作概率, 但不超过 (1+ε)
- 如果 A_t < 0 (坏动作): 鼓励减少该动作概率, 但不低于 (1-ε)

### GAE (Generalized Advantage Estimation)
A_t^GAE = Σ_{l=0}^{∞} (γλ)^l * δ_{t+l}

其中 δ_t = r_t + γV(s_{t+1}) - V(s_t) 是TD误差

## 神经网络结构

### PolicyNetwork (Actor)
输入: 状态向量 [6534]
  -> Linear(6534, 256) + ReLU
  -> Linear(256, 128) + ReLU
  -> Linear(128, 64) + ReLU
  -> Linear(64, 9) + Softmax  # 输出9个动作的概率

### ValueNetwork (Critic)
输入: 状态向量 [6534]
  -> Linear(6534, 256) + ReLU
  -> Linear(256, 128) + ReLU
  -> Linear(128, 64) + ReLU
  -> Linear(64, 1)  # 输出状态价值 V(s)
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple
from Utils.types import DQNConfig


class PPOMemory:
    """
    @brief PPO 经验回放类
    
    存储一个 episode 的所有 experience，供 PPO 更新使用。
    
    @note 与DQN的ReplayBuffer不同, PPO存储整个episode的轨迹,
    @note 然后在train()中进行多次epoch更新。
    
    @note 存储内容:
    - states: 状态列表
    - actions: 动作列表
    - rewards: 奖励列表
    - dones: 是否终止列表
    - probs: 旧策略的动作概率列表
    """
    def __init__(self):
        """
        @brief 构造函数
        
        初始化所有存储列表为空
        """
        self.states: List[List[float]] = []   # 状态列表
        self.actions: List[int] = []          # 动作列表
        self.rewards: List[float] = []        # 奖励列表
        self.dones: List[bool] = []           # 终止标志列表
        self.probs: List[float] = []          # 旧策略的动作概率

    def add(self, state: List[float], action: int, reward: float, done: bool, prob: float):
        """
        @brief 添加一个 transition
        
        @param state: 当前状态
        @param action: 采取的动作
        @param reward: 获得的奖励
        @param done: 是否终止
        @param prob: 旧策略选择该动作的概率
        """
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)
        self.probs.append(prob)

    def clear(self):
        """
        @brief 清空缓冲区
        
        @note 在每个episode训练后调用
        """
        self.states = []
        self.actions = []
        self.rewards = []
        self.dones = []
        self.probs = []

    def __len__(self):
        """
        @brief 获取存储的样本数量
        
        @return 状态列表的长度
        """
        return len(self.states)


class PPOPolicyNetwork(nn.Module):
    """
    @brief Policy 网络 (Actor)
    
    输入: 状态向量
    输出: 动作概率分布
    
    @note 使用Softmax输出, 保证输出是有效的概率分布:
    - 所有概率 >= 0
    - 所有概率之和 = 1
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        """
        @brief 构造函数
        
        @param state_dim: 状态维度 (6534)
        @param action_dim: 动作维度 (9)
        @param hidden_dims: 隐藏层维度
        """
        super(PPOPolicyNetwork, self).__init__()

        if hidden_dims is None:
            hidden_dims = [256, 128, 64]

        # 构建网络层
        layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
            ])
            prev_dim = hidden_dim

        # 输出层: 输出动作的logits (未归一化的概率)
        layers.append(nn.Linear(prev_dim, action_dim))
        
        # Softmax: 将logits转换为概率分布
        layers.append(nn.Softmax(dim=-1))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        @brief 前向传播
        
        @param x: 输入状态 [batch_size, state_dim]
        @return 动作概率 [batch_size, action_dim]
        """
        return self.network(x)


class PPOValueNetwork(nn.Module):
    """
    @brief Value 网络 (Critic)
    
    输入: 状态向量
    输出: 状态价值 V(s)
    
    @note V(s) 表示在状态s下的预期累积奖励
    @note 用于计算Advantage: A(s,a) = Q(s,a) - V(s)
    """
    def __init__(self, state_dim: int, hidden_dims: List[int] = None):
        """
        @brief 构造函数
        
        @param state_dim: 状态维度
        @param hidden_dims: 隐藏层维度
        """
        super(PPOValueNetwork, self).__init__()

        if hidden_dims is None:
            hidden_dims = [256, 128, 64]

        layers = []
        prev_dim = state_dim
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
            ])
            prev_dim = hidden_dim

        # 输出层: 单个标量值 (状态价值)
        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        @brief 前向传播
        
        @param x: 输入状态 [batch_size, state_dim]
        @return 状态价值 [batch_size, 1]
        """
        return self.network(x)


class PPOAgent:
    """
    @brief PPO 智能体类
    
    使用 PPO 算法进行策略学习:
    - Actor-Critic 架构
    - Clipped Surrogate Objective
    - GAE 优势函数估计
    - 多次 epoch 更新
    
    @note device_v: 计算设备 (cuda/cpu)
    @note policy_v: Policy网络 (Actor) - 输出动作概率
    @note value_v: Value网络 (Critic) - 输出状态价值
    @note memory_v: 经验回放缓冲区
    @note epsilon_v: 探索率 (用于动作选择, PPO不需要但保留接口)
    
    @example
        # 创建智能体
        config = DQNConfig()
        agent = PPOAgent(config)
        
        # 选择动作 (返回动作和概率)
        action_idx, action_prob = agent.select_action(state_tensor)
        
        # 存储经验
        agent.store_transition(state, action, reward, done, action_prob)
        
        # 训练 (每个episode后调用)
        agent.train()
    """
    __slots__ = ('device_v', 'policy_v', 'value_v', 'optimizer',
                  'memory_v', 'epsilon_v', 'config_v', 'training_step_v')

    def __init__(self, config: DQNConfig = None):
        """
        @brief 构造函数
        
        @param config: 配置对象, 如果为None则使用默认配置
        """
        if config is None:
            config = DQNConfig()
        self.config_v: DQNConfig = config

        # === 设置计算设备 ===
        self.device_v = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[PPOAgent] Using device: {self.device_v}")

        self.training_step_v = 0

        state_dim = config.state_dim_v
        action_dim = config.action_dim_v

        # === 创建Actor网络 (Policy) ===
        self.policy_v = PPOPolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        
        # === 创建Critic网络 (Value) ===
        self.value_v = PPOValueNetwork(state_dim, [256, 128, 64]).to(self.device_v)

        # === 创建优化器 ===
        # 使用Adam, Actor学习率正常, Critic学习率2倍
        self.optimizer = optim.Adam([
            {'params': self.policy_v.parameters(), 'lr': config.learning_rate_v},
            {'params': self.value_v.parameters(), 'lr': config.learning_rate_v * 2}
        ])

        # === 创建经验回放缓冲区 ===
        self.memory_v = PPOMemory()

        # === 探索率 (PPO不使用, 但保留接口) ===
        self.epsilon_v = config.epsilon_start_v

    def select_action(self, state: List[float]) -> Tuple[int, float]:
        """
        @brief 选择动作
        
        @param state: 状态列表 [6534]
        @return (action_idx, action_prob) - 动作索引和选择该动作的概率
        
        @note PPO使用概率采样而非贪婪选择:
        - 根据策略网络的输出概率分布随机采样
        - 这自然地提供了探索 (与epsilon-greedy不同)
        
        @example
            action_idx, action_prob = agent.select_action(state_tensor)
        """
        # 转换为tensor
        state_tensor = torch.FloatTensor(state).to(self.device_v)

        with torch.no_grad():
            # 获取动作概率分布
            probs = self.policy_v(state_tensor)

        # 根据概率分布随机采样一个动作
        action = random.choices(
            range(len(probs)),
            weights=probs.cpu().numpy(),
            k=1
        )[0]

        # 记录选择该动作的概率 (用于后续计算重要性采样比)
        prob = probs[action].item()

        return action, prob

    def store_transition(self, state: List[float], action: int, reward: float,
                         done: bool, prob: float):
        """
        @brief 存储经验到轨迹缓冲区
        
        @param state: 当前状态
        @param action: 采取的动作
        @param reward: 获得的奖励
        @param done: 是否终止
        @param prob: 选择该动作的概率 (来自旧策略)
        
        @note 与DQN不同, PPO存储整个episode后才更新
        """
        self.memory_v.add(state, action, reward, done, prob)

    def compute_gae(self, rewards: List[float], dones: List[bool],
                    next_state: List[float]) -> Tuple[List[float], List[float]]:
        """
        @brief 计算 GAE (Generalized Advantage Estimation)
        
        GAE是一种更稳定、更灵活的优势函数估计方法。
        
        @param rewards: 奖励列表
        @param dones: 终止标志列表
        @param next_state: 下一个状态
        @return (advantages, returns) - 优势和返回值
        
        @note Advantage A(s,a) = Q(s,a) - V(s)
        - A > 0: 该动作比平均水平好, 应该增加概率
        - A < 0: 该动作比平均水平差, 应该减少概率
        
        @note Returns = Advantage + Value = Q(s,a) 的估计
        """
        # 转换为tensor
        rewards_tensor = torch.FloatTensor(rewards).to(self.device_v)
        dones_tensor = torch.FloatTensor(dones).to(self.device_v)
        next_state_tensor = torch.FloatTensor(next_state).to(self.device_v)

        # === 计算下一个状态的价值 ===
        with torch.no_grad():
            next_value = self.value_v(next_state_tensor).item()

        # === 计算所有状态的价值 ===
        values = []
        with torch.no_grad():
            for i in range(len(rewards)):
                state_tensor = torch.FloatTensor(self.memory_v.states[i]).to(self.device_v)
                values.append(self.value_v(state_tensor).item())

        # 添加最后一个状态的价值
        values = torch.FloatTensor(values + [next_value]).to(self.device_v)

        # === 计算GAE优势 ===
        advantages = []
        gae = 0
        gamma = self.config_v.gamma_v
        lambda_ = 0.95  # GAE参数

        # 从后向前计算 (TD误差的累加)
        for i in reversed(range(len(rewards))):
            # TD误差: δ = r + γ * V(s') - V(s)
            delta = rewards_tensor[i] + gamma * values[i + 1] * (1 - dones_tensor[i]) - values[i]
            
            # GAE: A = δ + γλ * A (从后向前累加)
            gae = delta + gamma * lambda_ * (1 - dones_tensor[i]) * gae
            advantages.append(gae)
        
        # 反转顺序 (从前往后)
        advantages = list(reversed(advantages))

        # === 标准化优势 ===
        advantages = torch.FloatTensor(advantages).to(self.device_v)
        returns = advantages + values[:-1]  # Returns = Advantage + Value
        
        # 标准化: (A - mean) / std, 减少方差
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        return advantages.tolist(), returns.tolist()

    def train(self) -> None:
        """
        @brief 训练 PPO (一个 episode 的更新)
        
        @note 训练步骤:
        1. 检查样本数是否足够
        2. 计算GAE优势
        3. 多次epoch更新:
           a. 计算新策略的动作概率
           b. 计算重要性采样比 r(θ)
           c. 计算Clipped Surrogate损失
           d. 计算价值损失
           e. 计算熵损失 (鼓励探索)
           f. 反向传播更新
        4. 清空经验缓冲区
        
        @note 与DQN不同, PPO在每个episode结束后进行一次更新,
        @note 但会进行多个epoch的更新来充分利用数据。
        """
        # === 检查样本数 ===
        if len(self.memory_v) < 10:
            self.memory_v.clear()
            return

        # === 准备数据 ===
        states = torch.FloatTensor(self.memory_v.states).to(self.device_v)
        actions = torch.LongTensor(self.memory_v.actions).to(self.device_v)

        # === 计算GAE ===
        advantages, returns = self.compute_gae(
            self.memory_v.rewards,
            self.memory_v.dones,
            self.memory_v.states[-1]
        )

        advantages_tensor = torch.FloatTensor(advantages).to(self.device_v)
        returns_tensor = torch.FloatTensor(returns).to(self.device_v)
        old_probs = torch.FloatTensor(self.memory_v.probs).to(self.device_v)

        # === PPO超参数 ===
        clip_epsilon = 0.1    # Clip范围 [1-ε, 1+ε] = [0.9, 1.1]
        k_epochs = 10         # 每次更新的epoch数
        entropy_coef = 0.05   # 熵正则化系数

        # === 多次epoch更新 ===
        for _ in range(k_epochs):
            # 随机打乱顺序
            idx = torch.randperm(len(states))
            
            # 遍历每个样本
            for i in idx:
                state_i = states[i:i+1]           # [1, state_dim]
                action_i = actions[i]               # scalar
                old_prob_i = old_probs[i]           # 旧策略的概率
                advantage_i = advantages_tensor[i]   # 优势
                return_i = returns_tensor[i]       # 返回值

                # === 计算新策略的动作概率 ===
                probs = self.policy_v(state_i)
                new_prob = probs[0, action_i]  # 选择动作的概率

                # === 计算重要性采样比 ===
                # r(θ) = π_θ(a|s) / π_θ_old(a|s)
                ratio = new_prob / (old_prob_i + 1e-8)

                # === 计算Surrogate损失 ===
                # L^CLIP = min(r(θ) * A, clip(r(θ), 1-ε, 1+ε) * A)
                surr1 = ratio * advantage_i
                surr2 = torch.clamp(ratio, 1 - clip_epsilon, 1 + clip_epsilon) * advantage_i
                policy_loss = -torch.min(surr1, surr2).mean()

                # === 计算熵损失 ===
                # H(π) = -Σ π(a|s) * log π(a|s)
                # 熵越大, 策略越随机 (探索越多)
                entropy = -(probs * torch.log(probs + 1e-8)).sum()

                # === 计算价值损失 ===
                # L_V = (V(s) - G_t)^2
                value_pred = self.value_v(state_i)
                value_loss = nn.MSELoss()(value_pred, return_i.unsqueeze(0))

                # === 总损失 ===
                # L = L_policy + 0.5 * L_value - entropy_coef * H
                loss = policy_loss + 0.5 * value_loss - entropy_coef * entropy

                # === 反向传播 ===
                self.optimizer.zero_grad()
                loss.backward()
                
                # 梯度裁剪, 防止训练不稳定
                torch.nn.utils.clip_grad_norm_(self.policy_v.parameters(), 0.5)
                torch.nn.utils.clip_grad_norm_(self.value_v.parameters(), 0.5)
                
                self.optimizer.step()

            self.training_step_v += 1

        # === 清空经验缓冲区 ===
        self.memory_v.clear()

        # === 衰减探索率 (PPO不需要但保留接口) ===
        if self.epsilon_v > self.config_v.epsilon_end_v:
            decay = (self.config_v.epsilon_start_v - self.config_v.epsilon_end_v) / self.config_v.epsilon_decay_steps_v
            self.epsilon_v = max(self.epsilon_v - decay, self.config_v.epsilon_end_v)

    def get_epsilon(self) -> float:
        """
        @brief 获取当前探索率
        
        @return epsilon值
        
        @note PPO不使用epsilon-greedy, 但保留接口
        """
        return self.epsilon_v

    def set_epsilon(self, epsilon: float) -> None:
        """
        @brief 设置探索率
        
        @param epsilon: 新的epsilon值
        
        @note PPO不需要但保留接口
        """
        self.epsilon_v = epsilon

    def memory_size(self) -> int:
        """
        @brief 获取经验缓冲区大小
        
        @return 缓冲区中的样本数
        """
        return len(self.memory_v)

    def save(self, path: str) -> None:
        """
        @brief 保存模型
        
        @param path: 保存路径
        
        @note 保存内容:
        - policy: Actor网络权重
        - value: Critic网络权重
        - optimizer: 优化器状态
        - epsilon: 探索率
        - training_step: 训练步数
        """
        torch.save({
            'policy': self.policy_v.state_dict(),
            'value': self.value_v.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon_v,
            'training_step': self.training_step_v,
        }, path)
        print(f"[PPOAgent] Model saved to {path}")

    def load(self, path: str) -> None:
        """
        @brief 加载模型
        
        @param path: 模型文件路径
        
        @note 从保存的状态继续训练或推理
        """
        checkpoint = torch.load(path, map_location=self.device_v)
        self.policy_v.load_state_dict(checkpoint['policy'])
        self.value_v.load_state_dict(checkpoint['value'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon_v = checkpoint['epsilon']
        self.training_step_v = checkpoint['training_step']
        print(f"[PPOAgent] Model loaded from {path}")
