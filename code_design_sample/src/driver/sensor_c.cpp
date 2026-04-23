#include "sensor_c.h"
#include "sensor_impl.h"
#include <cstdlib>
#include <cstring>

namespace {

constexpr std::size_t handle_magic_v {0xDEADBEEF};

struct sensor_handle_t {
    std::size_t magic;
    code_project::driver::sensor_impl_t* impl_p;
};

}

sensor_handle_t* sensor_create(void) {
    auto* handle_p = static_cast<sensor_handle_t*>(std::malloc(sizeof(sensor_handle_t)));
    if (handle_p == nullptr) {
        return nullptr;
    }

    std::memset(handle_p, 0, sizeof(sensor_handle_t));
    handle_p->magic = handle_magic_v;
    handle_p->impl_p = new (std::nothrow) code_project::driver::sensor_impl_t();

    if (handle_p->impl_p == nullptr) {
        std::free(handle_p);
        return nullptr;
    }

    return handle_p;
}

void sensor_destroy(sensor_handle_t* handle_p) {
    if (handle_p == nullptr) {
        return;
    }

    if (handle_p->magic != handle_magic_v) {
        return;
    }

    delete handle_p->impl_p;
    handle_p->impl_p = nullptr;
    handle_p->magic = 0;

    std::free(handle_p);
}

int32_t sensor_initialize(sensor_handle_t* handle_p) {
    if (handle_p == nullptr || handle_p->impl_p == nullptr) {
        return static_cast<int32_t>(code_project::core::status_t::NULL_PTR);
    }

    auto result = handle_p->impl_p->initialize();
    return static_cast<int32_t>(result);
}

int32_t sensor_deinitialize(sensor_handle_t* handle_p) {
    if (handle_p == nullptr || handle_p->impl_p == nullptr) {
        return static_cast<int32_t>(code_project::core::status_t::NULL_PTR);
    }

    auto result = handle_p->impl_p->deinitialize();
    return static_cast<int32_t>(result);
}

int32_t sensor_read_once(sensor_handle_t* handle_p,
                         int32_t* temperature_p,
                         int32_t* humidity_p,
                         uint32_t* timestamp_p) {
    if (handle_p == nullptr || handle_p->impl_p == nullptr) {
        return static_cast<int32_t>(code_project::core::status_t::NULL_PTR);
    }

    code_project::driver::sensor_reading_t reading {};
    auto result = handle_p->impl_p->read_once(reading);

    if (code_project::core::is_error(result)) {
        return static_cast<int32_t>(result);
    }

    if (temperature_p != nullptr) {
        *temperature_p = reading.temperature_centi_v;
    }
    if (humidity_p != nullptr) {
        *humidity_p = reading.humidity_centi_v;
    }
    if (timestamp_p != nullptr) {
        *timestamp_p = reading.timestamp_ms_v;
    }

    return static_cast<int32_t>(code_project::core::status_t::OK);
}

int32_t sensor_set_address(sensor_handle_t* handle_p, uint8_t address) {
    (void)handle_p;
    (void)address;
    return 0;
}

uint8_t sensor_get_state(sensor_handle_t* handle_p) {
    if (handle_p == nullptr || handle_p->impl_p == nullptr) {
        return 0xFF;
    }

    auto state = handle_p->impl_p->get_state();
    return static_cast<uint8_t>(state);
}
