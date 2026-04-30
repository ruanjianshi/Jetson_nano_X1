# -*- coding: utf-8 -*-
"""
@file eval.py
@brief 强化学习验证/评估脚本
@note 位于 rl_project/train-eval/ 目录下

自动加载最新的模型进行评估，支持 DQN, PPO, A2C, DDPG, SAC, TD3

使用方法:
    python3 eval.py --agent dqn -e 50
    python3 eval.py --agent ppo -e 50
    python3 eval.py --agent a2c -e 50
    python3 eval.py --agent ddpg -e 50
    python3 eval.py --agent sac -e 50
    python3 eval.py --agent td3 -e 50
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Utils.types import EnvConfig, DQNConfig
from Environment.GameEnv import GameEnv
from Environment.Action import Action


def get_latest_model_path(agent_type: str):
    """@brief 获取最新的模型路径"""
    import glob
    
    example_dir = os.path.dirname(os.path.abspath(__file__))
    model_files = glob.glob(os.path.join(example_dir, f"{agent_type}_model_*ep.pt"))
    
    if not model_files:
        return None
    
    return max(model_files, key=os.path.getctime)


def get_env_config():
    """@brief 获取环境配置 (与训练时一致)"""
    return EnvConfig(
        height=32,
        width=32,
        obstacle_prob=0.03,
        obstacle_freq=999,
        food_count=15
    )


def get_agent_config():
    """@brief 获取智能体配置 (与训练时一致)"""
    config = DQNConfig()
    config.state_dim_v = 6 * 33 * 33
    config.action_dim_v = 9
    config.learning_rate_v = 0.0003
    config.gamma_v = 0.99
    config.epsilon_decay_steps_v = 2000
    config.batch_size_v = 64
    config.memory_capacity_v = 50000
    config.target_update_freq_v = 100
    return config


def evaluate_dqn(num_episodes: int) -> None:
    """@brief 评估 DQN 模型"""
    from Agents.DQNAgent import DQNAgent
    
    print("=" * 50, flush=True)
    print("       DQN Evaluation - Grid World", flush=True)
    print("=" * 50, flush=True)

    model_path = get_latest_model_path("dqn")

    if model_path is None or not os.path.exists(model_path):
        print("ERROR: No DQN model file found!", flush=True)
        print("\nPlease train first: python3 train.py --agent dqn", flush=True)
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = DQNAgent(agent_config)

    agent.load(model_path)
    agent.set_epsilon(0.0)

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    print(f"Loaded: {os.path.basename(model_path)}", flush=True)
    print(f"Agent: DQN", flush=True)
    print(f"Epsilon: {agent.get_epsilon():.4f} (pure exploitation)", flush=True)
    print("=" * 50, flush=True)
    print(f"{'Episode':<10} | {'Reward':<10} | {'Steps':<8} | {'Food':<6}", flush=True)
    print("-" * 50, flush=True)

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

        food_eaten = initial_food - len(env.food_pos_list_v)
        if step >= 300:
            food_eaten = initial_food
        food_eaten_list.append(food_eaten)

        print(f"{ep+1:<10} | {total_reward:<10.3f} | {step:<8} | {food_eaten:<6}", flush=True)

    print("=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Agent:           DQN")
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.3f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Ep:     {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.3f}")
    print(f"Max Reward:      {max(episode_rewards):.3f}")
    print("=" * 50)


def evaluate_ppo(num_episodes: int) -> None:
    """@brief 评估 PPO 模型"""
    from Agents.PPOAgent import PPOAgent
    
    print("=" * 50, flush=True)
    print("       PPO Evaluation - Grid World", flush=True)
    print("=" * 50, flush=True)

    model_path = get_latest_model_path("ppo")

    if model_path is None or not os.path.exists(model_path):
        print("ERROR: No PPO model file found!", flush=True)
        print("\nPlease train first: python3 train.py --agent ppo", flush=True)
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = PPOAgent(agent_config)

    agent.load(model_path)

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    print(f"Loaded: {os.path.basename(model_path)}", flush=True)
    print(f"Agent: PPO", flush=True)
    print(f"Epsilon: {agent.get_epsilon():.4f} (stochastic)", flush=True)
    print("=" * 50, flush=True)
    print(f"{'Episode':<10} | {'Reward':<10} | {'Steps':<8} | {'Food':<6}", flush=True)
    print("-" * 50, flush=True)

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0
        initial_food = len(env.food_pos_list_v)

        while step < 300:
            state_tensor = state.tensor()
            action_idx, _ = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            if step_result.terminal_v:
                break

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

        episode_rewards.append(total_reward)
        episode_steps.append(step)

        food_eaten = initial_food - len(env.food_pos_list_v)
        if step >= 300:
            food_eaten = initial_food
        food_eaten_list.append(food_eaten)

        print(f"{ep+1:<10} | {total_reward:<10.3f} | {step:<8} | {food_eaten:<6}", flush=True)

    print("=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Agent:           PPO")
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.3f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Ep:     {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.3f}")
    print(f"Max Reward:      {max(episode_rewards):.3f}")
    print("=" * 50)


def evaluate_a2c(num_episodes: int) -> None:
    """@brief 评估 A2C 模型"""
    from Agents.A2CAgent import A2CAgent
    
    print("=" * 50, flush=True)
    print("       A2C Evaluation - Grid World", flush=True)
    print("=" * 50, flush=True)

    model_path = get_latest_model_path("a2c")

    if model_path is None or not os.path.exists(model_path):
        print("ERROR: No A2C model file found!", flush=True)
        print("\nPlease train first: python3 train.py --agent a2c", flush=True)
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = A2CAgent(agent_config)

    agent.load(model_path)

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    print(f"Loaded: {os.path.basename(model_path)}", flush=True)
    print(f"Agent: A2C", flush=True)
    print("=" * 50, flush=True)
    print(f"{'Episode':<10} | {'Reward':<10} | {'Steps':<8} | {'Food':<6}", flush=True)
    print("-" * 50, flush=True)

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0
        initial_food = len(env.food_pos_list_v)

        while step < 300:
            state_tensor = state.tensor()
            action_idx, _ = agent.select_action(state_tensor)
            step_result = env.step(Action(action_idx))

            if step_result.terminal_v:
                break

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

        episode_rewards.append(total_reward)
        episode_steps.append(step)

        food_eaten = initial_food - len(env.food_pos_list_v)
        if step >= 300:
            food_eaten = initial_food
        food_eaten_list.append(food_eaten)

        print(f"{ep+1:<10} | {total_reward:<10.3f} | {step:<8} | {food_eaten:<6}", flush=True)

    print("=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Agent:           A2C")
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.3f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Ep:     {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.3f}")
    print(f"Max Reward:      {max(episode_rewards):.3f}")
    print("=" * 50)


def evaluate_ddpg(num_episodes: int) -> None:
    """@brief 评估 DDPG 模型"""
    from Agents.DDPGAgent import DDPGAgent
    
    print("=" * 50, flush=True)
    print("       DDPG Evaluation - Grid World", flush=True)
    print("=" * 50, flush=True)

    model_path = get_latest_model_path("ddpg")

    if model_path is None or not os.path.exists(model_path):
        print("ERROR: No DDPG model file found!", flush=True)
        print("\nPlease train first: python3 train.py --agent ddpg", flush=True)
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = DDPGAgent(agent_config)

    agent.load(model_path)
    agent.set_epsilon(0.0)

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    print(f"Loaded: {os.path.basename(model_path)}", flush=True)
    print(f"Agent: DDPG", flush=True)
    print(f"Epsilon: {agent.get_epsilon():.4f} (pure exploitation)", flush=True)
    print("=" * 50, flush=True)
    print(f"{'Episode':<10} | {'Reward':<10} | {'Steps':<8} | {'Food':<6}", flush=True)
    print("-" * 50, flush=True)

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

        food_eaten = initial_food - len(env.food_pos_list_v)
        if step >= 300:
            food_eaten = initial_food
        food_eaten_list.append(food_eaten)

        print(f"{ep+1:<10} | {total_reward:<10.3f} | {step:<8} | {food_eaten:<6}", flush=True)

    print("=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Agent:           DDPG")
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.3f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Ep:     {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.3f}")
    print(f"Max Reward:      {max(episode_rewards):.3f}")
    print("=" * 50)


def evaluate_sac(num_episodes: int) -> None:
    """@brief 评估 SAC 模型"""
    from Agents.SACAgent import SACAgent
    
    print("=" * 50, flush=True)
    print("       SAC Evaluation - Grid World", flush=True)
    print("=" * 50, flush=True)

    model_path = get_latest_model_path("sac")

    if model_path is None or not os.path.exists(model_path):
        print("ERROR: No SAC model file found!", flush=True)
        print("\nPlease train first: python3 train.py --agent sac", flush=True)
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = SACAgent(agent_config)

    agent.load(model_path)

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    print(f"Loaded: {os.path.basename(model_path)}", flush=True)
    print(f"Agent: SAC", flush=True)
    print("=" * 50, flush=True)
    print(f"{'Episode':<10} | {'Reward':<10} | {'Steps':<8} | {'Food':<6}", flush=True)
    print("-" * 50, flush=True)

    for ep in range(num_episodes):
        env.reset()
        state = env.current_state()
        step = 0
        total_reward = 0.0
        initial_food = len(env.food_pos_list_v)

        while step < 300:
            state_tensor = state.tensor()
            action_idx, _ = agent.select_action(state_tensor, deterministic=True)
            step_result = env.step(Action(action_idx))

            if step_result.terminal_v:
                break

            total_reward += step_result.reward_v
            state = env.current_state()
            step += 1

        episode_rewards.append(total_reward)
        episode_steps.append(step)

        food_eaten = initial_food - len(env.food_pos_list_v)
        if step >= 300:
            food_eaten = initial_food
        food_eaten_list.append(food_eaten)

        print(f"{ep+1:<10} | {total_reward:<10.3f} | {step:<8} | {food_eaten:<6}", flush=True)

    print("=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Agent:           SAC")
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.3f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Ep:     {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.3f}")
    print(f"Max Reward:      {max(episode_rewards):.3f}")
    print("=" * 50)


def evaluate_td3(num_episodes: int) -> None:
    """@brief 评估 TD3 模型"""
    from Agents.TD3Agent import TD3Agent
    
    print("=" * 50, flush=True)
    print("       TD3 Evaluation - Grid World", flush=True)
    print("=" * 50, flush=True)

    model_path = get_latest_model_path("td3")

    if model_path is None or not os.path.exists(model_path):
        print("ERROR: No TD3 model file found!", flush=True)
        print("\nPlease train first: python3 train.py --agent td3", flush=True)
        return

    config = get_env_config()
    agent_config = get_agent_config()

    env = GameEnv(config)
    agent = TD3Agent(agent_config)

    agent.load(model_path)
    agent.set_epsilon(0.0)

    episode_rewards = []
    episode_steps = []
    food_eaten_list = []

    print(f"Loaded: {os.path.basename(model_path)}", flush=True)
    print(f"Agent: TD3", flush=True)
    print(f"Epsilon: {agent.get_epsilon():.4f} (pure exploitation)", flush=True)
    print("=" * 50, flush=True)
    print(f"{'Episode':<10} | {'Reward':<10} | {'Steps':<8} | {'Food':<6}", flush=True)
    print("-" * 50, flush=True)

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

        food_eaten = initial_food - len(env.food_pos_list_v)
        if step >= 300:
            food_eaten = initial_food
        food_eaten_list.append(food_eaten)

        print(f"{ep+1:<10} | {total_reward:<10.3f} | {step:<8} | {food_eaten:<6}", flush=True)

    print("=" * 50)
    print("       Evaluation Results")
    print("=" * 50)
    print(f"Agent:           TD3")
    print(f"Episodes:        {num_episodes}")
    print(f"Avg Reward:      {sum(episode_rewards)/len(episode_rewards):.3f}")
    print(f"Avg Steps:       {sum(episode_steps)/len(episode_steps):.1f}")
    print(f"Avg Food/Ep:     {sum(food_eaten_list)/len(food_eaten_list):.1f}")
    print(f"Min Reward:      {min(episode_rewards):.3f}")
    print(f"Max Reward:      {max(episode_rewards):.3f}")
    print("=" * 50)


def evaluate(num_episodes: int = 20, agent_type: str = None) -> None:
    """
    @brief 评估模型
    
    @param num_episodes: 评估的 episode 数量
    @param agent_type: 智能体类型
    """
    if agent_type is None:
        print("\nSelect agent type:")
        print("1. DQN")
        print("2. PPO")
        print("3. A2C")
        print("4. DDPG")
        print("5. SAC")
        print("6. TD3")
        print("Enter choice (1-6): ", end="", flush=True)
        choice = input().strip()
        agent_map = {"1": "dqn", "2": "ppo", "3": "a2c", "4": "ddpg", "5": "sac", "6": "td3"}
        agent_type = agent_map.get(choice, "dqn")
    
    if agent_type.lower() == "dqn":
        evaluate_dqn(num_episodes)
    elif agent_type.lower() == "ppo":
        evaluate_ppo(num_episodes)
    elif agent_type.lower() == "a2c":
        evaluate_a2c(num_episodes)
    elif agent_type.lower() == "ddpg":
        evaluate_ddpg(num_episodes)
    elif agent_type.lower() == "sac":
        evaluate_sac(num_episodes)
    elif agent_type.lower() == "td3":
        evaluate_td3(num_episodes)
    else:
        print(f"Unknown agent type: {agent_type}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate RL agent')
    parser.add_argument('--agent', '-a', type=str, default=None,
                        choices=['dqn', 'ppo', 'a2c', 'ddpg', 'sac', 'td3'],
                        help='Agent type: dqn, ppo, a2c, ddpg, sac, td3 (default: ask interactively)')
    parser.add_argument('--episodes', '-e', type=int, default=20, 
                        help='Number of evaluation episodes (default: 20)')
    args = parser.parse_args()
    
    evaluate(args.episodes, args.agent)
