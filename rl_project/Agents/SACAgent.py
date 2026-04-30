# -*- coding: utf-8 -*-
"""
@file SACAgent.py
@brief SAC (Soft Actor-Critic) 智能体实现
@note 位于 rl_project/Agents/ 目录下

SAC 是基于最大熵的强化学习算法, 具有自动探索调节能力。

## SAC 算法原理

SAC 使用最大熵强化学习框架, 目标函数包含策略熵:

π* = argmax E[Σ r(s,a)] + α * H(π)

其中 H(π) = -Σ π(a|s) log π(a|s) 是策略熵。

## 核心组件

1. **Soft Q-Network**: 学习软Q值 (包含熵)
   - V(s) = E[Q(s,a)] + α * H(π)

2. **Policy Network**: 学习随机策略 π(a|s)
   - 使用 Squashed Gaussian 或 softmax

3. **温度参数 α**: 自动调节探索
   - 熵作为额外奖励

## 与 PPO 的区别

| 特性 | SAC | PPO |
|------|-----|-----|
| 探索 | 最大熵, 自动调节 | 熵正则化, 手动设置 |
| 更新 | Off-policy | On-policy |
| 目标 | 最大化熵加权回报 | Clipped 目标 |
| 样本效率 | 高 | 低 |

## 离散动作空间适配

对于离散动作空间:
- 使用 softmax 策略
- 熵直接计算: H(π) = -Σ π(a) log π(a)
- 温度 α 可以固定或自动调节
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple
from Utils.types import DQNConfig


class SACPolicyNetwork(nn.Module):
    """
    @brief Policy 网络 (Actor)
    
    输入: 状态向量
    输出: 动作概率分布 (softmax)
    
    @note 离散动作空间使用 softmax 输出
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(SACPolicyNetwork, self).__init__()

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
        """@brief 输出各动作的 logit (未归一化的概率)"""
        return self.network(x)

    def get_probs(self, x: torch.Tensor) -> torch.Tensor:
        """@brief 获取动作概率分布"""
        logits = self.network(x)
        return torch.softmax(logits, dim=-1)

    def get_log_probs(self, x: torch.Tensor) -> torch.Tensor:
        """@brief 获取动作的对数概率"""
        logits = self.network(x)
        return torch.log_softmax(logits, dim=-1)


