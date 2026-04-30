# -*- coding: utf-8 -*-
"""
@file DQNAgent.py
@brief DQN 智能体实现 (PyTorch神经网络版本)
@note 位于 rl_project/Agents/ 目录下

基于深度神经网络的DQN (Deep Q-Network) 实现，使用PyTorch进行GPU加速。

## DQN 算法原理

DQN 通过神经网络逼近Q值函数 Q(s, a) -> 表示在状态s下执行动作a的预期累积奖励。

### 核心组件
1. **Q-Network**: 输入状态, 输出各动作的Q值
2. **Target Network**: 用于计算目标Q值, 避免训练不稳定
3. **Experience Replay**: 存储经验, 打破样本相关性
4. **Epsilon-Greedy**: 平衡探索与利用

### 更新公式
- Q(s, a) <- Q(s, a) + α * (r + γ * max_a' Q_target(s', a') - Q(s, a))
- 目标Q值: r + γ * max_a' Q_target(s', a') (非终止状态)
- 目标Q值: r (终止状态, 没有未来奖励)

## 神经网络结构

输入: 状态向量 [6534] = 6 * 33 * 33
  -> Linear(6534, 256) + ReLU
  -> Linear(256, 128) + ReLU
  -> Linear(128, 64) + ReLU
  -> Linear(64, 9)           # 输出9个动作的Q值
"""

import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List
from Utils.types import DQNConfig, Transition


class QNetwork(nn.Module):
    """
    @brief Q值网络 - 深度神经网络
    
    输入: 状态向量 (state_dim,)
    输出: 各动作的Q值 (action_dim,)
    
    结构: [state_dim] -> [256] -> [128] -> [64] -> [action_dim]
    
    @note 使用全连接层 (Linear) 而非卷积层, 因为输入已经是展平的状态向量
    @note ReLU 作为激活函数, 提供非线性
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = None):
        """
        @brief 构造函数
        
        @param state_dim: 状态维度 (默认6534)
        @param action_dim: 动作维度 (默认9)
        @param hidden_dims: 隐藏层维度列表, 默认[256, 128, 64]
        """
        super(QNetwork, self).__init__()
        
        # 默认隐藏层维度
        if hidden_dims is None:
            hidden_dims = [256, 128, 64]
        
        # 构建网络层
        layers = []
        prev_dim = state_dim  # 输入维度
        
        # 循环创建隐藏层
        for hidden_dim in hidden_dims:
            layers.extend([
                # 全连接层: prev_dim -> hidden_dim
                nn.Linear(prev_dim, hidden_dim),
                # ReLU激活函数: max(0, x)
                nn.ReLU(),
            ])
            prev_dim = hidden_dim  # 更新输入维度
        
        # 输出层: 最后一个隐藏层 -> action_dim (Q值)
        layers.append(nn.Linear(prev_dim, action_dim))
        
        # 使用Sequential容器包装所有层
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        @brief 前向传播
        
        @param x: 输入状态tensor [batch_size, state_dim]
        @return 各动作的Q值 [batch_size, action_dim]
        
        @note 每个动作对应一个Q值, Q值越大表示该动作越好
        """
        return self.network(x)


