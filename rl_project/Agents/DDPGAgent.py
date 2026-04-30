# -*- coding: utf-8 -*-
"""
@file DDPGAgent.py
@brief DDPG (Deep Deterministic Policy Gradient) 智能体实现
@note 位于 rl_project/Agents/ 目录下

DDPG 是用于连续动作空间的算法，但可以适配离散动作空间。

## DDPG 算法原理 (连续动作版)

1. **Actor (Policy)**: 学习确定性策略 μ(s)
   - 输出: 直接输出动作值 (而非概率)
   - 损失: -Q(s, μ(s))  (最大化Q值)

2. **Critic**: 学习 Q(s, a)
   - 输出: 状态-动作对的Q值
   - 损失: (r + γ*Q_target(s', μ(s')) - Q(s, a))^2

3. **目标网络**: 稳定训练
   - 使用 soft update 而非 hard copy

## 离散动作空间适配

由于环境使用离散动作 (9个动作)，我们对 DDPG 进行适配:
- Actor 输出各动作的 Q 值 (像 DQN 一样)
- 使用 Ornstein-Uhlenbeck 噪声进行探索
- 选择 Q 值最大的动作 (贪婪)

## 与 DQN 的区别

| 特性 | DQN | DDPG |
|------|-----|------|
| 策略 | 间接通过 Q 值 | 直接学习策略 |
| 动作输出 | Q 值最大 | 直接输出 |
| 探索 | Epsilon-greedy | 噪声添加到动作 |
| 目标网络 | Hard copy | Soft update |
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple
from Utils.types import DQNConfig


class DDPGPolicyNetwork(nn.Module):
    """
    @brief Policy 网络 (Actor)
    
    输入: 状态向量
    输出: 各动作的 Q 值 (用于离散动作空间)
    
    @note 与 QNetwork 类似，但用于 Actor-Critic 结构
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(DDPGPolicyNetwork, self).__init__()

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

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """@brief 输出各动作的Q值 (用于选择最大Q值的动作)"""
        return self.network(x)


