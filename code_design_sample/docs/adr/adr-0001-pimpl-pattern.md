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
