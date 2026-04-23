Based on Your: C++ Code Design and Engineering Development Guidelines (Optimized Version)

I need to build a sample code library that AI can read to understand the specification

The project structure is as follows:
```
code_design_sample/
├── include/code_project/
│   ├── core/
│   │   ├── status.h           ✅
│   │   └── result.h          ✅
│   ├── driver/
│   │   ├── sensor_types.h     ✅
│   │   ├── sensor_base.h     ✅
│   │   ├── sensor_impl.h     ✅
│   │   ├── sensor_c.h        ✅
│   │   └── i2c_bus_base.h    ✅
│   ├── protocol/
│   ├── utils/
│   └── version.h              ✅
├── src/
│   ├── driver/
│   │   ├── sensor_impl.cpp   ✅
│   │   └── sensor_c.cpp      ✅
│   └── ...
├── tests/
│   └── driver/
│       └── sensor_test.cpp   ✅
├── cmake/
├── docs/adr/
├── CMakeLists.txt            ✅
└── .clang-format
```

## Key Features

1. **Core Layer** - Status codes, result types
2. **Driver Layer** - Sensor driver with:
   - Base class interface (sensor_base_t)
   - Pimpl implementation (sensor_impl_t)
   - C-compatible interface (sensor_c.h)
   - Mock-able I2C bus abstraction
3. **Tests** - GoogleTest unit tests with mocks

## How AI Can Learn from This

The sample code demonstrates:
- `_t` naming convention for types
- `enum class` for error codes and states
- RAII resource management
- Pimpl pattern for ABI stability
- Thread-safe state management
- C++ and C interface separation
- Dependency injection for testability
- Unit testing with mocks

Would you like me to continue creating more examples (protocol layer, utils, etc.) or add additional CI configuration files (.clang-format, .clang-tidy)?
