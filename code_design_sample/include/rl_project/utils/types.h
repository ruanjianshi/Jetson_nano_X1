/**
 * @file types.h
 * @brief 网格世界环境类型定义
 * @note 位于 include/rl_project/env/ 目录下
 */

#pragma once

#include <cstdint>
#include <array>

namespace rl_project::env {  // NOLINT

constexpr std::uint8_t kAgentChannel = 0;
constexpr std::uint8_t kGoalChannel = 1;
constexpr std::uint8_t kObstacleNChannel = 2;
constexpr std::uint8_t kObstacleEChannel = 3;
constexpr std::uint8_t kObstacleSChannel = 4;
constexpr std::uint8_t kObstacleWChannel = 5;
constexpr std::uint8_t kChannelCount = 6;

constexpr std::uint8_t kActionCount = 9;
constexpr std::int32_t kRewardFood = 1;
constexpr std::int32_t kRewardObstacle = -1;
constexpr std::int32_t kRewardOutOfBounds = -2;
constexpr std::int32_t kRewardDefault = 0;

constexpr std::uint8_t kWindowSize = 33;
constexpr std::uint8_t kHalfSize = 16;

enum class action_t : std::uint8_t {
    UP = 0,        ///< 上 ↑ (index 0)
    UP_RIGHT = 1,  ///< 右上 ↗ (index 1)
    RIGHT = 2,     ///< 右 → (index 2)
    DOWN_RIGHT = 3,///< 右下 ↘ (index 3)
    DOWN = 4,     ///< 下 ↓ (index 4)
    DOWN_LEFT = 5,///< 左下 ↙ (index 5)
    LEFT = 6,     ///< 左 ← (index 6)
    UP_LEFT = 7,  ///< 左上 ↖ (index 7)
    STAY = 8,     ///< 原地 □ (index 8)
    INVALID
};

struct position_t {
    std::uint8_t row_v {0};
    std::uint8_t col_v {0};

    constexpr bool operator==(const position_t& other) const {
        return row_v == other.row_v && col_v == other.col_v;
    }

    position_t operator+(const position_t& other) const {
        return position_t{static_cast<std::uint8_t>(row_v + other.row_v),
                          static_cast<std::uint8_t>(col_v + other.col_v)};
    }
};

constexpr std::int8_t kDirectionRow[] = {-1, -1, 0, 1, 1, 1, 0, -1, 0};
constexpr std::int8_t kDirectionCol[] = {0, 1, 1, 1, 0, -1, -1, -1, 0};

struct transition_result_t {
    position_t next_pos_v;
    std::int32_t reward_v {0};
    bool terminal_v {false};
    bool ate_food_v {false};
    bool hit_obstacle_v {false};
};

struct env_config_t {
    std::uint16_t height_v {64};
    std::uint16_t width_v {64};
    float obstacle_prob_v {0.05f};
    std::uint16_t obstacle_freq_v {20};
    std::uint16_t food_count_v {20};
};

struct step_result_t {
    std::array<float, kChannelCount * kWindowSize * kWindowSize> state_v;
    float reward_v {0.0f};
    bool terminal_v {false};
};

}  // namespace rl_project::env