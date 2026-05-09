/**
 * @file state.h
 * @brief State 类 - 智能体的感知状态
 * @note 位于 include/rl_project/core/ 目录下
 */

#pragma once

#include "utils/types.h"
#include <array>
#include <cstdint>

namespace rl_project::env {  // NOLINT

class game_env_t;

class state_t {
public:
    static constexpr std::uint8_t kWindowSize = 33;
    static constexpr std::uint8_t kHalfSize = 16;

    explicit state_t(const game_env_t& env);

    state_t() = default;

    constexpr const auto& tensor() const { return tensor_v; }

    constexpr std::uint8_t window_size() const { return kWindowSize; }

    constexpr std::uint8_t channel_count() const { return kChannelCount; }

private:
    std::array<float, kChannelCount * kWindowSize * kWindowSize> tensor_v {};
    void initialize_from_env(const game_env_t& env);
};

}  // namespace rl_project::env