# -*- coding: utf-8 -*-
"""
@file train.py
@brief 强化学习训练脚本
@note 位于 rl_project/train-eval/ 目录下

支持 DQN, PPO, A2C, DDPG, SAC, TD3 六种智能体的训练

使用方法:
    # DQN 训练
    python3 train.py --agent dqn
    python3 train.py --agent dqn -e 200
    
    # PPO 训练
    python3 train.py --agent ppo -e 200
    
    # A2C 训练
    python3 train.py --agent a2c -e 200
    
    # DDPG 训练
    python3 train.py --agent ddpg -e 200
    
    # SAC 训练
    python3 train.py --agent sac -e 200
    
    # TD3 训练
    python3 train.py --agent td3 -e 200
"""

import sys
import os

# === 添加项目根目录到Python路径 ===
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.types import EnvConfig, DQNConfig, Transition
from Environment.GameEnv import GameEnv
from Environment.Action import Action


def get_model_path(episodes: int, agent_type: str) -> str:
    """
    @brief 获取模型保存路径
    
    @param episodes: 训练回合数
    @param agent_type: 智能体类型
    @return 模型保存的完整路径
    """
    filename = f"{agent_type}_model_{episodes}ep.pt"
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def get_env_config():
    """
    @brief 获取环境配置
    
    @return EnvConfig对象
    """
    return EnvConfig(
        height=32,
        width=32,
        obstacle_prob=0.03,
        obstacle_freq=999,
        food_count=15
    )


def get_agent_config():
    """
    @brief 获取智能体配置
    
    @return DQNConfig对象
    """
    config = DQNConfig()
    config.state_dim_v = 6 * 33 * 33
    config.action_dim_v = 9
    config.learning_rate_v = 0.0003
    config.gamma_v = 0.99
    config.epsilon_start_v = 0.1
    config.epsilon_end_v = 0.01
    config.epsilon_decay_steps_v = 2000
    config.batch_size_v = 64
    config.memory_capacity_v = 50000
    config.target_update_freq_v = 100
    return config


