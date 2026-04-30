# -*- coding: utf-8 -*-
"""
@file TD3Agent.py
@brief TD3 (Twin Delayed DDPG) 智能体实现
@note 位于 rl_project/Agents/ 目录下

TD3 是 DDPG 的改进版本，通过三重技巧解决 Q 值过估计问题。

## TD3 三大技巧

1. **Twin Q-Networks**: 使用两个 Q 网络，取较小值
   - 减少 Q 值过估计
   - 类似 Double DQN 的思想

2. **Delayed Policy Updates**: 策略网络延迟更新
   - 每隔 d 个步骤更新一次策略
   - 在 Q 网络更稳定后再更新策略

3. **Target Policy Smoothing**: 目标策略平滑
   - 在目标动作上添加小噪声
   - 减少策略的方差

## DDPG vs TD3

| 特性 | DDPG | TD3 |
|------|------|-----|
| Q 网络 | 1个 | 2个 (Twin) |
| 策略延迟更新 | 无 | 有 |
| 目标策略平滑 | 无 | 有 |
| Q 值过估计 | 严重 | 较轻 |
| 性能 | 一般 | 更好 |

## 算法原理

1. **Actor**: 学习确定性策略 μ(s)
2. **Critic**: 学习 Q(s, μ(s))
3. **Twin Critics**: 两个 Q 网络，取最小值

## 离散动作空间适配

对于离散动作:
- Actor 输出各动作的 Q 值
- 添加噪声到 Q 值进行探索
- 选择最大 Q 值的动作
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple
from Utils.types import DQNConfig


class TD3PolicyNetwork(nn.Module):
    """
    @brief Policy 网络 (Actor)
    
    输入: 状态向量
    输出: 各动作的 Q 值
    
    @note 与 DDPG 的 PolicyNetwork 相同
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(TD3PolicyNetwork, self).__init__()

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
        return self.network(x)


