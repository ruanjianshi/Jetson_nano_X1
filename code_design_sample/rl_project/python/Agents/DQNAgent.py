# -*- coding: utf-8 -*-
"""
@file DQNAgent.py
@brief DQN 智能体实现
@note 位于 rl_project/python/Agents/ 目录下

DQN (Deep Q-Network) 智能体的简化实现, 使用线性Q函数逼近而非深度神经网络。

## 算法原理

### Q-Learning 基础
Q-Learning是一种基于值函数的强化学习算法, 核心是Q函数 Q(s, a):
- 表示在状态s下采取动作a的长期价值期望
- 最优Q函数满足Bellman方程: Q(s,a) = r + γ * max_a' Q(s', a')

### 经验回放 (Experience Replay)
- 存储过去的经验 (s, a, r, s', terminal) 到replay buffer
- 训练时随机采样batch, 打破样本间的时间相关性
- 类似于人类"回忆过往经验进行学习"的过程

### 探索策略 (Exploration)
- Epsilon-Greedy: 以ε概率随机探索, 1-ε概率贪心利用
- Epsilon衰减: 随着训练进行, 逐渐减少随机探索, 增加利用

### 简化实现说明
本实现使用线性Q函数逼近 (Q = w · state), 而非深度神经网络:
- Q_table存储每个(state_dim * action_dim)的权重
- 训练时使用梯度下降更新权重
- 适用于状态空间较小的情况

## 核心公式

### Q值计算
对于给定状态state和动作a:
    Q(s, a) = Σ_i (w_i * s_i)

### 权重更新
    w_i := w_i + α * (target_q - Q(s,a)) * s_i

其中:
    target_q = r + γ * max_a' Q(s', a')  (非终止状态)
    target_q = r                        (终止状态)
"""

import random
import numpy as np
from typing import List
from Utils.types import (
    DQNConfig, Transition, K_CHANNEL_COUNT, K_WINDOW_SIZE
)

K_Q_CLIP = 500.0        # Q值裁剪阈值, 防止数值溢出
K_TD_ERROR_CLIP = 10.0  # TD误差裁剪阈值


