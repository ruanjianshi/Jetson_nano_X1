# ADR-0003: Deep Reinforcement Learning Project

## Status
Accepted

## Context

Based on the article "如何从零开始深度强化学习项目" (P0-P1), we need to implement a grid world environment with:
- Multi-channel grid representation (agent, food, 4-directional obstacles)
- DQN agent with experience replay
- State representation as local perception window
- 9 discrete actions (8 directions + stay)

## Decision

### Module Structure

```
include/rl_project/
├── core/           # Core types
├── env/            # Environment (GameEnv, State, Action)
│   ├── types.h    # Constants and type definitions
│   ├── game_env.h  # Grid world environment
│   ├── state.h     # Agent's perception state
│   └── action.h    # Action definition
└── agent/          # RL agents (DQN)

src/rl_project/
├── env/            # Environment implementations
│   ├── game_env.cpp
│   └── state.cpp
├── agent/          # Agent implementations
│   └── dqn_agent.cpp
└── example/       # Usage examples with main()
```

### Grid World Configuration

- Size: 64×64 (configurable)
- Agent channel: 0 (blue)
- Food channel: 1 (green)
- Obstacle channels: 2-5 (red, 4 directions)
- State window: 33×33 with agent at center

### Action Space

9 discrete actions: ↑↗→↘↓↙←↖□

### Reward Design

- Eat food: +1
- Hit obstacle: -1
- Out of bounds: -2
- Default: 0

## Consequences

### Positive

- Clear separation between environment and agent
- Scalable to larger grids and more complex scenarios
- Easy to add new RL algorithms (A2C, PPO, etc.)

### Negative

- Simple linear Q-table (could use neural network later)
- Single-threaded training

## References

- 《我该干啥》之如何从零开始深度强化学习项目 (P0, P1)
- DQN algorithm