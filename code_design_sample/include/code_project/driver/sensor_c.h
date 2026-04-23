#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sensor_handle_t sensor_handle_t;

sensor_handle_t* sensor_create(void);
void sensor_destroy(sensor_handle_t* handle_p);

int32_t sensor_initialize(sensor_handle_t* handle_p);
int32_t sensor_deinitialize(sensor_handle_t* handle_p);

int32_t sensor_read_once(sensor_handle_t* handle_p,
                         int32_t* temperature_p,
                         int32_t* humidity_p,
                         uint32_t* timestamp_p);

int32_t sensor_set_address(sensor_handle_t* handle_p, uint8_t address);
uint8_t sensor_get_state(sensor_handle_t* handle_p);

#ifdef __cplusplus
}
#endif
