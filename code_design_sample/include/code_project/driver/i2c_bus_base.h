#pragma once

#include <cstdint>
#include <functional>

namespace code_project::driver {

using data_ready_cb_t = std::function<void(std::int32_t temperature_v, std::int32_t humidity_v)>;

class i2c_bus_base_t {
public:
    virtual ~i2c_bus_base_t() = default;

    virtual core::status_t write_reg(std::uint8_t reg, std::uint8_t value) = 0;
    virtual core::status_t read_reg(std::uint8_t reg, std::uint8_t& value) = 0;
    virtual core::status_t read_regs(std::uint8_t reg, std::uint8_t* data_p, std::size_t len) = 0;
};

}  // namespace code_project::driver
