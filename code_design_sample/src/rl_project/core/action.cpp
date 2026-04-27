/**
 * @file action.cpp
 * @brief Action 类实现
 * @note 位于 src/rl_project/env/ 目录下
 */

#include "env/action.h"
#include "env/game_env.h"
#include <cstdlib>
#include <ctime>

namespace rl_project::env {  // NOLINT

action_t::action_t(std::uint8_t action_idx)
    : index_v(action_idx >= kActionCount ? 8 : action_idx) {}

const char* action_t::to_string() const {
    return kActionChars + index_v;
}

void action_t::apply_to(game_env_t& env) const {
    auto dir = direction();
    (void)env;
    (void)dir;
}

action_t action_t::random() {
    return action_t(static_cast<std::uint8_t>(std::rand() % kActionCount));
}

action_t action_t::from_index(std::uint8_t idx) {
    return action_t(idx);
}

}  // namespace rl_project::env