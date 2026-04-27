# Architecture Decision Records (ADR)

本文档记录项目中的重要架构决策。

## ADR 索引

| ID | 标题 | 状态 | 日期 |
|----|------|------|------|
| [ADR-0001](./adr-0001-pimpl-pattern.md) | Use Pimpl Pattern for Driver Implementation | Accepted | 2026-04-23 |
| [ADR-0002](./adr-0002-module-architecture.md) | Module Architecture | Accepted | 2026-04-27 |
| [ADR-0003](./adr-0003-reinforcement-learning.md) | Reinforcement Learning Module (rl_project) | Accepted | 2026-04-27 |

## 如何添加 ADR

1. 在 `docs/adr/` 目录下创建 `adr-NNNN-title.md` 文件
2. 使用本模板的格式（Status, Context, Decision, Consequences）
3. 更新本索引表

## ADR 模板

```markdown
# ADR-NNNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
描述问题和背景

## Decision
描述做出的决策

## Consequences
### Positive
### Negative
```