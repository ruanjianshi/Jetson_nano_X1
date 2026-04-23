#pragma once

#include "sensor_base.h"
#include <memory>
#include <mutex>

namespace code_project::driver {

class sensor_impl_t final : public sensor_base_t {
public:
    sensor_impl_t();
    ~sensor_impl_t() override;

    sensor_impl_t(const sensor_impl_t&) = delete;
    sensor_impl_t& operator=(const sensor_impl_t&) = delete;
    sensor_impl_t(sensor_impl_t&&) noexcept = default;
    sensor_impl_t& operator=(sensor_impl_t&&) noexcept = default;

    core::status_t initialize() override;
    core::status_t deinitialize() override;
    core::status_t read_once(sensor_reading_t& reading_s) override;
    core::status_t set_config(const sensor_config_t& config_s) override;
    sensor_state_t get_state() const override;
    core::status_t get_error() const override;

private:
    class sensor_priv_t;
    std::unique_ptr<sensor_priv_t> p_impl_p;

    mutable std::mutex state_mutex_;
    sensor_state_t state_v {sensor_state_t::IDLE};
    core::status_t last_error_v {core::status_t::OK};
};

}  // namespace code_project::driver
