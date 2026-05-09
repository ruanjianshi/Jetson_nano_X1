# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-04-23

### Added
- Initial project structure
- Core layer (status codes, result types)
- Driver layer with sensor example
  - Base class interface (sensor_base_t)
  - Pimpl implementation (sensor_impl_t)
  - C-compatible interface (sensor_c.h)
  - I2C bus abstraction for testing
- Unit tests with GoogleTest/GoogleMock
- .clang-format configuration
- .clang-tidy configuration
- CONTRIBUTING.md guidelines
