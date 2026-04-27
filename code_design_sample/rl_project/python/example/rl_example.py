# -*- coding: utf-8 -*-
"""
@file rl_example.py
@brief 强化学习示例 - DQN 智能体训练网格世界
@note 位于 rl_project/python/example/ 目录下

本模块提供完整训练和测试流程的示例代码。

## 使用方法

### 训练模式
    python3 rl_example.py
    -> 选择 1
    -> 运行200个episodes的训练

### 测试模式
    python3 rl_example.py
    -> 选择 2
    -> 运行5个episodes的测试 (epsilon=0, 完全利用策略)

## 训练流程

1. 初始化环境 (GameEnv) 和智能体 (DQNAgent)
2. For each episode:
   a. env.reset() - 重置环境
   b. For each step (最多500步):
      - agent.select_action(state) - 选择动作
      - env.step(action) - 执行动作, 获取奖励和新状态
      - agent.store_transition() - 存储经验
      - agent.train() - 训练更新
      - 如果terminal, break
3. 定期输出训练统计信息

## 关键参数说明

### 环境参数
- grid size: 64x64
- obstacle_prob: 0.05 (边界生成障碍物的概率)
- obstacle_freq: 20 (每20步重新生成边缘障碍物)
- food_count: 20 (食物数量)

### 智能体参数
- learning_rate: 0.001 (权重更新学习率)
- gamma: 0.99 (折扣因子)
- epsilon_start: 1.0 (初始探索率)
- epsilon_end: 0.01 (最终探索率)
- epsilon_decay: 5000 (衰减步数)
- batch_size: 32 (采样batch大小)
- memory_capacity: 10000 (经验池容量)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.types import EnvConfig, DQNConfig, Transition
from Environment.GameEnv import GameEnv
from Environment.Action import Action
from Agents.DQNAgent import DQNAgent


def print_step(episode: int, step: int, agent_pos, reward: float, epsilon: float) -> None:
    """
    @brief 打印单个步骤的信息
    
    @param episode: 当前episode编号
    @param step: 当前step编号
    @param agent_pos: 智能体位置 (Position对象)
    @param reward: 当前步骤获得的奖励
    @param epsilon: 当前探索率
    """
    print(f"Ep {episode:4d} | Step {step:4d} | Agent ({agent_pos.row_v:2d},{agent_pos.col_v:2d}) | "
          f"Reward {reward:5.1f} | Epsilon {epsilon:.4f}")


def train(num_episodes: int) -> None:
    """
    @brief 训练DQN智能体
    
    @param num_episodes: 训练的总episode数量
    
    训练过程中会:
    - 每10个episode输出一次平均奖励
    - 每50个episode渲染一次环境状态
    - 训练结束后输出总平均奖励
    """
    print("=" * 40, flush=True)
    print("       DQN Training - Grid World", flush=True)
    print("=" * 40, flush=True)

    # 创建环境配置
    config = EnvConfig(
        height=64,
        width=64,
        obstacle_prob=0.05,
        obstacle_freq=20,
        food_count=20
    )

    # 创建智能体配置
    agent_config = DQNConfig()
    agent_config.state_dim_v = 6 * 33 * 33   # 6534
    agent_config.action_dim_v = 9             # 9个动作
    agent_config.learning_rate_v = 0.001     # 学习率
    agent_config.gamma_v = 0.99              # 折扣因子
    agent_config.epsilon_start_v = 1.0       # 初始探索率
    agent_config.epsilon_end_v = 0.01         # 最终探索率
    agent_config.epsilon_decay_steps_v = 5000  # 衰减步数
    agent_config.batch_size_v = 32           # batch大小
    agent_config.memory_capacity_v = 10000   # 经验池容量

    # 创建环境和智能体实例
    env = GameEnv(config)
    agent = DQNAgent(agent_config)

    # 记录每个episode的总奖励
    episode_rewards = []

    # 主训练循环
    for ep in range(num_episodes):
        # 重置环境, 获取初始状态
        env.reset()

        state = env.current_state()
        step = 0
        total_reward = 0.0

        # Episode内循环 (最多500步)
        while step < 500:
            # 获取当前状态tensor
            state_tensor = state.tensor()

            # 智能体选择动作
            action_idx = agent.select_action(state_tensor)

            # 环境执行动作
            step_result = env.step(Action(action_idx))

            # 如果episode结束 (撞障碍物/出界), 跳出
            if step_result.terminal_v:
                break

            # 创建transition经验
            trans = Transition()
            trans.state_v = list(state_tensor)                    # 当前状态
            trans.action_v = action_idx                           # 采取的动作
            trans.reward_v = step_result.reward_v                 # 获得的奖励
            trans.next_state_v = list(env.current_state().tensor()) # 下一状态
            trans.terminal_v = step_result.terminal_v             # 是否终止

            # 存储经验并训练
            agent.store_transition(trans)
            agent.train()

            # 更新状态和累计奖励
            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

        # 记录本episode总奖励
        episode_rewards.append(total_reward)

        # 每10个episode输出统计
        if (ep + 1) % 10 == 0:
            avg_reward = sum(episode_rewards[-10:]) / 10.0
            print(f"Episode {(ep + 1):5d} | Avg Reward (last 10): {avg_reward:8.2f} | "
                  f"Epsilon: {agent.get_epsilon():.4f} | Memory: {agent.memory_size()}")

        # 每50个episode渲染环境
        if (ep + 1) % 50 == 0:
            env.render()

    # 训练结束
    print("\n" + "=" * 40)
    print("       Training Complete!")
    print("=" * 40)

    # 输出平均奖励
    total = sum(episode_rewards)
    print(f"Average reward: {total / len(episode_rewards):.2f}")


def test(num_episodes: int) -> None:
    """
    @brief 测试训练好的智能体
    
    @param num_episodes: 测试的episode数量
    
    测试时:
    - epsilon设为0, 完全利用学到的策略
    - 打印每个step的详细信息
    - 输出每个episode的总奖励
    """
    print("=" * 40)
    print("       DQN Testing - Grid World")
    print("=" * 40)

    # 创建配置 (与训练相同)
    config = EnvConfig(
        height=64,
        width=64,
        obstacle_prob=0.05,
        obstacle_freq=20,
        food_count=20
    )

    agent_config = DQNConfig()
    agent_config.state_dim_v = 6 * 33 * 33
    agent_config.action_dim_v = 9

    # 创建环境和智能体
    env = GameEnv(config)
    agent = DQNAgent(agent_config)

    # 完全利用模式 (无探索)
    agent.set_epsilon(0.0)

    # 测试循环
    for ep in range(num_episodes):
        env.reset()

        state = env.current_state()
        step = 0
        total_reward = 0.0

        print(f"\nEpisode {ep + 1}:")

        while step < 500:
            state_tensor = state.tensor()
            action_idx = agent.select_action(state_tensor)

            step_result = env.step(Action(action_idx))

            # 打印每步信息
            print_step(ep + 1, step + 1, env.agent_pos(), step_result.reward_v, 0.0)

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

            if step_result.terminal_v:
                break

        print(f"Total reward: {total_reward}")


if __name__ == "__main__":
    """
    @brief 主入口
    
    提供交互式选择:
    - 1: 训练模式 (200 episodes)
    - 2: 测试模式 (5 episodes)
    """
    print("Select mode:")
    print("1. Train (200 episodes)")
    print("2. Test (5 episodes)")
    print("Enter choice (1/2): ", end="")

    choice = input().strip()
    if choice == "1":
        train(200)
    else:
        test(5)