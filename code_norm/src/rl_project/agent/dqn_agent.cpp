/**
 * @file dqn_agent.cpp
 * @brief DQN 智能体实现
 * @note 位于 src/rl_project/agent/ 目录下
 */

#include "agent/dqn_agent.h"
#include <algorithm>
#include <cstdlib>
#include <cmath>
#include <numeric>

namespace rl_project::agent {  // NOLINT

dqn_agent_t::dqn_agent_t(const dqn_config_t& config)
    : config_v(config),
      q_table_v(config.state_dim_v * config.action_dim_v, 0.0f),
      epsilon_v(config.epsilon_start_v) {
    memory_v.reserve(config.memory_capacity_v);
}

dqn_agent_t::dqn_agent_t()
    : dqn_agent_t(dqn_config_t{}) {}

std::uint8_t dqn_agent_t::select_action(
    const std::array<float, kChannelCount * kWindowSize * kWindowSize>& state) {
    return epsilon_greedy(state);
}

std::uint8_t dqn_agent_t::epsilon_greedy(
    const std::array<float, kChannelCount * kWindowSize * kWindowSize>& state) {
    if (static_cast<float>(std::rand()) / RAND_MAX < epsilon_v) {
        return std::rand() % config_v.action_dim_v;
    }
    return argmax(state);
}

std::uint8_t dqn_agent_t::argmax(
    const std::array<float, kChannelCount * kWindowSize * kWindowSize>& state) {
    std::uint32_t best_action = 0;
    float best_q = -1e9f;

    for (std::uint8_t a = 0; a < config_v.action_dim_v; ++a) {
        float q = 0.0f;
        for (std::uint32_t i = 0; i < config_v.state_dim_v; ++i) {
            q += q_table_v[a * config_v.state_dim_v + i] * state[i];
        }

        if (q > best_q) {
            best_q = q;
            best_action = a;
        }
    }

    return best_action;
}

void dqn_agent_t::store_transition(const transition_t& transition) {
    if (memory_v.size() >= config_v.memory_capacity_v) {
        memory_v.erase(memory_v.begin());
    }
    memory_v.push_back(transition);
}

void dqn_agent_t::train() {
    if (memory_v.size() < config_v.batch_size_v) {
        return;
    }

    std::vector<transition_t> batch;
    std::sample(memory_v.begin(), memory_v.end(), std::back_inserter(batch),
                config_v.batch_size_v, std::mt19937{std::random_device{}()});

    for (const auto& trans : batch) {
        std::uint8_t action = trans.action_v;
        float reward = trans.reward_v;
        bool terminal = trans.terminal_v;

        float target_q = reward;
        if (!terminal) {
            float max_next_q = -1e9f;
            for (std::uint8_t a = 0; a < config_v.action_dim_v; ++a) {
                float q = 0.0f;
                for (std::uint32_t i = 0; i < config_v.state_dim_v; ++i) {
                    q += q_table_v[a * config_v.state_dim_v + i] * trans.next_state_v[i];
                }
                if (q > max_next_q) {
                    max_next_q = q;
                }
            }
            target_q += config_v.gamma_v * max_next_q;
        }

        for (std::uint32_t i = 0; i < config_v.state_dim_v; ++i) {
            float& w = q_table_v[action * config_v.state_dim_v + i];
            w += config_v.learning_rate_v * (target_q - w) * trans.state_v[i];
        }

        (void)compute_target;
    }

    training_step_v++;

    if (epsilon_v > config_v.epsilon_end_v) {
        epsilon_v -= (config_v.epsilon_start_v - config_v.epsilon_end_v) /
                     static_cast<float>(config_v.epsilon_decay_steps_v);
        if (epsilon_v < config_v.epsilon_end_v) {
            epsilon_v = config_v.epsilon_end_v;
        }
    }
}

float dqn_agent_t::get_epsilon() const {
    return epsilon_v;
}

void dqn_agent_t::set_epsilon(float epsilon) {
    epsilon_v = epsilon;
}

std::uint32_t dqn_agent_t::memory_size() const {
    return static_cast<std::uint32_t>(memory_v.size());
}

float dqn_agent_t::compute_target(const transition_t& transition) {
    float target = transition.reward_v;
    if (!transition.terminal_v) {
        float max_q = -1e9f;
        for (std::uint8_t a = 0; a < config_v.action_dim_v; ++a) {
            float q = 0.0f;
            for (std::uint32_t i = 0; i < config_v.state_dim_v; ++i) {
                q += q_table_v[a * config_v.state_dim_v + i] * transition.next_state_v[i];
            }
            max_q = std::max(max_q, q);
        }
        target += config_v.gamma_v * max_q;
    }
    return target;
}

}  // namespace rl_project::agent