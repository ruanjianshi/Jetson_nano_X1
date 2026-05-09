/**
 * @file dqn_agent.h
 * @brief DQN 智能体实现
 * @note 位于 include/rl_project/agent/ 目录下
 */

#pragma once

#include "env/types.h"
#include <array>
#include <vector>
#include <memory>

namespace rl_project::agent {  // NOLINT

struct dqn_config_t {
    std::uint16_t state_dim_v {kChannelCount * kWindowSize * kWindowSize};
    std::uint16_t action_dim_v {kActionCount};
    float learning_rate_v {0.001f};
    float gamma_v {0.99f};
    float epsilon_start_v {1.0f};
    float epsilon_end_v {0.01f};
    std::uint32_t epsilon_decay_steps_v {10000};
    std::uint32_t batch_size_v {32};
    std::uint32_t memory_capacity_v {10000};
    std::uint32_t target_update_freq_v {100};
};

struct transition_t {
    std::array<float, kChannelCount * kWindowSize * kWindowSize> state_v;
    std::uint8_t action_v;
    float reward_v;
    std::array<float, kChannelCount * kWindowSize * kWindowSize> next_state_v;
    bool terminal_v;
};

class dqn_agent_t {
public:
    explicit dqn_agent_t(const dqn_config_t& config);

    dqn_agent_t();

    std::uint8_t select_action(const std::array<float, kChannelCount * kWindowSize * kWindowSize>& state);

    void store_transition(const transition_t& transition);

    void train();

    float get_epsilon() const;

    void set_epsilon(float epsilon);

    std::uint32_t memory_size() const;

private:
    dqn_config_t config_v;
    std::vector<transition_t> memory_v;
    std::vector<float> q_table_v;
    std::uint32_t training_step_v {0};
    float epsilon_v {1.0f};

    std::uint8_t epsilon_greedy(const std::array<float, kChannelCount * kWindowSize * kWindowSize>& state);

    std::uint8_t argmax(const std::array<float, kChannelCount * kWindowSize * kWindowSize>& state);

    float compute_target(const transition_t& transition);
};

}  // namespace rl_project::agent