# C++ Code Design Sample

> **参考**: C++ 代码设计与工程开发规范 (CODING_STANDARDS.md v3.0.0)

本项目是代码设计规范的示例实现，AI 可通过阅读本项目理解规范要求。

## 项目结构

```
code_design_sample/
├── include/
│   ├── code_project/           # 嵌入式/驱动项目示例
│   │   ├── core/               # 状态码(status.h)、结果类型(result.h)
│   │   ├── driver/            # 设备驱动：sensor_base.h, sensor_impl.h
│   │   ├── protocol/           # 通信协议：i2c_bus_base.h
│   │   ├── utils/             # 公共类型：sensor_types.h
│   │   └── version.h
│   └── rl_project/             # 强化学习项目示例
│       ├── core/
│       ├── env/               # 环境：grid_world.h, q_learning.h
│       ├── agent/
│       └── utils/
├── src/
│   ├── code_project/
│   │   ├── driver/
│   │   ├── example/            # sensor_example.cpp（含 main）
│   │   └── ...
│   └── rl_project/
│       ├── env/
│       ├── example/            # rl_example.cpp（含 main）
│       └── ...
├── tests/
│   ├── code_project/
│   └── rl_project/
├── log/
│   ├── code_project/
│   └── rl_project/
├── docs/
│   ├── adr/                   # 架构决策记录
│   └── LOGGING_STANDARDS.md
├── CODING_STANDARDS.md
├── CLAUDE.md
└── README.md
```

## 模块说明

### code_project (嵌入式/驱动示例)

| 模块 | 说明 | 依赖 |
|------|------|------|
| `core` | 通用状态码、结果类型 | 无 |
| `utils` | 共享类型定义 | core |
| `protocol` | 通信协议抽象 | core |
| `driver` | 设备驱动实现 | core, utils, protocol |

### rl_project (强化学习示例)

| 模块 | 说明 | 依赖 |
|------|------|------|
| `core` | 核心类型 | 无 |
| `env` | 环境（网格世界） | core |
| `agent` | 智能体（Q-Learning, SARSA） | env |
| `utils` | 工具类型 | core |

## 核心特性

1. **Core Layer** - 统一状态码 (`status_t`)、结果类型 (`result_t`)
2. **Driver Layer** - 传感器驱动：
   - `sensor_base_t` - 抽象接口
   - `sensor_impl_t` - Pimpl 实现
3. **Protocol Layer** - I2C 总线抽象 (`i2c_bus_base_t`)
4. **Utils Layer** - 公共类型 (`sensor_types.h`)
5. **RL Layer** - 强化学习：
   - `grid_world_env_t` - 网格世界环境
   - `q_learning_t` - Q-Learning 智能体
   - `sarsa_t` - SARSA 智能体
6. **Examples** - 驱动使用示例（含 main 函数）
7. **Tests** - GoogleTest 单元测试

## 设计模式

- **Pimpl 惯用法**: 隐藏实现细节，稳定 ABI
- **RAII**: 资源管理
- **抽象基类**: 接口与实现分离，便于测试
- **依赖注入**: 便于 mock

## 命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 类型 | `_t` 后缀 | `status_t`, `sensor_state_t` |
| 实现类 | `_impl_t` 后缀 | `sensor_impl_t` |
| 基类 | `_base_t` 后缀 | `sensor_base_t` |
| 私有类 | `_priv_t` 后缀 | `sensor_priv_t` |
| 变量 | `_v` 后缀 | `state_v`, `timeout_ms_v` |
| 指针 | `_p` 后缀 | `i2c_bus_p_` |
| 常量 | `k` 前缀 | `kActionCount`, `kGridSize` |

## 文档

- [CODING_STANDARDS.md](./CODING_STANDARDS.md) - 代码规范
- [CLAUDE.md](./CLAUDE.md) - AI 开发指南
- [LOGGING_STANDARDS.md](./docs/LOGGING_STANDARDS.md) - 日志规范
- [ADR](./docs/adr/) - 架构决策记录

## ADR 索引

| ID | 标题 |
|----|------|
| ADR-0001 | Pimpl Pattern for Driver Implementation |
| ADR-0002 | Module Architecture |
| ADR-0003 | Reinforcement Learning Module (rl_project) |