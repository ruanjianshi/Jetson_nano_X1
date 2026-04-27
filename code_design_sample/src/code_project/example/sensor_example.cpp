/**
 * @file sensor_example.cpp
 * @brief 传感器驱动使用示例
 * @note 位于 src/code_project/example/ 目录下
 * @details 展示传感器驱动的典型使用方式，包含 main 函数
 */

#include "driver/sensor_impl.h"
#include "protocol/i2c_bus_base.h"
#include "utils/sensor_types.h"
#include "core/status.h"
#include <iostream>
#include <memory>

namespace code_project::example {  // NOLINT

namespace {

class fake_i2c_bus_t final : public protocol::i2c_bus_base_t {
public:
    core::status_t write_reg(std::uint8_t reg, std::uint8_t value) override {
        (void)reg;
        (void)value;
        return core::status_t::OK;
    }

    core::status_t read_reg(std::uint8_t reg, std::uint8_t& value) override {
        (void)reg;
        value = 0x03;
        return core::status_t::OK;
    }

    core::status_t read_regs(std::uint8_t reg, std::uint8_t* data_p, std::size_t len) override {
        (void)reg;
        if (data_p != nullptr && len >= 2) {
            data_p[0] = 25;
            data_p[1] = 25;
        }
        return core::status_t::OK;
    }
};

}  // namespace

void sensor_basic_usage() {
    auto i2c_bus_p = std::make_unique<fake_i2c_bus_t>();
    driver::sensor_impl_t sensor {};

    auto result = sensor.initialize();
    if (core::is_error(result)) {
        std::cerr << "Sensor init failed: " << static_cast<int>(result) << std::endl;
        return;
    }

    driver::sensor_reading_t reading {};
    result = sensor.read_once(reading);
    if (core::is_success(result)) {
        std::cout << "Temperature: " << reading.temperature_centi_v / 100.0 << " C" << std::endl;
        std::cout << "Humidity: " << reading.humidity_centi_v / 100.0 << " %" << std::endl;
    }

    sensor.deinitialize();
}

void sensor_with_config() {
    driver::sensor_impl_t sensor {};

    driver::sensor_config_t config {};
    config.i2c_address_v = 0x23;
    config.timeout_ms_v = 200;
    config.enable_avg_v = true;

    sensor.set_config(config);
    sensor.initialize();
    sensor.deinitialize();
}

}  // namespace code_project::example

/**
 * @brief 程序入口
 * @return 0 正常退出
 */
int main() {
    std::cout << "=== Sensor Basic Usage ===" << std::endl;
    code_project::example::sensor_basic_usage();

    std::cout << "\n=== Sensor With Config ===" << std::endl;
    code_project::example::sensor_with_config();

    return 0;
}