#pragma once

#include <cstdint>

namespace code_project::core {

enum class status_t : std::int32_t {
    OK = 0,
    NULL_PTR = -1,
    NOT_INITIALIZED = -2,
    ALREADY_INITIALIZED = -3,
    INVALID_ARGUMENT = -4,
    IO_FAILED = -5,
    TIMEOUT = -6,
    CRC_FAILED = -7,
    BUFFER_OVERFLOW = -8,
    DEVICE_ERROR = -9
};

constexpr bool is_success(status_t status) {
    return status == status_t::OK;
}

constexpr bool is_error(status_t status) {
    return !is_success(status);
}

}  // namespace code_project::core