class DQNAgent:
    """
    @brief DQN智能体类 - 实现深度Q网络学习

    使用线性Q函数逼近实现DQN算法, 包含:
    - 经验回放缓冲区 (Replay Buffer)
    - Epsilon-Greedy探索策略
    - Q-Learning权重更新

    @note config_v: DQN配置参数
    @note q_table_v: Q函数权重 [action_dim * state_dim]
    @note memory_v: 经验回放缓冲区
    @note training_step_v: 训练步数计数
    @note epsilon_v: 当前探索率
    """
    __slots__ = ('config_v', 'memory_v', 'q_table_v', 'training_step_v', 'epsilon_v')

    def __init__(self, config: DQNConfig = None):
        """
        @brief 构造函数

        @param config: DQNConfig配置对象, 如果为None则使用默认配置
        """
        if config is None:
            config = DQNConfig()
        self.config_v: DQNConfig = config

        # 使用NumPy数组存储Q表: action_dim * state_dim 个权重
        self.q_table_v: np.ndarray = np.zeros((config.action_dim_v, config.state_dim_v), dtype=np.float32)

        # 初始化经验回放缓冲区
        self.memory_v: List[Transition] = []

        # 训练步数
        self.training_step_v: int = 0

        # 初始探索率
        self.epsilon_v: float = config.epsilon_start_v

    def select_action(self, state: List[float]) -> int:
        """
        @brief 选择动作

        使用Epsilon-Greedy策略选择动作:
        - 以ε概率随机选择 (探索)
        - 以1-ε概率选择Q值最大的动作 (利用)

        @param state: 当前状态 (List[float], 长度state_dim)
        @return 选中的动作索引 [0, action_dim-1]
        """
        return self._epsilon_greedy(state)

    def _epsilon_greedy(self, state: List[float]) -> int:
        """
        @brief Epsilon-Greedy动作选择

        @param state: 当前状态
        @return 动作索引
        """
        # 探索: 随机选择动作
        if random.random() < self.epsilon_v:
            return random.randint(0, self.config_v.action_dim_v - 1)
        # 利用: 选择Q值最大的动作
        return self._argmax(state)

    def _argmax(self, state: List[float]) -> int:
        """
        @brief 选择Q值最大的动作

        计算所有动作的Q值, 返回最大Q值对应的动作索引.
        如果多个动作Q值相同, 返回第一个.

        @param state: 当前状态
        @return Q值最大的动作索引
        """
        # 使用NumPy进行批量矩阵乘法加速
        state_np = np.array(state, dtype=np.float32)
        q_values = np.dot(self.q_table_v, state_np)  # shape: (action_dim,)
        return int(np.argmax(q_values))

    def store_transition(self, transition: Transition) -> None:
        """
        @brief 存储转换经验到回放缓冲区

        如果缓冲区已满, 移除最旧的经历.

        @param transition: Transition对象, 包含(s, a, r, s', terminal)
        """
        # 缓冲区满时移除最早的经验 (FIFO)
        if len(self.memory_v) >= self.config_v.memory_capacity_v:
            self.memory_v.pop(0)
        self.memory_v.append(transition)

    def train(self) -> None:
        """
        @brief 训练智能体 (执行一次学习更新)

        从经验回放缓冲区采样batch, 执行Q-Learning更新:
        1. 随机采样batch_size个经验
        2. 对每条经验计算TD目标值 target_q
        3. 对每条经验:
           a. 计算当前Q(s,a)值
           b. 计算TD误差 (target_q - Q(s,a))
           c. 用梯度下降更新对应动作的权重

        @note 只有当缓冲区样本数 >= batch_size时才训练
        """
        # 样本不足时跳过
        if len(self.memory_v) < self.config_v.batch_size_v:
            return

        # 随机采样batch
        batch = random.sample(self.memory_v, self.config_v.batch_size_v)

        # 准备batch数据 (NumPy数组, 形状: [batch, state_dim])
        batch_state = np.array([t.state_v for t in batch], dtype=np.float32)
        batch_action = np.array([t.action_v for t in batch], dtype=np.int32)
        batch_reward = np.array([t.reward_v for t in batch], dtype=np.float32)
        batch_next_state = np.array([t.next_state_v for t in batch], dtype=np.float32)
        batch_terminal = np.array([t.terminal_v for t in batch], dtype=bool)

        # -------------------------------------------------------------------------
        # 步骤1: 计算所有next_state的Q值 (批量计算)
        # -------------------------------------------------------------------------
        # Q(next_state, a) 对所有a, 形状: [batch, action_dim]
        next_q_all = np.dot(batch_next_state, self.q_table_v.T)  # (batch, action_dim)

        # 裁剪Q值防止溢出
        next_q_all = np.clip(next_q_all, -K_Q_CLIP, K_Q_CLIP)

        max_next_q = np.max(next_q_all, axis=1)  # (batch,)

        # -------------------------------------------------------------------------
        # 步骤2: 计算TD目标
        # -------------------------------------------------------------------------
        # target = r + γ * max_a' Q(s', a') (非终止)
        # target = r                       (终止)
        target_q = batch_reward + self.config_v.gamma_v * max_next_q * (~batch_terminal)

        # 裁剪target_q
        target_q = np.clip(target_q, -K_Q_CLIP, K_Q_CLIP)

        # -------------------------------------------------------------------------
        # 步骤3: 计算当前Q(s,a)值 (批量计算)
        # -------------------------------------------------------------------------
        # Q(s, a) 对batch中每个样本
        current_q = np.sum(self.q_table_v[batch_action] * batch_state, axis=1)  # (batch,)

        # -------------------------------------------------------------------------
        # 步骤4: 计算TD误差并进行梯度下降更新
        # -------------------------------------------------------------------------
        # TD误差 = target_q - Q(s,a)
        td_error = target_q - current_q  # (batch,)

        # 裁剪TD误差防止梯度爆炸
        td_error = np.clip(td_error, -K_TD_ERROR_CLIP, K_TD_ERROR_CLIP)

        # 对每个样本更新对应动作的权重
        # w[a] := w[a] + α * TD_error * state
        for i in range(self.config_v.batch_size_v):
            action = batch_action[i]
            self.q_table_v[action] += self.config_v.learning_rate_v * td_error[i] * batch_state[i]

        # 更新训练步数
        self.training_step_v += 1

        # Epsilon衰减
        if self.epsilon_v > self.config_v.epsilon_end_v:
            decay_step = (self.config_v.epsilon_start_v - self.config_v.epsilon_end_v) / float(self.config_v.epsilon_decay_steps_v)
            self.epsilon_v -= decay_step
            if self.epsilon_v < self.config_v.epsilon_end_v:
                self.epsilon_v = self.config_v.epsilon_end_v

    def get_epsilon(self) -> float:
        """@brief 获取当前探索率"""
        return self.epsilon_v

    def set_epsilon(self, epsilon: float) -> None:
        """
        @brief 设置探索率

        @param epsilon: 新的探索率值
        @note 用于测试时将epsilon设为0, 完全利用学到的策略
        """
        self.epsilon_v = epsilon

    def memory_size(self) -> int:
        """@brief 获取当前经验缓冲区大小"""
        return len(self.memory_v)