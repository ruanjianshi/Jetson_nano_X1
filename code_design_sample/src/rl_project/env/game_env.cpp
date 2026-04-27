/**
 * @file game_env.cpp
 * @brief GameEnv 类实现
 * @note 位于 src/rl_project/env/ 目录下
 */

#include "env/game_env.h"
#include <algorithm>
#include <cstdlib>
#include <ctime>
#include <cstring>

namespace rl_project::env {  // NOLINT

namespace {

constexpr std::int8_t kObstacleMoveRow[] = {-1, 0, 1, 0};
constexpr std::int8_t kObstacleMoveCol[] = {0, 1, 0, -1};

bool is_valid_position(std::uint8_t row, std::uint8_t col, std::uint16_t height, std::uint16_t width) {
    return row < height && col < width;
}

}  // namespace

game_env_t::game_env_t(const env_config_t& config)
    : config_v(config),
      grid_v(config.height_v, std::vector<std::uint8_t>(config.width_v, 0)) {
    std::srand(static_cast<unsigned>(std::time(nullptr)));
    reset();
}

game_env_t::game_env_t()
    : game_env_t(env_config_t{}) {}

state_t game_env_t::reset() {
    std::memset(grid_v.data()->data(), 0, grid_v.size() * grid_v[0].size());

    food_pos_list_v.clear();

    agent_pos_v.row_v = static_cast<std::uint8_t>(std::rand() % (config_v.height_v - 2) + 1);
    agent_pos_v.col_v = static_cast<std::uint8_t>(std::rand() % (config_v.width_v - 2) + 1);

    generate_obstacles();
    generate_food();

    t_v = 0;
    total_reward_v = 0.0f;

    update_state();
    return current_state_v;
}

void game_env_t::generate_obstacles() {
    for (std::uint8_t edge = 0; edge < 4; ++edge) {
        if (edge == 0) {
            for (std::uint16_t c = 0; c < config_v.width_v; ++c) {
                if (static_cast<float>(std::rand()) / RAND_MAX < config_v.obstacle_prob_v) {
                    grid_v[0][c] |= (1 << kObstacleSChannel);
                }
            }
        } else if (edge == 1) {
            for (std::uint16_t c = 0; c < config_v.width_v; ++c) {
                if (static_cast<float>(std::rand()) / RAND_MAX < config_v.obstacle_prob_v) {
                    grid_v[config_v.height_v - 1][c] |= (1 << kObstacleNChannel);
                }
            }
        } else if (edge == 2) {
            for (std::uint16_t r = 0; r < config_v.height_v; ++r) {
                if (static_cast<float>(std::rand()) / RAND_MAX < config_v.obstacle_prob_v) {
                    grid_v[r][0] |= (1 << kObstacleEChannel);
                }
            }
        } else {
            for (std::uint16_t r = 0; r < config_v.height_v; ++r) {
                if (static_cast<float>(std::rand()) / RAND_MAX < config_v.obstacle_prob_v) {
                    grid_v[r][config_v.width_v - 1] |= (1 << kObstacleWChannel);
                }
            }
        }
    }
}

void game_env_t::generate_food() {
    while (food_pos_list_v.size() < config_v.food_count_v) {
        position_t pos {
            static_cast<std::uint8_t>(std::rand() % (config_v.height_v - 2) + 1),
            static_cast<std::uint8_t>(std::rand() % (config_v.width_v - 2) + 1)
        };

        if (!(pos.row_v == agent_pos_v.row_v && pos.col_v == agent_pos_v.col_v)) {
            food_pos_list_v.push_back(pos);
            grid_v[pos.row_v][pos.col_v] |= (1 << kGoalChannel);
        }
    }
}

void game_env_t::move_obstacles() {
    std::vector<std::vector<std::uint8_t>> new_grid = grid_v;

    for (std::uint16_t r = 0; r < config_v.height_v; ++r) {
        for (std::uint16_t c = 0; c < config_v.width_v; ++c) {
            std::uint8_t cell = grid_v[r][c];

            for (std::uint8_t ch = kObstacleNChannel; ch <= kObstacleWChannel; ++ch) {
                if (cell & (1 << ch)) {
                    std::uint8_t dir_idx = ch - kObstacleNChannel;
                    std::int8_t dr = kObstacleMoveRow[dir_idx];
                    std::int8_t dc = kObstacleMoveCol[dir_idx];

                    std::uint8_t new_r = static_cast<std::uint8_t>(r + dr);
                    std::uint8_t new_c = static_cast<std::uint8_t>(c + dc);

                    if (new_r < config_v.height_v && new_c < config_v.width_v) {
                        new_grid[new_r][new_c] |= (1 << ch);
                    }
                }
            }
        }
    }

    grid_v = std::move(new_grid);
}

step_result_t game_env_t::step(const action_t& action) {
    step_result_t result {};

    auto dir = action.direction();
    position_t new_pos {
        static_cast<std::uint8_t>(agent_pos_v.row_v + dir.row_v),
        static_cast<std::uint8_t>(agent_pos_v.col_v + dir.col_v)
    };

    if (is_out_of_bounds(new_pos)) {
        result.reward_v = static_cast<float>(kRewardOutOfBounds);
        result.terminal_v = true;
        total_reward_v += result.reward_v;
        t_v++;
        return result;
    }

    if (is_obstacle(new_pos)) {
        result.reward_v = static_cast<float>(kRewardObstacle);
        result.terminal_v = true;
        result.hit_obstacle_v = true;
        total_reward_v += result.reward_v;
        t_v++;
        return result;
    }

    agent_pos_v = new_pos;

    if (is_food(agent_pos_v)) {
        result.reward_v = static_cast<float>(kRewardFood);
        result.ate_food_v = true;
        grid_v[agent_pos_v.row_v][agent_pos_v.col_v] &= ~(1 << kGoalChannel);
        for (auto it = food_pos_list_v.begin(); it != food_pos_list_v.end(); ++it) {
            if (it->row_v == agent_pos_v.row_v && it->col_v == agent_pos_v.col_v) {
                food_pos_list_v.erase(it);
                break;
            }
        }
        generate_food();
    } else {
        result.reward_v = static_cast<float>(kRewardDefault);
    }

    if (t_v % config_v.obstacle_freq_v == 0) {
        generate_obstacles();
    }

    move_obstacles();

    update_state();
    result.terminal_v = false;

    total_reward_v += result.reward_v;
    t_v++;

    return result;
}

bool game_env_t::is_out_of_bounds(const position_t& pos) const {
    return pos.row_v == 0 || pos.row_v >= config_v.height_v - 1 ||
           pos.col_v == 0 || pos.col_v >= config_v.width_v - 1;
}

bool game_env_t::is_obstacle(const position_t& pos) const {
    if (!is_valid_pos(pos.row_v, pos.col_v, config_v.height_v, config_v.width_v)) {
        return false;
    }
    std::uint8_t cell = grid_v[pos.row_v][pos.col_v];
    for (std::uint8_t ch = kObstacleNChannel; ch <= kObstacleWChannel; ++ch) {
        if (cell & (1 << ch)) {
            return true;
        }
    }
    return false;
}

bool game_env_t::is_food(const position_t& pos) const {
    if (!is_valid_pos(pos.row_v, pos.col_v, config_v.height_v, config_v.width_v)) {
        return false;
    }
    return (grid_v[pos.row_v][pos.col_v] & (1 << kGoalChannel)) != 0;
}

void game_env_t::update_state() {
    current_state_v = state_t(*this);
}

bool game_env_t::is_valid_pos(std::uint8_t row, std::uint8_t col) const {
    return is_valid_position(row, col, config_v.height_v, config_v.width_v);
}

void game_env_t::render() {
    std::cout << "=== GameEnv Render ===" << std::endl;
    std::cout << "Time: " << t_v << ", Total Reward: " << total_reward_v << std::endl;
    std::cout << "Agent Position: (" << static_cast<int>(agent_pos_v.row_v)
              << ", " << static_cast<int>(agent_pos_v.col_v) << ")" << std::endl;
    std::cout << "Food Count: " << food_pos_list_v.size() << std::endl;

    std::cout << "Grid (";
    for (std::uint16_t r = 0; r < std::min<std::uint16_t>(10, config_v.height_v); ++r) {
        if (r > 0) std::cout << " ";
        for (std::uint16_t c = 0; c < std::min<std::uint16_t>(16, config_v.width_v); ++c) {
            char ch = '.';
            if (r == agent_pos_v.row_v && c == agent_pos_v.col_v) {
                ch = 'A';
            } else if (grid_v[r][c] & (1 << kGoalChannel)) {
                ch = 'F';
            } else if (grid_v[r][c] & (1 << kObstacleNChannel)) {
                ch = 'N';
            } else if (grid_v[r][c] & (1 << kObstacleEChannel)) {
                ch = 'E';
            } else if (grid_v[r][c] & (1 << kObstacleSChannel)) {
                ch = 'S';
            } else if (grid_v[r][c] & (1 << kObstacleWChannel)) {
                ch = 'W';
            }
            std::cout << ch;
        }
        std::cout << std::endl;
    }
    std::cout << "=== End Render ===" << std::endl;
}

}  // namespace rl_project::env