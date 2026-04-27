/**
 * @file game_env.h
 * @brief GameEnv 类 - 格子世界环境
 * @note 位于 include/rl_project/env/ 目录下
 */

#pragma once

#include "types.h"
#include "state.h"
#include "action.h"
#include <cstdint>
#include <vector>
#include <array>

namespace rl_project::env {  // NOLINT

class game_env_t {
public:
    explicit game_env_t(const env_config_t& config);

    game_env_t();

    state_t reset();

    step_result_t step(const action_t& action);

    position_t agent_pos() const { return agent_pos_v; }

    const env_config_t& config() const { return config_v; }

    bool is_out_of_bounds(const position_t& pos) const;

    bool is_obstacle(const position_t& pos) const;

    bool is_food(const position_t& pos) const;

    void render();

    std::uint32_t time_step() const { return t_v; }

    float total_reward() const { return total_reward_v; }

private:
    env_config_t config_v {};
    std::vector<std::vector<std::uint8_t>> grid_v;
    std::vector<position_t> food_pos_list_v;
    position_t agent_pos_v {};
    state_t current_state_v;
    std::uint32_t t_v {0};
    float total_reward_v {0.0f};

    void generate_obstacles();
    void generate_food();
    void move_obstacles();
    void update_state();

    bool is_valid_pos(std::uint8_t row, std::uint8_t col) const;
};

}  // namespace rl_project::env