class DQNAgent:
    """
    @brief DQN智能体类 - 基于深度神经网络的强化学习
    
    使用PyTorch实现的神经网络进行Q值逼近:
    - 双网络结构 (主网络 + 目标网络)
    - Experience Replay 经验回放
    - Epsilon-Greedy探索策略
    
    @note device_v: 计算设备 (cuda/cpu)
    @note q_network_v: 主Q网络 (用于选择动作和更新)
    @note target_network_v: 目标Q网络 (用于计算目标Q值)
    @note optimizer_v: 优化器 (Adam)
    @note memory_v: 经验回放缓冲区
    @note training_step_v: 训练步数计数
    @note epsilon_v: 当前探索率
    
    @example
        # 创建智能体
        config = DQNConfig()
        agent = DQNAgent(config)
        
        # 选择动作
        state_tensor = state.tensor()  # 获取状态
        action_idx = agent.select_action(state_tensor)  # 选择动作
        
        # 存储经验
        agent.store_transition(transition)
        
        # 训练
        agent.train()
    """
    # __slots__ 限制此类只能有这些属性, 减少内存占用
    __slots__ = ('device_v', 'q_network_v', 'target_network_v', 'optimizer_v',
                 'memory_v', 'training_step_v', 'epsilon_v', 'config_v')

    def __init__(self, config: DQNConfig = None):
        """
        @brief 构造函数
        
        @param config: DQNConfig配置对象, 如果为None则使用默认配置
        
        @note 自动检测CUDA, 如果可用则使用GPU
        """
        # 如果没有提供配置, 使用默认配置
        if config is None:
            config = DQNConfig()
        self.config_v: DQNConfig = config
        
        # === 设置计算设备 ===
        # 优先使用CUDA GPU, 如果不可用则使用CPU
        self.device_v = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[DQNAgent] Using device: {self.device_v}")
        
        # === 创建Q网络 (主网络) ===
        # 这是实际用于选择动作的网络
        self.q_network_v = QNetwork(
            config.state_dim_v,   # 输入维度: 6534
            config.action_dim_v,  # 输出维度: 9 (每个动作的Q值)
            [256, 128, 64]         # 隐藏层维度
        ).to(self.device_v)  # 将模型移动到GPU/CPU
        
        # === 创建目标网络 ===
        # 用于计算目标Q值, 避免训练不稳定
        # 初始权重与主网络相同
        self.target_network_v = QNetwork(
            config.state_dim_v,
            config.action_dim_v,
            [256, 128, 64]
        ).to(self.device_v)
        
        # 从主网络复制权重到目标网络
        self.target_network_v.load_state_dict(self.q_network_v.state_dict())
        
        # 设置为评估模式 (不更新BN等层)
        self.target_network_v.eval()
        
        # === 创建优化器 ===
        # Adam优化器, 学习率从config读取
        self.optimizer_v = optim.Adam(self.q_network_v.parameters(), lr=config.learning_rate_v)
        
        # === 创建经验回放缓冲区 ===
        # 存储(s, a, r, s', terminal)元组
        self.memory_v: List[Transition] = []
        
        # === 训练步数计数器 ===
        self.training_step_v: int = 0
        
        # === 探索率 (Epsilon) ===
        # 用于epsilon-greedy策略: epsilon概率随机选择, 否则选择最大Q值
        self.epsilon_v: float = config.epsilon_start_v

    def select_action(self, state: List[float]) -> int:
        """
        @brief 选择动作
        
        @param state: 状态tensor列表 [6534]
        @return 选择的动作索引 [0, 8]
        
        @note 使用epsilon-greedy策略:
        - 以epsilon概率随机选择 (探索)
        - 以1-epsilon概率选择Q值最大的动作 (利用)
        
        @example
            action_idx = agent.select_action(state_tensor)
        """
        return self._epsilon_greedy(state)

    def _epsilon_greedy(self, state: List[float]) -> int:
        """
        @brief Epsilon-Greedy 动作选择
        
        @param state: 状态列表
        @return 动作索引
        
        @note 策略:
        - 如果随机数 < epsilon: 随机选择 (探索)
        - 否则: 选择Q值最大的动作 (利用)
        """
        # 以epsilon概率随机选择 (探索)
        if random.random() < self.epsilon_v:
            return random.randint(0, self.config_v.action_dim_v - 1)
        
        # 否则选择Q值最大的动作 (利用)
        return self._argmax(state)

    def _argmax(self, state: List[float]) -> int:
        """
        @brief 选择Q值最大的动作
        
        @param state: 状态列表
        @return Q值最大的动作索引
        
        @note 使用贪婪策略, 只选择当前Q值最高的动作
        """
        with torch.no_grad():  # 不需要梯度, 加快推理速度
            # 转换为tensor并移动到设备
            state_tensor = torch.FloatTensor(state).to(self.device_v)
            
            # 前向传播获取Q值
            q_values = self.q_network_v(state_tensor)
            
            # 返回Q值最大值的索引
            return int(q_values.argmax().item())

    def store_transition(self, transition: Transition) -> None:
        """
        @brief 存储经验到回放缓冲区
        
        @param transition: Transition对象, 包含(s, a, r, s', terminal)
        
        @note 经验回放缓冲区有容量限制:
        - 如果超过容量, 丢弃最旧的经验
        - 这保证缓冲区只包含最新的经验
        
        @example
            agent.store_transition(trans)
        """
        # 如果缓冲区已满, 移除最旧的经验 (FIFO)
        if len(self.memory_v) >= self.config_v.memory_capacity_v:
            self.memory_v.pop(0)  # 移除第一个元素
        
        # 添加新经验
        self.memory_v.append(transition)

    def train(self) -> None:
        """
        @brief 训练智能体 (一次梯度更新)
        
        从经验回放缓冲区随机采样, 执行一次梯度更新。
        
        @note 训练步骤:
        1. 检查缓冲区样本数是否足够
        2. 随机采样batch
        3. 计算当前Q值 (from q_network)
        4. 计算目标Q值 (from target_network)
        5. 计算损失 (MSE between current_Q and target_Q)
        6. 反向传播更新 q_network
        7. 定期同步 target_network
        8. 衰减 epsilon
        
        @note 只有当缓冲区样本数 >= batch_size时才训练
        """
        # === 检查样本数是否足够 ===
        if len(self.memory_v) < self.config_v.batch_size_v:
            return

        # === 随机采样batch ===
        # 从经验池随机选择batch_size个样本
        batch = random.sample(self.memory_v, self.config_v.batch_size_v)

        # === 准备batch数据 ===
        # 将Python列表转换为PyTorch张量
        batch_state = torch.FloatTensor([t.state_v for t in batch]).to(self.device_v)
        batch_action = torch.LongTensor([t.action_v for t in batch]).to(self.device_v)
        batch_reward = torch.FloatTensor([t.reward_v for t in batch]).to(self.device_v)
        batch_next_state = torch.FloatTensor([t.next_state_v for t in batch]).to(self.device_v)
        batch_terminal = torch.BoolTensor([t.terminal_v for t in batch]).to(self.device_v)

        # === 计算当前Q值 ===
        # 使用主网络计算当前状态下各动作的Q值
        # gather(1, batch_action) 选取每个样本实际执行的动作对应的Q值
        current_q = self.q_network_v(batch_state).gather(1, batch_action.unsqueeze(1)).squeeze(1)

        # === 计算目标Q值 ===
        with torch.no_grad():  # 目标网络不需要梯度
            # 使用目标网络计算下一个状态各动作的Q值
            next_q_all = self.target_network_v(batch_next_state)
            
            # 取最大Q值 (贪婪策略)
            max_next_q = next_q_all.max(1)[0]
            
            # 如果是终止状态, 目标Q值就是当前奖励 (没有未来奖励)
            # 如果不是终止状态, 目标Q值 = 当前奖励 + 折扣 * 未来最大Q值
            max_next_q = max_next_q.masked_fill(batch_terminal, 0.0)  # 终止状态mask为0
            target_q = batch_reward + self.config_v.gamma_v * max_next_q

        # === 计算损失并更新 ===
        # 使用MSE损失: (current_Q - target_Q)^2
        loss = nn.MSELoss()(current_q, target_q)
        
        # 梯度清零 (避免累积)
        self.optimizer_v.zero_grad()
        
        # 反向传播计算梯度
        loss.backward()
        
        # 梯度裁剪: 防止梯度爆炸
        torch.nn.utils.clip_grad_norm_(self.q_network_v.parameters(), 10.0)
        
        # 更新网络参数
        self.optimizer_v.step()

        # === 定期更新目标网络 ===
        self.training_step_v += 1
        if self.training_step_v % self.config_v.target_update_freq_v == 0:
            # 将主网络的权重复制到目标网络
            self.target_network_v.load_state_dict(self.q_network_v.state_dict())

        # === Epsilon衰减 ===
        # 逐渐减少随机探索, 增加利用已学知识
        if self.epsilon_v > self.config_v.epsilon_end_v:
            decay_step = (self.config_v.epsilon_start_v - self.config_v.epsilon_end_v) / float(self.config_v.epsilon_decay_steps_v)
            self.epsilon_v -= decay_step
            if self.epsilon_v < self.config_v.epsilon_end_v:
                self.epsilon_v = self.config_v.epsilon_end_v

    def get_epsilon(self) -> float:
        """
        @brief 获取当前探索率
        
        @return epsilon值 [0, 1]
        
        @note 用于训练日志显示
        """
        return self.epsilon_v

    def set_epsilon(self, epsilon: float) -> None:
        """
        @brief 设置探索率
        
        @param epsilon: 新的epsilon值
        
        @note 用于评估时设置epsilon=0 (纯利用)
        """
        self.epsilon_v = epsilon

    def memory_size(self) -> int:
        """
        @brief 获取经验缓冲区大小
        
        @return 缓冲区中的经验数量
        """
        return len(self.memory_v)
    
    def save(self, path: str) -> None:
        """
        @brief 保存模型
        
        @param path: 保存路径
        
        @note 保存内容:
        - q_network: 主网络权重
        - target_network: 目标网络权重
        - optimizer: 优化器状态 (可继续训练)
        - epsilon: 当前探索率
        - training_step: 训练步数
        
        @example
            agent.save("dqn_model.pt")
        """
        torch.save({
            'q_network': self.q_network_v.state_dict(),
            'target_network': self.target_network_v.state_dict(),
            'optimizer': self.optimizer_v.state_dict(),
            'epsilon': self.epsilon_v,
            'training_step': self.training_step_v,
        }, path)
        print(f"[DQNAgent] Model saved to {path}")
    
    def load(self, path: str) -> None:
        """
        @brief 加载模型
        
        @param path: 模型文件路径
        
        @note 加载后模型会从保存的状态继续
        @note 需要确保config设置一致 (state_dim, action_dim等)
        
        @example
            agent.load("dqn_model.pt")
        """
        checkpoint = torch.load(path, map_location=self.device_v)
        self.q_network_v.load_state_dict(checkpoint['q_network'])
        self.target_network_v.load_state_dict(checkpoint['target_network'])
        self.optimizer_v.load_state_dict(checkpoint['optimizer'])
        self.epsilon_v = checkpoint['epsilon']
        self.training_step_v = checkpoint['training_step']
        print(f"[DQNAgent] Model loaded from {path}")
