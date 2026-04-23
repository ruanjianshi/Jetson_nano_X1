#pragma once

#include "sensor_types.h"
#include "../../core/status.h"

namespace code_project::driver {

class sensor_base_t {
public:
    virtual ~sensor_base_t() = default;

    virtual core::status_t initialize() = 0;
    virtual core::status_t deinitialize() = 0;
    virtual core::status_t read_once(sensor_reading_t& reading_s) = 0;
    virtual core::status_t set_config(const sensor_config_t& config_s) = 0;
    virtual sensor_state_t get_state() const = 0;
    virtual core::status_t get_error() const = 0;
};

}  // namespace code_project::driver
