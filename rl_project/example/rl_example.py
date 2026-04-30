# -*- coding: utf-8 -*-
"""
@file rl_example.py
@brief 强化学习示例 - DQN 智能体训练网格世界
@note 位于 rl_project/python/example/ 目录下

本模块提供完整训练、验证和测试流程的示例代码。

## 使用方法

### 训练模式
    python3 rl_example.py
    -> 选择 1
    -> 运行episodes的训练, 自动保存模型到 dqn_model.pt

### 加载验证模式
    python3 rl_example.py
    -> 选择 2
    -> 从 dqn_model.pt 加载模型, 运行验证

## 文件说明
- dqn_model.pt: 训练好的模型权重文件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.types import EnvConfig, DQNConfig, Transition
from Environment.GameEnv import GameEnv
from Environment.Action import Action
from Agents.DQNAgent import DQNAgent


MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dqn_model.pt")


def get_env_config():
    """获取环境配置"""
    return EnvConfig(
        height=32,
        width=32,
        obstacle_prob=0.03,
        obstacle_freq=999,
        food_count=15
    )


def get_agent_config():
    """获取智能体配置"""
    config = DQNConfig()
    config.state_dim_v = 6 * 33 * 33
    config.action_dim_v = 9
    config.learning_rate_v = 0.001
    config.gamma_v = 0.99
    config.epsilon_start_v = 1.0
    config.epsilon_end_v = 0.01
    config.epsilon_decay_steps_v = 500
    config.batch_size_v = 64
    config.memory_capacity_v = 50000
    config.target_update_freq_v = 100
    return config


def print_step(episode: int, step: int, agent_pos, reward: float, epsilon: float) -> None:
    """打印单个步骤的信息"""
    print(f"Ep {episode:4d} | Step {step:4d} | Agent ({agent_pos.row_v:2d},{agent_pos.col_v:2d}) | "
          f"Reward {reward:5.2f} | Epsilon {epsilon:.4f}", flush=True)


def train(num_episodes: int) -> None:
    """
    @brief 训练DQN智能体并保存模型
    """
    print("=" * 50, flush=True)
    print("       DQN Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = DQNAgent(agent_config)

    episode_rewards = []

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0

        while step < 300:
            state_tensor = state.tensor()
            action_idx = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            if step_result.terminal_v:
                break

            trans = Transition()
            trans.state_v = list(state_tensor)
            trans.action_v = action_idx
            trans.reward_v = step_result.reward_v
            trans.next_state_v = list(env.current_state().tensor())
            trans.terminal_v = step_result.terminal_v

            agent.store_transition(trans)
            agent.train()

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

        episode_rewards.append(total_reward)

        if (ep + 1) % 10 == 0:
            avg_reward = sum(episode_rewards[-10:]) / 10.0
            print(f"Episode {(ep + 1):5d} | Avg Reward: {avg_reward:8.2f} | "
                  f"Epsilon: {agent.get_epsilon():.4f} | Steps: {step}", flush=True)

        if (ep + 1) % 50 == 0:
            env.render()

    print("\n" + "=" * 50)
    print("       Training Complete!")
    print("=" * 50)

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Average reward: {avg:.2f}")

    # 保存模型
    agent.save(MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")


def evaluate(num_episodes: int = 20) -> None:
    """
    @brief 加载模型并验证
    """
    print("=" * 50, flush=True)
    print("       DQN Evaluation - Loading Model", flush=True)
    print("=" * 50, flush=True)

    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model file not found at {MODEL_PATH}")
        print("Please train first (option 1)")
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = DQNAgent(agent_config)

    # 加载模型
    agent.load(MODEL_PATH)
    agent.set_epsilon(0.0)  # 完全利用

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0
        initial_food = len(env.food_pos_list_v)

        while step < 300:
            state_tensor = state.tensor()
            action_idx = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            if step_result.terminal_v:
                break

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

        episode_rewards.append(total_reward)
        episode_steps.append(step)
        food_eaten = initial_food - len(env.food_pos_list_v) + (300 - step) // 100
        food_eaten_list.append(food_eaten if step < 300 else initial_food)

        print(f"Eval Ep {ep+1:3d} | Reward: {total_reward:7.2f} | Steps: {step:3d} | Food Eaten: {food_eaten}", flush=True)

    print("\n" + "=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.2f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Eps:    {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.2f}")
    print(f"Max Reward:      {max(episode_rewards):.2f}")


def test(num_episodes: int) -> None:
    """
    @brief 测试模式 (不使用训练好的模型, 仅测试环境)
    """
    print("=" * 50)
    print("       DQN Testing (Random Agent)")
    print("=" * 50)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = DQNAgent(agent_config)
    agent.set_epsilon(1.0)  # 完全随机

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0

        print(f"\nEpisode {ep + 1}:")

        while step < 300:
            state_tensor = state.tensor()
            action_idx = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            print_step(ep + 1, step + 1, env.agent_pos(), step_result.reward_v, 1.0)

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

            if step_result.terminal_v:
                break

        print(f"Total reward: {total_reward:.2f}")


if __name__ == "__main__":
    print("=" * 50)
    print("  DQN Grid World - PyTorch Neural Network")
    print("=" * 50)
    print("\nSelect mode:")
    print("1. Train (100 episodes) -> saves to dqn_model.pt")
    print("2. Evaluate (20 episodes) -> loads dqn_model.pt")
    print("3. Test (5 episodes, random agent)")
    print("Enter choice (1/2/3): ", end="", flush=True)

    choice = input().strip()

    if choice == "1":
        train(100)
    elif choice == "2":
        evaluate(20)
    elif choice == "3":
        test(5)
    else:
        print("Invalid choice")