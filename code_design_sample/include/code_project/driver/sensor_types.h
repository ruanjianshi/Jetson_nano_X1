#pragma once

#include <cstdint>

namespace code_project::driver {

enum class sensor_err_t : std::int32_t {
    OK = 0,
    NULL_PTR = -1,
    NOT_INITIALIZED = -2,
    ALREADY_INITIALIZED = -3,
    I2C_FAILED = -4,
    CRC_FAILED = -5,
    TIMEOUT = -6,
    INVALID_ARGUMENT = -7,
    DEVICE_ERROR = -8
};

enum class sensor_state_t : std::uint8_t {
    IDLE = 0,
    INITIALIZED,
    RUNNING,
    ERROR_STATE
};

struct sensor_config_t {
    std::uint8_t i2c_address_v {0x23};
    std::uint32_t timeout_ms_v {100};
    bool enable_avg_v {true};
};

struct sensor_reading_t {
    std::int32_t temperature_centi_v {0};
    std::int32_t humidity_centi_v {0};
    std::uint32_t timestamp_ms_v {0};
};

}  // namespace code_project::driver
