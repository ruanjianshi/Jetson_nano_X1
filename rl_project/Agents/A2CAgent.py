# -*- coding: utf-8 -*-
"""
@file A2CAgent.py
@brief A2C (Advantage Actor-Critic) 智能体实现
@note 位于 rl_project/Agents/ 目录下

A2C 是 Actor-Critic 算法的一种变体, 是 A3C (Asynchronous Advantage Actor-Critic) 的同步版本。

## A2C vs PPO

A2C 比 PPO 更简单:
- 不使用 clipped surrogate objective
- 不进行多 epoch 更新
- 每个 episode 只进行一次策略更新
- 使用 N-step returns 而非 GAE

## 算法原理

1. **Actor (Policy)**: 学习策略 π(a|s)
   - 输出: 各动作的概率
   - 损失: -logπ(a|s) * A(s,a)

2. **Critic (Value)**: 学习状态价值 V(s)
   - 输出: 状态价值
   - 损失: (R - V(s))^2

3. **Advantage**: A(s,a) = R - V(s)
   - 使用 N-step return: R = r_t + γ*r_{t+1} + ... + γ^{n-1}*r_{t+n-1} + γ^n*V(s_{t+n})

## 与 PPO 的区别

| 特性 | A2C | PPO |
|------|-----|-----|
| 策略更新 | 单次 | 多次 epoch |
| 约束 | 无 | Clipped surrogate |
| 优势估计 | N-step | GAE |
| 复杂度 | ⭐⭐ | ⭐⭐⭐ |
| 内存效率 | 高 | 中 |
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple
from Utils.types import DQNConfig


class A2CMemory:
    """
    @brief A2C 经验回放类
    
    存储一个 episode 的所有 experience，供 A2C 更新使用。
    与 PPO 不同，A2C 在 episode 结束后进行一次性更新。
    
    @note 与 PPOMemory 类似，但不需要存储 old_probs
    """
    def __init__(self):
        """@brief 构造函数，初始化所有存储列表为空"""
        self.states: List[List[float]] = []   # 状态列表
        self.actions: List[int] = []          # 动作列表
        self.rewards: List[float] = []        # 奖励列表
        self.dones: List[bool] = []           # 终止标志列表

    def add(self, state: List[float], action: int, reward: float, done: bool):
        """
        @brief 添加一个 transition
        
        @param state: 当前状态
        @param action: 采取的动作
        @param reward: 获得的奖励
        @param done: 是否终止
        """
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)

    def clear(self):
        """@brief 清空缓冲区"""
        self.states = []
        self.actions = []
        self.rewards = []
        self.dones = []

    def __len__(self):
        """@brief 获取存储的样本数量"""
        return len(self.states)


class A2CPolicyNetwork(nn.Module):
    """
    @brief Policy 网络 (Actor)
    
    输入: 状态向量
    输出: 动作概率分布
    
    @note 与 PPO 的 PolicyNetwork 结构相同
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(A2CPolicyNetwork, self).__init__()

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

        layers.append(nn.Linear(prev_dim, action_dim))
        layers.append(nn.Softmax(dim=-1))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class A2CValueNetwork(nn.Module):
    """
    @brief Value 网络 (Critic)
    
    输入: 状态向量
    输出: 状态价值 V(s)
    
    @note 与 PPO 的 ValueNetwork 结构相同
    """
    def __init__(self, state_dim: int, hidden_dims: List[int] = None):
        super(A2CValueNetwork, self).__init__()

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

        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class A2CAgent:
    """
    @brief A2C 智能体类
    
    Advantage Actor-Critic 算法:
    - Actor: 学习策略 π(a|s)
    - Critic: 学习状态价值 V(s)
    - 使用 N-step returns 计算 advantage
    
    @note A2C 是同步版本，比 A3C 更简单
    @note 比 PPO 更简单，没有 clipped 和多 epoch
    
    @example
        config = DQNConfig()
        agent = A2CAgent(config)
        
        action_idx, _ = agent.select_action(state_tensor)
        agent.store_transition(state, action, reward, done)
        agent.train()
    """
    __slots__ = ('device_v', 'policy_v', 'value_v', 'optimizer',
                 'memory_v', 'config_v', 'training_step_v', 'gamma_v', 'n_steps_v')

    def __init__(self, config: DQNConfig = None):
        """
        @brief 构造函数
        
        @param config: 配置对象
        """
        if config is None:
            config = DQNConfig()
        self.config_v: DQNConfig = config

        # === 设置计算设备 ===
        self.device_v = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[A2CAgent] Using device: {self.device_v}")

        self.training_step_v = 0
        
        # A2C 超参数
        self.gamma_v = config.gamma_v  # 折扣因子
        self.n_steps_v = 16            # N-step return 的 n 值

        state_dim = config.state_dim_v
        action_dim = config.action_dim_v

        # === 创建网络 ===
        self.policy_v = A2CPolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.value_v = A2CValueNetwork(state_dim, [256, 128, 64]).to(self.device_v)

        # === 创建优化器 ===
        # Actor 和 Critic 使用不同的学习率
        self.optimizer = optim.Adam([
            {'params': self.policy_v.parameters(), 'lr': config.learning_rate_v},
            {'params': self.value_v.parameters(), 'lr': config.learning_rate_v * 2}
        ])

        # === 创建经验回放缓冲区 ===
        self.memory_v = A2CMemory()

    def select_action(self, state: List[float]) -> Tuple[int, float]:
        """
        @brief 选择动作
        
        @param state: 状态列表 [6534]
        @return (action_idx, action_prob)
        
        @note 使用概率采样进行动作选择
        """
        state_tensor = torch.FloatTensor(state).to(self.device_v)

        with torch.no_grad():
            probs = self.policy_v(state_tensor)

        action = random.choices(
            range(len(probs)),
            weights=probs.cpu().numpy(),
            k=1
        )[0]

        prob = probs[action].item()

        return action, prob

    def store_transition(self, state: List[float], action: int, reward: float, done: bool):
        """
        @brief 存储经验
        
        @param state: 当前状态
        @param action: 采取的动作
        @param reward: 获得的奖励
        @param done: 是否终止
        """
        self.memory_v.add(state, action, reward, done)

    def compute_n_step_returns(self) -> Tuple[List[float], List[float]]:
        """
        @brief 计算 N-step Returns 和 Advantages
        
        @return (returns, advantages)
        
        @note N-step return:
        G_t = r_t + γ*r_{t+1} + ... + γ^{n-1}*r_{t+n-1} + γ^n*V(s_{t+n})
        
        @note Advantage:
        A_t = G_t - V(s_t)
        """
        states = self.memory_v.states
        rewards = self.memory_v.rewards
        dones = self.memory_v.dones
        
        if len(states) == 0:
            return [], []
        
        # 计算最后一个状态的value作为bootstrap
        with torch.no_grad():
            last_state = torch.FloatTensor(states[-1]).to(self.device_v)
            last_value = self.value_v(last_state).item()
        
        # 计算所有状态的value
        values = []
        with torch.no_grad():
            for s in states:
                s_tensor = torch.FloatTensor(s).to(self.device_v)
                values.append(self.value_v(s_tensor).item())
        
        # 计算 n-step returns
        n = self.n_steps_v
        returns = []
        advantages = []
        
        for t in range(len(states)):
            # 目标状态索引
            target_n = min(t + n, len(states))
            
            # 计算 n-step return
            G = 0.0
            for i in range(t, target_n):
                G += (self.gamma_v ** (i - t)) * rewards[i]
            
            # 如果不是终止状态，加上bootstrap value
            if target_n < len(states):
                G += (self.gamma_v ** n) * values[target_n]
            else:
                G += (self.gamma_v ** (len(states) - t - 1)) * last_value
            
            returns.append(G)
            advantages.append(G - values[t])
        
        return returns, advantages

    def train(self) -> None:
        """
        @brief 训练 A2C
        
        @note 训练步骤:
        1. 计算 N-step returns 和 advantages
        2. 计算策略损失: -logπ(a|s) * A(s,a)
        3. 计算价值损失: (G - V(s))^2
        4. 反向传播更新
        5. 清空经验缓冲区
        """
        if len(self.memory_v) < 5:
            self.memory_v.clear()
            return

        # === 计算 N-step returns ===
        returns, advantages = self.compute_n_step_returns()
        
        if len(returns) == 0:
            return

        # === 准备数据 ===
        states = torch.FloatTensor(self.memory_v.states).to(self.device_v)
        actions = torch.LongTensor(self.memory_v.actions).to(self.device_v)
        returns_tensor = torch.FloatTensor(returns).to(self.device_v)
        advantages_tensor = torch.FloatTensor(advantages).to(self.device_v)

        # === 标准化 advantages ===
        advantages_tensor = (advantages_tensor - advantages_tensor.mean()) / (advantages_tensor.std() + 1e-8)

        # === 计算策略损失 ===
        # L_policy = -logπ(a|s) * A(s,a)
        log_probs = torch.log(self.policy_v(states) + 1e-8)
        action_log_probs = log_probs.gather(1, actions.unsqueeze(1)).squeeze(1)
        policy_loss = -(action_log_probs * advantages_tensor).mean()

        # === 计算价值损失 ===
        # L_value = (G - V(s))^2
        values = self.value_v(states).squeeze(1)
        value_loss = nn.MSELoss()(values, returns_tensor)

        # === 总损失 ===
        # A2C 通常对价值损失使用较小的系数
        loss = policy_loss + 0.5 * value_loss

        # === 反向传播 ===
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_v.parameters(), 0.5)
        torch.nn.utils.clip_grad_norm_(self.value_v.parameters(), 0.5)
        self.optimizer.step()

        self.training_step_v += 1
        
        # === 清空经验缓冲区 ===
        self.memory_v.clear()

    def get_epsilon(self) -> float:
        """@brief 获取探索率 (A2C不使用，返回0)"""
        return 0.0

    def set_epsilon(self, epsilon: float) -> None:
        """@brief 设置探索率 (A2C不使用)"""
        pass

    def memory_size(self) -> int:
        """@brief 获取经验缓冲区大小"""
        return len(self.memory_v)

    def save(self, path: str) -> None:
        """
        @brief 保存模型
        
        @param path: 保存路径
        """
        torch.save({
            'policy': self.policy_v.state_dict(),
            'value': self.value_v.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'training_step': self.training_step_v,
        }, path)
        print(f"[A2CAgent] Model saved to {path}")

    def load(self, path: str) -> None:
        """
        @brief 加载模型
        
        @param path: 模型文件路径
        """
        checkpoint = torch.load(path, map_location=self.device_v)
        self.policy_v.load_state_dict(checkpoint['policy'])
        self.value_v.load_state_dict(checkpoint['value'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.training_step_v = checkpoint['training_step']
        print(f"[A2CAgent] Model loaded from {path}")
