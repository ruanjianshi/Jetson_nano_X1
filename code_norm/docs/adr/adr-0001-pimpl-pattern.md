# ADR-0001: Use Pimpl Pattern for Driver Implementation

## Status
Accepted

## Context

We need to maintain stable ABI for our sensor driver while allowing implementation details to change frequently. We also want to hide heavy dependencies (like I2C HAL) from the public header.

## Decision

Use Pimpl pattern with the following rules:

- Public interface in `sensor_base_t` (abstract class)
- Implementation in `sensor_impl_t` (concrete class)
- Private details in `sensor_priv_t` (hidden in .cpp)
- Use `std::unique_ptr` for pimpl pointer
- Disable copying, enable move operations
- Define destructor in .cpp to allow forward declaration

## Module Structure

```
include/code_project/
├── core/           # Status codes, result types
├── driver/         # Device drivers (sensor_base.h, sensor_impl.h)
├── protocol/       # Communication protocols (i2c_bus_base.h)
└── utils/          # Common types (sensor_types.h)

src/code_project/
├── driver/         # Driver implementations
├── protocol/       # Protocol implementations
├── utils/          # Utility implementations
└── example/       # Usage examples
```

## Consequences

### Positive

- Stable ABI
- Fast compile times when implementation changes
- Hidden dependencies
- Clean separation of interface and implementation

### Negative

- Slight indirection overhead
- More boilerplate code

## References

- C++ Core Guidelines CP.41
- Effective Modern C++ Item 22