class TD3QNetwork(nn.Module):
    """
    @brief Q 网络 (Critic)
    
    输入: 状态向量
    输出: 各动作的 Q 值
    
    @note TD3 使用两个独立的 Q 网络
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(TD3QNetwork, self).__init__()

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
        return self.network(x)


class TD3Noise:
    """
    @brief 目标策略平滑噪声
    
    用于 TD3 的 Target Policy Smoothing。
    使用较小的噪声来平滑目标策略。
    """
    def __init__(self, size: int, sigma: float = 0.2):
        """
        @brief 构造函数
        
        @param size: 噪声维度
        @param sigma: 噪声标准差
        """
        self.size = size
        self.sigma = sigma

    def sample(self) -> np.ndarray:
        """@brief 采样噪声"""
        return np.random.randn(self.size) * self.sigma


class TD3Agent:
    """
    @brief TD3 智能体类
    
    Twin Delayed DDPG:
    - Twin Q-Networks: 减少 Q 值过估计
    - Delayed Policy Updates: 策略延迟更新
    - Target Policy Smoothing: 目标策略平滑
    
    @note 是 DDPG 的改进版本，性能更好
    
    @example
        config = DQNConfig()
        agent = TD3Agent(config)
        
        action_idx = agent.select_action(state_tensor)
        agent.store_transition(transition)
        agent.train()
    """
    __slots__ = ('device_v', 'policy_v', 'target_policy_v', 
                 'q1_network_v', 'q2_network_v',
                 'target_q1_v', 'target_q2_v',
                 'optimizer_policy', 'optimizer_q',
                 'memory_v', 'config_v', 'training_step_v', 'noise',
                 'epsilon_v', 'gamma_v', 'tau_v',
                 'policy_delay_v', 'policy_noise_sigma')

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
        print(f"[TD3Agent] Using device: {self.device_v}")

        self.training_step_v = 0
        
        # === TD3 超参数 ===
        self.gamma_v = config.gamma_v      # 折扣因子
        self.tau_v = 0.005                 # Soft update 系数
        self.epsilon_v = config.epsilon_start_v  # 探索率
        self.policy_delay_v = 2           # 策略更新延迟 (每隔2步更新一次)
        self.policy_noise_sigma = 0.2     # 目标策略噪声标准差

        state_dim = config.state_dim_v
        action_dim = config.action_dim_v

        # === 创建网络 ===
        # Actor (Policy)
        self.policy_v = TD3PolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_policy_v = TD3PolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_policy_v.load_state_dict(self.policy_v.state_dict())
        self.target_policy_v.eval()
        
        # Twin Critics (两个 Q 网络)
        self.q1_network_v = TD3QNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.q2_network_v = TD3QNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        
        # 目标网络
        self.target_q1_v = TD3QNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_q2_v = TD3QNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_q1_v.load_state_dict(self.q1_network_v.state_dict())
        self.target_q2_v.load_state_dict(self.q2_network_v.state_dict())
        self.target_q1_v.eval()
        self.target_q2_v.eval()

        # === 创建优化器 ===
        self.optimizer_policy = optim.Adam(self.policy_v.parameters(), lr=config.learning_rate_v)
        self.optimizer_q = optim.Adam(
            list(self.q1_network_v.parameters()) + list(self.q2_network_v.parameters()),
            lr=config.learning_rate_v * 2
        )

        # === 经验回放缓冲区 ===
        self.memory_v: List = []

        # === 探索噪声 ===
        self.noise = TD3Noise(action_dim, sigma=0.3)

    def select_action(self, state: List[float]) -> int:
        """
        @brief 选择动作
        
        @param state: 状态列表
        @return 选择的动作索引
        
        @note 使用带噪声的贪婪策略
        """
        state_tensor = torch.FloatTensor(state).to(self.device_v)

        with torch.no_grad():
            q_values = self.policy_v(state_tensor)
            
            # 添加噪声进行探索
            noise = self.noise.sample() * self.epsilon_v
            noise_tensor = torch.FloatTensor(noise).to(self.device_v)
            q_values = q_values + noise_tensor
            
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
        @brief 训练 TD3
        
        @note TD3 训练步骤:
        1. 采样 batch
        2. 计算目标 Q 值 (Twin Q, 取最小 + 策略平滑噪声)
        3. 更新 Q 网络 (每步)
        4. 延迟更新策略网络 (每隔 policy_delay 步)
        5. 更新目标网络
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

        # === 计算目标 Q 值 ===
        with torch.no_grad():
            # 目标策略 + 噪声 (Target Policy Smoothing)
            target_q_values = self.target_policy_v(batch_next_state)
            
            # 添加小噪声到目标动作
            noise = np.random.randn(*target_q_values.shape) * self.policy_noise_sigma
            noise = np.clip(noise, -0.5, 0.5)  # Clip 噪声范围
            noise_tensor = torch.FloatTensor(noise).to(self.device_v)
            target_q_values = target_q_values + noise_tensor
            
            # 选择最大 Q 值的动作
            target_action = target_q_values.argmax(dim=1)
            
            # Twin Q: 取两个 Q 网络的较小值
            target_q1 = self.target_q1_v(batch_next_state)
            target_q2 = self.target_q2_v(batch_next_state)
            target_q1 = target_q1.gather(1, target_action.unsqueeze(1)).squeeze(1)
            target_q2 = target_q2.gather(1, target_action.unsqueeze(1)).squeeze(1)
            target_q_min = torch.min(target_q1, target_q2)
            
            # 目标 Q 值
            target_q = batch_reward + self.gamma_v * (~batch_terminal) * target_q_min

        # === 更新 Q 网络 ===
        current_q1 = self.q1_network_v(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)
        current_q2 = self.q2_network_v(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)

        q1_loss = nn.MSELoss()(current_q1, target_q)
        q2_loss = nn.MSELoss()(current_q2, target_q)
        q_loss = q1_loss + q2_loss

        self.optimizer_q.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q1_network_v.parameters(), 10.0)
        torch.nn.utils.clip_grad_norm_(self.q2_network_v.parameters(), 10.0)
        self.optimizer_q.step()

        # === 延迟更新策略网络 ===
        if self.training_step_v % self.policy_delay_v == 0:
            # 策略损失: 最大化 Q 值
            policy_q = self.policy_v(batch_state)
            policy_action = policy_q.argmax(dim=1)
            policy_q_values = self.q1_network_v(batch_state)
            policy_q = policy_q_values.gather(1, policy_action.unsqueeze(1)).squeeze(1)
            
            policy_loss = -policy_q.mean()

            self.optimizer_policy.zero_grad()
            policy_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy_v.parameters(), 10.0)
            self.optimizer_policy.step()

            # === 更新目标网络 ===
            self._soft_update(self.policy_v, self.target_policy_v)
            self._soft_update(self.q1_network_v, self.target_q1_v)
            self._soft_update(self.q2_network_v, self.target_q2_v)

        self.training_step_v += 1

        # === 衰减探索率 ===
        if self.epsilon_v > self.config_v.epsilon_end_v:
            self.epsilon_v -= (self.config_v.epsilon_start_v - self.config_v.epsilon_end_v) / self.config_v.epsilon_decay_steps_v

    def _soft_update(self, source: nn.Module, target: nn.Module):
        """
        @brief Soft update 目标网络
        
        @param source: 源网络
        @param target: 目标网络
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
            'q1_network': self.q1_network_v.state_dict(),
            'q2_network': self.q2_network_v.state_dict(),
            'target_q1': self.target_q1_v.state_dict(),
            'target_q2': self.target_q2_v.state_dict(),
            'optimizer_policy': self.optimizer_policy.state_dict(),
            'optimizer_q': self.optimizer_q.state_dict(),
            'epsilon': self.epsilon_v,
            'training_step': self.training_step_v,
        }, path)
        print(f"[TD3Agent] Model saved to {path}")

    def load(self, path: str) -> None:
        """
        @brief 加载模型
        
        @param path: 模型文件路径
        """
        checkpoint = torch.load(path, map_location=self.device_v)
        self.policy_v.load_state_dict(checkpoint['policy'])
        self.target_policy_v.load_state_dict(checkpoint['target_policy'])
        self.q1_network_v.load_state_dict(checkpoint['q1_network'])
        self.q2_network_v.load_state_dict(checkpoint['q2_network'])
        self.target_q1_v.load_state_dict(checkpoint['target_q1'])
        self.target_q2_v.load_state_dict(checkpoint['target_q2'])
        self.optimizer_policy.load_state_dict(checkpoint['optimizer_policy'])
        self.optimizer_q.load_state_dict(checkpoint['optimizer_q'])
        self.epsilon_v = checkpoint['epsilon']
        self.training_step_v = checkpoint['training_step']
        print(f"[TD3Agent] Model loaded from {path}")
