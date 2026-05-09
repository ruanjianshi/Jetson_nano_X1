/**
 * @file rl_example.cpp
 * @brief 强化学习示例 - DQN 智能体训练网格世界
 * @note 位于 src/rl_project/example/ 目录下
 * @details 展示如何使用 GameEnv 和 DQNAgent 进行训练
 */

#include "env/game_env.h"
#include "env/action.h"
#include "env/state.h"
#include "agent/dqn_agent.h"
#include <iostream>
#include <vector>
#include <iomanip>

namespace rl_project::example {  // NOLINT

void print_step(std::uint32_t episode, std::uint32_t step,
                const env::position_t& agent_pos,
                float reward, float epsilon) {
    std::cout << "Ep " << std::setw(4) << episode
              << " | Step " << std::setw(4) << step
              << " | Agent (" << std::setw(2) << static_cast<int>(agent_pos.row_v)
              << "," << std::setw(2) << static_cast<int>(agent_pos.col_v)
              << ") | Reward " << std::setw(5) << std::showpos << reward
              << " | Epsilon " << std::setw(6) << std::noshowpos << epsilon
              << std::endl;
}

void run_episode(agent::dqn_agent_t& agent, env::game_env_t& env,
                 bool training, bool verbose) {
    env.reset();

    auto state = env.current_state();
    std::uint32_t step = 0;
    float total_reward = 0.0f;

    while (true) {
        auto state_tensor = state.tensor();

        std::uint8_t action_idx = agent.select_action(state_tensor);

        auto step_result = env.step(env::action_t(action_idx));

        if (step_result.terminal_v) {
            if (verbose) {
                std::cout << "  -> Episode ended! Reward: " << step_result.reward_v << std::endl;
            }
            break;
        }

        if (training) {
            agent::transition_t trans {};
            std::memcpy(trans.state_v.data(), state_tensor.data(), sizeof(trans.state_v));
            trans.action_v = action_idx;
            trans.reward_v = step_result.reward_v;
            trans.terminal_v = step_result.terminal_v;

            agent.store_transition(trans);
            agent.train();
        }

        total_reward += step_result.reward_v;
        state = env.current_state();
        step++;

        if (verbose) {
            print_step(0, step, env.agent_pos(), step_result.reward_v, agent.get_epsilon());
        }

        if (step >= 500) {
            if (verbose) {
                std::cout << "  -> Max steps reached!" << std::endl;
            }
            break;
        }
    }

    if (verbose) {
        std::cout << "  Total reward: " << total_reward << ", Steps: " << step << std::endl;
    }
}

void train(std::uint32_t num_episodes) {
    std::cout << "========================================" << std::endl;
    std::cout << "       DQN Training - Grid World" << std::endl;
    std::cout << "========================================" << std::endl;

    env::env_config_t config {};
    config.height_v = 64;
    config.width_v = 64;
    config.obstacle_prob_v = 0.05f;
    config.obstacle_freq_v = 20;
    config.food_count_v = 20;

    agent::dqn_config_t agent_config {};
    agent_config.state_dim_v = env::kChannelCount * env::kWindowSize * env::kWindowSize;
    agent_config.action_dim_v = env::kActionCount;
    agent_config.learning_rate_v = 0.001f;
    agent_config.gamma_v = 0.99f;
    agent_config.epsilon_start_v = 1.0f;
    agent_config.epsilon_end_v = 0.01f;
    agent_config.epsilon_decay_steps_v = 5000;
    agent_config.batch_size_v = 32;
    agent_config.memory_capacity_v = 10000;

    env::game_env_t env(config);
    agent::dqn_agent_t agent(agent_config);

    std::vector<float> episode_rewards;
    episode_rewards.reserve(num_episodes);

    for (std::uint32_t ep = 0; ep < num_episodes; ++ep) {
        env.reset();

        auto state = env.current_state();
        std::uint32_t step = 0;
        float total_reward = 0.0f;

        while (step < 500) {
            auto state_tensor = state.tensor();

            std::uint8_t action_idx = agent.select_action(state_tensor);

            auto step_result = env.step(env::action_t(action_idx));

            if (step_result.terminal_v) {
                break;
            }

            agent::transition_t trans {};
            std::memcpy(trans.state_v.data(), state_tensor.data(), sizeof(trans.state_v));
            trans.action_v = action_idx;
            trans.reward_v = step_result.reward_v;
            std::memcpy(trans.next_state_v.data(), env.current_state().tensor().data(),
                        sizeof(trans.next_state_v));
            trans.terminal_v = step_result.terminal_v;

            agent.store_transition(trans);
            agent.train();

            total_reward += step_result.reward_v;
            state = env.current_state();
            step++;
        }

        episode_rewards.push_back(total_reward);

        if ((ep + 1) % 10 == 0) {
            float avg_reward = 0.0f;
            for (std::size_t i = ep - 9; i <= ep; ++i) {
                avg_reward += episode_rewards[i];
            }
            avg_reward /= 10.0f;

            std::cout << "Episode " << std::setw(5) << (ep + 1)
                      << " | Avg Reward (last 10): " << std::setw(8) << std::fixed
                      << std::setprecision(2) << avg_reward
                      << " | Epsilon: " << std::setprecision(4) << agent.get_epsilon()
                      << " | Memory: " << agent.memory_size()
                      << std::endl;
        }

        if ((ep + 1) % 50 == 0) {
            env.render();
        }
    }

    std::cout << "\n========================================" << std::endl;
    std::cout << "       Training Complete!" << std::endl;
    std::cout << "========================================" << std::endl;

    float total = 0.0f;
    for (auto r : episode_rewards) {
        total += r;
    }
    std::cout << "Average reward: " << (total / episode_rewards.size()) << std::endl;
}

void test(std::uint32_t num_episodes) {
    std::cout << "========================================" << std::endl;
    std::cout << "       DQN Testing - Grid World" << std::endl;
    std::cout << "========================================" << std::endl;

    env::env_config_t config {};
    config.height_v = 64;
    config.width_v = 64;
    config.obstacle_prob_v = 0.05f;
    config.obstacle_freq_v = 20;
    config.food_count_v = 20;

    agent::dqn_config_t agent_config {};
    agent_config.state_dim_v = env::kChannelCount * env::kWindowSize * env::kWindowSize;
    agent_config.action_dim_v = env::kActionCount;

    env::game_env_t env(config);
    agent::dqn_agent_t agent(agent_config);

    agent.set_epsilon(0.0f);

    for (std::uint32_t ep = 0; ep < num_episodes; ++ep) {
        env.reset();

        auto state = env.current_state();
        std::uint32_t step = 0;
        float total_reward = 0.0f;

        std::cout << "\nEpisode " << (ep + 1) << ":" << std::endl;

        while (step < 500) {
            auto state_tensor = state.tensor();
            std::uint8_t action_idx = agent.select_action(state_tensor);

            auto step_result = env.step(env::action_t(action_idx));

            print_step(ep + 1, step + 1, env.agent_pos(),
                       step_result.reward_v, 0.0f);

            total_reward += step_result.reward_v;
            state = env.current_state();
            step++;

            if (step_result.terminal_v) {
                break;
            }
        }

        std::cout << "Total reward: " << total_reward << std::endl;
    }
}

}  // namespace rl_project::example

int main() {
    std::srand(static_cast<unsigned>(std::time(nullptr)));

    std::cout << "Select mode:" << std::endl;
    std::cout << "1. Train (200 episodes)" << std::endl;
    std::cout << "2. Test (5 episodes)" << std::endl;
    std::cout << "Enter choice (1/2): ";

    int choice = 1;
    std::cin >> choice;

    if (choice == 1) {
        rl_project::example::train(200);
    } else {
        rl_project::example::test(5);
    }

    return 0;
}