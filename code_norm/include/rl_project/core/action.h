/**
 * @file action.h
 * @brief Action 类 - 智能体的动作
 * @note 位于 include/rl_project/core/ 目录下
 */

#pragma once

#include "utils/types.h"
#include <cstdint>

namespace rl_project::env {  // NOLINT

class game_env_t;

class action_t {
public:
    static constexpr const char* kActionChars = "↑↗→↘↓↙←↖□";

    explicit action_t(std::uint8_t action_idx);

    action_t() = default;

    static action_t random();

    static action_t from_index(std::uint8_t idx);

    constexpr std::uint8_t index() const { return index_v; }

    const char* to_string() const;

    void apply_to(game_env_t& env) const;

    constexpr position_t direction() const {
        return position_t{static_cast<std::uint8_t>(kDirectionRow[index_v]),
                         static_cast<std::uint8_t>(kDirectionCol[index_v])};
    }

private:
    std::uint8_t index_v {0};
};

}  // namespace rl_project::env