def train_dqn(num_episodes: int) -> None:
    """@brief 训练 DQN 智能体"""
    from Agents.DQNAgent import DQNAgent
    
    print("=" * 50, flush=True)
    print("       DQN Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)
    print(f"Device: CUDA" if __import__('torch').cuda.is_available() else "Device: CPU", flush=True)
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
    print(f"Agent: DQN")

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Total Episodes:  {num_episodes}")
    print(f"Average Reward:  {avg:.2f}")
    print(f"Best Episode:    {max(episode_rewards):.2f}")
    print(f"Worst Episode:  {min(episode_rewards):.2f}")

    model_path = get_model_path(num_episodes, "dqn")
    agent.save(model_path)
    print(f"\nModel saved to: {model_path}")


def train_ppo(num_episodes: int) -> None:
    """@brief 训练 PPO 智能体"""
    from Agents.PPOAgent import PPOAgent
    
    print("=" * 50, flush=True)
    print("       PPO Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)
    print(f"Device: CUDA" if __import__('torch').cuda.is_available() else "Device: CPU", flush=True)
    print("=" * 50, flush=True)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = PPOAgent(agent_config)

    episode_rewards = []

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0

        while step < 300:
            state_tensor = state.tensor()
            action_idx, action_prob = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            agent.store_transition(
                list(state_tensor),
                action_idx,
                step_result.reward_v,
                step_result.terminal_v,
                action_prob
            )

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

            if step_result.terminal_v:
                break

        agent.train()
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
    print(f"Agent: PPO")

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Total Episodes:  {num_episodes}")
    print(f"Average Reward:  {avg:.2f}")
    print(f"Best Episode:    {max(episode_rewards):.2f}")
    print(f"Worst Episode:  {min(episode_rewards):.2f}")

    model_path = get_model_path(num_episodes, "ppo")
    agent.save(model_path)
    print(f"\nModel saved to: {model_path}")


def train_a2c(num_episodes: int) -> None:
    """@brief 训练 A2C 智能体"""
    from Agents.A2CAgent import A2CAgent
    
    print("=" * 50, flush=True)
    print("       A2C Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)
    print(f"Device: CUDA" if __import__('torch').cuda.is_available() else "Device: CPU", flush=True)
    print("=" * 50, flush=True)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = A2CAgent(agent_config)

    episode_rewards = []

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0

        while step < 300:
            state_tensor = state.tensor()
            action_idx, _ = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            agent.store_transition(
                list(state_tensor),
                action_idx,
                step_result.reward_v,
                step_result.terminal_v
            )

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

            if step_result.terminal_v:
                break

        agent.train()
        episode_rewards.append(total_reward)

        if (ep + 1) % 10 == 0:
            avg_reward = sum(episode_rewards[-10:]) / 10.0
            print(f"Episode {(ep + 1):5d} | Avg Reward: {avg_reward:8.2f} | Steps: {step}", flush=True)

        if (ep + 1) % 50 == 0:
            env.render()

    print("\n" + "=" * 50)
    print("       Training Complete!")
    print("=" * 50)
    print(f"Agent: A2C")

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Total Episodes:  {num_episodes}")
    print(f"Average Reward:  {avg:.2f}")
    print(f"Best Episode:    {max(episode_rewards):.2f}")
    print(f"Worst Episode:  {min(episode_rewards):.2f}")

    model_path = get_model_path(num_episodes, "a2c")
    agent.save(model_path)
    print(f"\nModel saved to: {model_path}")


def train_ddpg(num_episodes: int) -> None:
    """@brief 训练 DDPG 智能体"""
    from Agents.DDPGAgent import DDPGAgent
    
    print("=" * 50, flush=True)
    print("       DDPG Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)
    print(f"Device: CUDA" if __import__('torch').cuda.is_available() else "Device: CPU", flush=True)
    print("=" * 50, flush=True)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = DDPGAgent(agent_config)

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
    print(f"Agent: DDPG")

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Total Episodes:  {num_episodes}")
    print(f"Average Reward:  {avg:.2f}")
    print(f"Best Episode:    {max(episode_rewards):.2f}")
    print(f"Worst Episode:  {min(episode_rewards):.2f}")

    model_path = get_model_path(num_episodes, "ddpg")
    agent.save(model_path)
    print(f"\nModel saved to: {model_path}")


def train_sac(num_episodes: int) -> None:
    """@brief 训练 SAC 智能体"""
    from Agents.SACAgent import SACAgent
    
    print("=" * 50, flush=True)
    print("       SAC Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)
    print(f"Device: CUDA" if __import__('torch').cuda.is_available() else "Device: CPU", flush=True)
    print("=" * 50, flush=True)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = SACAgent(agent_config)

    episode_rewards = []

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0

        while step < 300:
            state_tensor = state.tensor()
            action_idx, _ = agent.select_action(state_tensor)
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
            print(f"Episode {(ep + 1):5d} | Avg Reward: {avg_reward:8.2f} | Steps: {step}", flush=True)

        if (ep + 1) % 50 == 0:
            env.render()

    print("\n" + "=" * 50)
    print("       Training Complete!")
    print("=" * 50)
    print(f"Agent: SAC")

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Total Episodes:  {num_episodes}")
    print(f"Average Reward:  {avg:.2f}")
    print(f"Best Episode:    {max(episode_rewards):.2f}")
    print(f"Worst Episode:  {min(episode_rewards):.2f}")

    model_path = get_model_path(num_episodes, "sac")
    agent.save(model_path)
    print(f"\nModel saved to: {model_path}")


def train_td3(num_episodes: int) -> None:
    """@brief 训练 TD3 智能体"""
    from Agents.TD3Agent import TD3Agent
    
    print("=" * 50, flush=True)
    print("       TD3 Training - Grid World (PyTorch)", flush=True)
    print("=" * 50, flush=True)
    print(f"Device: CUDA" if __import__('torch').cuda.is_available() else "Device: CPU", flush=True)
    print("=" * 50, flush=True)

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = TD3Agent(agent_config)

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
    print(f"Agent: TD3")

    avg = sum(episode_rewards) / len(episode_rewards)
    print(f"Total Episodes:  {num_episodes}")
    print(f"Average Reward:  {avg:.2f}")
    print(f"Best Episode:    {max(episode_rewards):.2f}")
    print(f"Worst Episode:  {min(episode_rewards):.2f}")

    model_path = get_model_path(num_episodes, "td3")
    agent.save(model_path)
    print(f"\nModel saved to: {model_path}")


def train(num_episodes: int = 100, agent_type: str = "dqn") -> None:
    """
    @brief 训练智能体
    
    @param num_episodes: 训练的总 episode 数量
    @param agent_type: 智能体类型 ("dqn", "ppo", "a2c", "ddpg", "sac", "td3")
    """
    if agent_type.lower() == "dqn":
        train_dqn(num_episodes)
    elif agent_type.lower() == "ppo":
        train_ppo(num_episodes)
    elif agent_type.lower() == "a2c":
        train_a2c(num_episodes)
    elif agent_type.lower() == "ddpg":
        train_ddpg(num_episodes)
    elif agent_type.lower() == "sac":
        train_sac(num_episodes)
    elif agent_type.lower() == "td3":
        train_td3(num_episodes)
    else:
        print(f"Unknown agent type: {agent_type}")
        print("Available agents: dqn, ppo, a2c, ddpg, sac, td3")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train RL agent')
    parser.add_argument('--agent', '-a', type=str, default='dqn', 
                        choices=['dqn', 'ppo', 'a2c', 'ddpg', 'sac', 'td3'],
                        help='Agent type: dqn, ppo, a2c, ddpg, sac, td3 (default: dqn)')
    parser.add_argument('--episodes', '-e', type=int, default=100, 
                        help='Number of training episodes (default: 100)')
    args = parser.parse_args()
    
    train(args.episodes, args.agent)