class SACQNetwork(nn.Module):
    """
    @brief Q 网络 (Critic)
    
    输入: 状态向量
    输出: 各动作的 Q 值
    
    @note SAC 使用两个 Q 网络 (Twin Q) 来减少 Q 值过估计
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        super(SACQNetwork, self).__init__()

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
        """@brief 输出各动作的 Q 值"""
        return self.network(x)


class SACAgent:
    """
    @brief SAC 智能体类
    
    Soft Actor-Critic (最大熵强化学习):
    - 使用随机策略 π(a|s)
    - 自动调节探索 (熵作为奖励)
    - Off-policy 学习 (样本效率高)
    
    @note 适配离散动作空间
    
    @example
        config = DQNConfig()
        agent = SACAgent(config)
        
        action_idx = agent.select_action(state_tensor)
        agent.store_transition(transition)
        agent.train()
    """
    __slots__ = ('device_v', 'policy_v', 'q1_network_v', 'q2_network_v',
                 'target_q1_v', 'target_q2_v', 'optimizer_policy', 'optimizer_q',
                 'memory_v', 'config_v', 'training_step_v', 
                 'log_alpha', 'optimizer_alpha',
                 'target_entropy', 'gamma_v')

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
        print(f"[SACAgent] Using device: {self.device_v}")

        self.training_step_v = 0
        
        # === SAC 超参数 ===
        self.gamma_v = config.gamma_v  # 折扣因子
        
        state_dim = config.state_dim_v
        action_dim = config.action_dim_v

        # === 创建网络 ===
        # Policy (Actor)
        self.policy_v = SACPolicyNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        
        # Twin Q-Networks (Critic) - 使用两个 Q 网络减少过估计
        self.q1_network_v = SACQNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.q2_network_v = SACQNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        
        # 目标 Q 网络
        self.target_q1_v = SACQNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
        self.target_q2_v = SACQNetwork(state_dim, action_dim, [256, 128, 64]).to(self.device_v)
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

        # === 熵温度参数 α ===
        # log_alpha 用于自动调节熵权重
        # 初始温度 0.1, 鼓励前期探索
        self.log_alpha = torch.tensor(np.log(0.1), requires_grad=True, device=self.device_v)
        self.optimizer_alpha = optim.Adam([self.log_alpha], lr=config.learning_rate_v * 0.1)
        
        # 目标熵: 离散动作空间的合理值
        # 对于 9 个动作, 目标熵约为 log(9) ≈ 2.2
        self.target_entropy = -np.log(1.0 / action_dim) * 0.98

        # === 经验回放缓冲区 ===
        self.memory_v: List = []

    def select_action(self, state: List[float], deterministic: bool = False) -> Tuple[int, float]:
        """
        @brief 选择动作
        
        @param state: 状态列表
        @param deterministic: 是否使用确定性策略 (用于评估)
        @return (action_idx, action_prob)
        
        @note 评估时使用 deterministic=True
        """
        state_tensor = torch.FloatTensor(state).to(self.device_v)

        with torch.no_grad():
            probs = self.policy_v.get_probs(state_tensor)
            
            if deterministic:
                # 贪婪选择
                action = int(probs.argmax().item())
            else:
                # 随机采样
                action = random.choices(range(len(probs)), weights=probs.cpu().numpy(), k=1)[0]
            
            prob = probs[action].item()

        return action, prob

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
        @brief 训练 SAC
        
        @note 训练步骤:
        1. 采样 batch
        2. 计算目标 Q 值 (使用目标网络和熵)
        3. 更新 Q 网络
        4. 更新策略网络
        5. 更新温度参数 α
        6. 定期更新目标网络
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

        # === 获取当前策略 ===
        probs = self.policy_v.get_probs(batch_state)
        log_probs = self.policy_v.get_log_probs(batch_state)
        
        # 熵: -Σ π(a) log π(a)
        entropy = -(probs * log_probs).sum(dim=1)
        
        # 当前温度
        alpha = self.log_alpha.exp()

        # === 更新 Q 网络 ===
        with torch.no_grad():
            # 下一状态的目标 Q 值
            next_probs = self.policy_v.get_probs(batch_next_state)
            next_log_probs = self.policy_v.get_log_probs(batch_next_state)
            next_entropy = -(next_probs * next_log_probs).sum(dim=1)
            
            # 使用较小的 Q 值作为目标 (减少过估计)
            next_q1 = self.target_q1_v(batch_next_state)
            next_q2 = self.target_q2_v(batch_next_state)
            next_q = torch.min(next_q1, next_q2)
            
            # 目标: r + γ * (Q - α * H)
            next_target = batch_reward + self.gamma_v * (~batch_terminal) * (next_q - alpha * next_entropy)

        # 当前 Q 值
        current_q1 = self.q1_network_v(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)
        current_q2 = self.q2_network_v(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)

        # Q 损失
        q1_loss = nn.MSELoss()(current_q1, next_target)
        q2_loss = nn.MSELoss()(current_q2, next_target)
        q_loss = q1_loss + q2_loss

        self.optimizer_q.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q1_network_v.parameters(), 10.0)
        torch.nn.utils.clip_grad_norm_(self.q2_network_v.parameters(), 10.0)
        self.optimizer_q.step()

        # === 更新策略网络 ===
        # 策略损失: -E[Q(s,a) - α * log π(a|s)]
        # 等价于最大化 E[α * log π(a|s) - Q(s,a)]
        # 为了更好的梯度, 使用 reparameterization trick 的离散版本
        
        policy_q = torch.min(
            self.q1_network_v(batch_state),
            self.q2_network_v(batch_state)
        )
        
        # 策略损失: -Σ π(a|s) * (Q(s,a) - α * log π(a|s))
        policy_loss = (probs * (alpha * log_probs - policy_q)).sum(dim=1).mean()

        self.optimizer_policy.zero_grad()
        policy_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_v.parameters(), 10.0)
        self.optimizer_policy.step()

        # === 更新温度参数 α ===
        # 目标: 保持熵在 target_entropy 附近
        alpha_loss = -(self.log_alpha * (entropy.detach() + self.target_entropy)).mean()

        self.optimizer_alpha.zero_grad()
        alpha_loss.backward()
        self.optimizer_alpha.step()

        # === 更新目标网络 ===
        if self.training_step_v % self.config_v.target_update_freq_v == 0:
            self._update_target_network(self.q1_network_v, self.target_q1_v)
            self._update_target_network(self.q2_network_v, self.target_q2_v)

        self.training_step_v += 1

    def _update_target_network(self, source: nn.Module, target: nn.Module):
        """
        @brief 更新目标网络 (Polyak 平均)
        
        @param source: 源网络
        @param target: 目标网络
        """
        tau = 0.005  # Polyak 系数
        for target_param, source_param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                tau * source_param.data + (1.0 - tau) * target_param.data
            )

    def get_epsilon(self) -> float:
        """@brief SAC 不使用 epsilon, 返回 0"""
        return 0.0

    def set_epsilon(self, epsilon: float) -> None:
        """@brief SAC 不使用 epsilon"""
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
            'q1_network': self.q1_network_v.state_dict(),
            'q2_network': self.q2_network_v.state_dict(),
            'target_q1': self.target_q1_v.state_dict(),
            'target_q2': self.target_q2_v.state_dict(),
            'optimizer_policy': self.optimizer_policy.state_dict(),
            'optimizer_q': self.optimizer_q.state_dict(),
            'log_alpha': self.log_alpha,
            'optimizer_alpha': self.optimizer_alpha.state_dict(),
            'training_step': self.training_step_v,
        }, path)
        print(f"[SACAgent] Model saved to {path}")

    def load(self, path: str) -> None:
        """
        @brief 加载模型
        
        @param path: 模型文件路径
        """
        checkpoint = torch.load(path, map_location=self.device_v)
        self.policy_v.load_state_dict(checkpoint['policy'])
        self.q1_network_v.load_state_dict(checkpoint['q1_network'])
        self.q2_network_v.load_state_dict(checkpoint['q2_network'])
        self.target_q1_v.load_state_dict(checkpoint['target_q1'])
        self.target_q2_v.load_state_dict(checkpoint['target_q2'])
        self.optimizer_policy.load_state_dict(checkpoint['optimizer_policy'])
        self.optimizer_q.load_state_dict(checkpoint['optimizer_q'])
        self.log_alpha = checkpoint['log_alpha']
        self.optimizer_alpha.load_state_dict(checkpoint['optimizer_alpha'])
        self.training_step_v = checkpoint['training_step']
        print(f"[SACAgent] Model loaded from {path}")
