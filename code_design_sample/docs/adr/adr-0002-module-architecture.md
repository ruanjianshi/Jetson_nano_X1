# ADR-0002: Module Architecture

## Status
Accepted

## Context

We need a clear module structure that separates concerns and defines dependencies. The project must be maintainable, testable, and follow consistent naming conventions.

## Decision

Define four main modules with clear boundaries:

### Module Definitions

| Module | Purpose | Location | Dependencies |
|--------|---------|----------|--------------|
| `core` | Common types (status codes, result types) | `include/code_project/core/` | None |
| `utils` | Shared types used across modules | `include/code_project/utils/` | core |
| `protocol` | Communication protocol abstractions | `include/code_project/protocol/` | core |
| `driver` | Device driver implementations | `include/code_project/driver/` | core, utils, protocol |

### Dependency Direction

```
core → utils → protocol → driver
```

Rules:
- `core` has no dependencies (base layer)
- `utils` depends on `core`
- `protocol` depends on `core`
- `driver` depends on `core`, `utils`, `protocol`

### Directory Structure

```
project/
├── include/code_project/
│   ├── core/           # Status, result types
│   ├── utils/          # Shared types (sensor_types.h)
│   ├── protocol/       # Protocol interfaces (i2c_bus_base.h)
│   └── driver/         # Driver interfaces (sensor_base.h, sensor_impl.h)
├── src/code_project/
│   ├── core/
│   ├── utils/
│   ├── protocol/
│   ├── driver/         # Driver implementations
│   └── example/       # Usage examples
├── tests/code_project/
│   ├── core/
│   ├── driver/
│   └── protocol/
└── log/code_project/
    ├── core/
    ├── driver/
    ├── protocol/
    └── utils/
```

## Consequences

### Positive

- Clear separation of concerns
- Independent module development
- Easy to test with mocks
- Scalable structure for adding new modules

### Negative

- More directories to manage
- Potential circular dependency risk if rules not followed

## References

- CODING_STANDARDS.md Section 10
- Clean Architecture principles