class DDPGQNetwork(nn.Module):
    """
    @brief Q 网络 (Critic)
    
    输入: 状态向量
    输出: 状态-动作对的 Q 值
    
    @note 这是 DDPG 的 Critic，评估给定状态-动作对的价值
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(DDPGQNetwork, self).__init__()

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

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """@brief 输出各动作的Q值"""
        return self.network(x)


class OUNoise:
    """
    @brief Ornstein-Uhlenbeck 噪声
    
    用于 DDPG 的探索噪声，产生 временно 相关的时间序列噪声。
    
    @note 噪声具有均值回归特性，适合连续动作空间
    @note 对于离散动作空间，我们添加到 Q 值上进行探索
    """
    def __init__(self, size: int, mu: float = 0.0, theta: float = 0.15, sigma: float = 0.2):
        """
        @brief 构造函数
        
        @param size: 噪声维度 (动作数量)
        @param mu: 噪声均值
        @param theta: 均值回归速度
        @param sigma: 噪声强度
        """
        self.size = size
        self.mu = mu
        self.theta = theta
        self.sigma = sigma
        self.state = np.ones(size) * mu

    def reset(self):
        """@brief 重置噪声状态"""
        self.state = np.ones(self.size) * self.mu

    def sample(self) -> np.ndarray:
        """
        @brief 采样噪声
        
        @return 噪声向量
        """
        dx = self.theta * (self.mu - self.state) + self.sigma * np.random.randn(self.size)
        self.state += dx
        return self.state


class DDPGAgent:
    """
    @brief DDPG 智能体类
    
    Deep Deterministic Policy Gradient:
    - Actor: 学习确定性策略 μ(s)
    - Critic: 学习 Q(s, a)
    - 使用双网络 + 目标网络
    - 使用 Ornstein-Uhlenbeck 噪声探索
    
    @note 适配离散动作: Actor 输出 Q 值，选择最大 Q 的动作
    
    @example
        config = DQNConfig()
        agent = DDPGAgent(config)
        
        action_idx = agent.select_action(state_tensor)
        agent.store_transition(transition)
        agent.train()
    """
    __slots__ = ('device_v', 'policy_v', 'target_policy_v', 'q_network_v',
                 'target_q_network_v', 'optimizer_policy', 'optimizer_q',
                 'memory_v', 'config_v', 'training_step_v', 'noise',
                 'epsilon_v', 'gamma_v', 'tau_v')

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
        print(f"[DDPGAgent] Using device: {self.device_v}")

        self.training_step_v = 0
        
        # === DDPG 超参数 ===
        self.gamma_v = config.gamma_v  # 折扣因子
        self.tau_v = 0.001             # Soft update 系数 (很小确保稳定)
        self.epsilon_v = config.epsilon_start_v  # 探索率

        state_dim = config.state_dim_v
        action_dim = config.action_dim_v

        # === 创建网络 ===
        # Actor (Policy)
        self.policy_v = DDPGPolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_policy_v = DDPGPolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_policy_v.load_state_dict(self.policy_v.state_dict())
        self.target_policy_v.eval()
        
        # Critic (Q-Network)
        self.q_network_v = DDPGQNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_q_network_v = DDPGQNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_q_network_v.load_state_dict(self.q_network_v.state_dict())
        self.target_q_network_v.eval()

        # === 创建优化器 ===
        self.optimizer_policy = optim.Adam(self.policy_v.parameters(), lr=config.learning_rate_v)
        self.optimizer_q = optim.Adam(self.q_network_v.parameters(), lr=config.learning_rate_v * 2)

        # === 经验回放缓冲区 ===
        self.memory_v: List = []

        # === 探索噪声 ===
        self.noise = OUNoise(action_dim, mu=0.0, theta=0.15, sigma=0.3)

    def select_action(self, state: List[float]) -> int:
        """
        @brief 选择动作
        
        @param state: 状态列表
        @return 选择的动作索引
        
        @note 使用带噪声的贪婪策略:
        1. 获取 Actor 的 Q 值输出
        2. 添加 Ornstein-Uhlenbeck 噪声
        3. 选择 Q 值最大的动作
        """
        state_tensor = torch.FloatTensor(state).to(self.device_v)

        with torch.no_grad():
            # 获取 Q 值
            q_values = self.policy_v(state_tensor)
            
            # 添加噪声进行探索
            noise = self.noise.sample() * self.epsilon_v
            noise_tensor = torch.FloatTensor(noise).to(self.device_v)
            q_values = q_values + noise_tensor
            
            # 选择最大 Q 值的动作
            action = int(q_values.argmax().item())

        return action

    def store_transition(self, transition) -> None:
        """
        @brief 存储经验
        
        @param transition: Transition 对象
        """
        if len(self.memory_v) >= self.config_v.memory_capacity_v:
            self.memory_v.pop(0)
        self.memory_v.append(transition)

    def train(self) -> None:
        """
        @brief 训练 DDPG
        
        @note 训练步骤:
        1. 采样 batch
        2. 从 target policy 获取下一动作
        3. 从 target Q 获取目标 Q 值
        4. 更新 Critic: (r + γ*Q_target - Q)^2
        5. 更新 Actor: -Q (最大化 Q)
        6. Soft update 目标网络
        """
        if len(self.memory_v) < self.config_v.batch_size_v:
            return

        # === 采样 batch ===
        batch = random.sample(self.memory_v, self.config_v.batch_size_v)

        batch_state = torch.FloatTensor([t.state_v for t in batch]).to(self.device_v)
        batch_action = torch.LongTensor([t.action_v for t in batch]).to(self.device_v)
        batch_reward = torch.FloatTensor([t.reward_v for t in batch]).to(self.device_v)
        batch_next_state = torch.FloatTensor([t.next_state_v for t in batch]).to(self.device_v)
        batch_terminal = torch.BoolTensor([t.terminal_v for t in batch]).to(self.device_v)

        # === 更新 Critic ===
        with torch.no_grad():
            # 目标策略网络输出的 Q 值
            next_q = self.target_policy_v(batch_next_state)
            # 选择最大 Q 值的动作
            next_action = next_q.argmax(dim=1)
            # 目标 Q 网络输出的 Q 值
            target_q = self.target_q_network_v(batch_next_state)
            # Gather 选择的动作对应的 Q 值
            target_q = target_q.gather(1, next_action.unsqueeze(1)).squeeze(1)
            # 目标 Q 值
            target_q = batch_reward + self.gamma_v * target_q * (~batch_terminal)

        # 当前 Q 网络的 Q 值
        current_q = self.q_network_v(batch_state)
        current_q = current_q.gather(1, batch_action.unsqueeze(1)).squeeze(1)
        
        # Critic 损失
        q_loss = nn.MSELoss()(current_q, target_q)

        self.optimizer_q.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network_v.parameters(), 10.0)
        self.optimizer_q.step()

        # === 更新 Actor ===
        # Actor 损失: 最大化 Q 值
        policy_q = self.policy_v(batch_state)
        # 选择每个状态最大 Q 值的动作
        policy_action = policy_q.argmax(dim=1)
        # 计算这些动作的 Q 值
        policy_q_values = self.q_network_v(batch_state)
        policy_q = policy_q_values.gather(1, policy_action.unsqueeze(1)).squeeze(1)
        
        # Actor 损失: 最小化 -Q 等价于最大化 Q
        policy_loss = -policy_q.mean()

        self.optimizer_policy.zero_grad()
        policy_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_v.parameters(), 10.0)
        self.optimizer_policy.step()

        # === Soft update 目标网络 ===
        self._soft_update(self.policy_v, self.target_policy_v)
        self._soft_update(self.q_network_v, self.target_q_network_v)

        self.training_step_v += 1

        # === 衰减探索噪声 ===
        if self.epsilon_v > self.config_v.epsilon_end_v:
            self.epsilon_v -= (self.config_v.epsilon_start_v - self.config_v.epsilon_end_v) / self.config_v.epsilon_decay_steps_v
            self.noise.reset()

    def _soft_update(self, source: nn.Module, target: nn.Module):
        """
        @brief Soft update 目标网络
        
        @param source: 源网络 (当前网络)
        @param target: 目标网络
        
        @note target = τ * source + (1-τ) * target
        @note τ 通常很小 (如 0.001)
        """
        for target_param, source_param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                self.tau_v * source_param.data + (1.0 - self.tau_v) * target_param.data
            )

    def get_epsilon(self) -> float:
        """@brief 获取当前探索率"""
        return self.epsilon_v

    def set_epsilon(self, epsilon: float) -> None:
        """@brief 设置探索率"""
        self.epsilon_v = epsilon

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
            'target_policy': self.target_policy_v.state_dict(),
            'q_network': self.q_network_v.state_dict(),
            'target_q_network': self.target_q_network_v.state_dict(),
            'optimizer_policy': self.optimizer_policy.state_dict(),
            'optimizer_q': self.optimizer_q.state_dict(),
            'epsilon': self.epsilon_v,
            'training_step': self.training_step_v,
        }, path)
        print(f"[DDPGAgent] Model saved to {path}")

    def load(self, path: str) -> None:
        """
        @brief 加载模型
        
        @param path: 模型文件路径
        """
        checkpoint = torch.load(path, map_location=self.device_v)
        self.policy_v.load_state_dict(checkpoint['policy'])
        self.target_policy_v.load_state_dict(checkpoint['target_policy'])
        self.q_network_v.load_state_dict(checkpoint['q_network'])
        self.target_q_network_v.load_state_dict(checkpoint['target_q_network'])
        self.optimizer_policy.load_state_dict(checkpoint['optimizer_policy'])
        self.optimizer_q.load_state_dict(checkpoint['optimizer_q'])
        self.epsilon_v = checkpoint['epsilon']
        self.training_step_v = checkpoint['training_step']
        print(f"[DDPGAgent] Model loaded from {path}")
