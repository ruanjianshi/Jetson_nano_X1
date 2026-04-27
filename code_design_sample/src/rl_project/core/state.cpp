/**
 * @file state.cpp
 * @brief State 类实现
 * @note 位于 src/rl_project/env/ 目录下
 */

#include "env/state.h"
#include "env/game_env.h"
#include <algorithm>
#include <cstring>

namespace rl_project::env {  // NOLINT

state_t::state_t(const game_env_t& env) {
    initialize_from_env(env);
}

void state_t::initialize_from_env(const game_env_t& env) {
    const auto& config = env.config();
    position_t agent_pos = env.agent_pos();

    std::uint8_t pad_row = kHalfSize + 1;
    std::uint8_t pad_col = kHalfSize + 1;

    std::array<std::array<float, kWindowSize>, kChannelCount> channel_data {};
    for (auto& ch : channel_data) {
        ch.fill(0.5f);
    }

    for (std::uint8_t r = 0; r < config.height_v; ++r) {
        for (std::uint8_t c = 0; c < config.width_v; ++c) {
            std::uint8_t target_r = r + pad_row;
            std::uint8_t target_c = c + pad_col;

            if (target_r < kWindowSize && target_c < kWindowSize) {
                float value = 0.0f;
                if (r == agent_pos.row_v && c == agent_pos.col_v) {
                    channel_data[kAgentChannel][target_r * kWindowSize + target_c] = 1.0f;
                }
            }
        }
    }

    for (std::uint8_t ch = 0; ch < kChannelCount; ++ch) {
        std::memcpy(&tensor_v[ch * kWindowSize * kWindowSize],
                    channel_data[ch].data(),
                    kWindowSize * kWindowSize * sizeof(float));
    }

    (void)env;
}

}  // namespace rl_project::env