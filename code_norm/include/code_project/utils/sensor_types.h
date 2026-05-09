#pragma once

/**
 * @file sensor_types.h
 * @brief 传感器驱动类型定义
 * @note 位于 include/code_project/utils/ 目录下
 */

#include <cstdint>

namespace code_project::driver {  // NOLINT

/**
 * @brief 传感器错误码
 */
enum class sensor_err_t : std::int32_t {
    OK = 0,                 ///< 成功
    NULL_PTR = -1,         ///< 空指针错误
    NOT_INITIALIZED = -2,  ///< 未初始化
    ALREADY_INITIALIZED = -3,  ///< 已初始化
    I2C_FAILED = -4,       ///< I2C 操作失败
    CRC_FAILED = -5,       ///< CRC 校验失败
    TIMEOUT = -6,          ///< 操作超时
    INVALID_ARGUMENT = -7, ///< 无效参数
    DEVICE_ERROR = -8     ///< 设备错误
};

/**
 * @brief 传感器状态
 */
enum class sensor_state_t : std::uint8_t {
    IDLE = 0,          ///< 空闲状态
    INITIALIZED,       ///< 已初始化
    RUNNING,           ///< 运行中
    ERROR_STATE        ///< 错误状态
};

/**
 * @brief 传感器配置结构体
 */
struct sensor_config_t {
    std::uint8_t i2c_address_v {0x23};  ///< I2C 地址，默认 0x23
    std::uint32_t timeout_ms_v {100};   ///< 超时时间(ms)
    bool enable_avg_v {true};           ///< 是否启用均值滤波
};

/**
 * @brief 传感器读数结构体
 * @note 温度和湿度单位为百分度，例如 2500 表示 25.00°C
 */
struct sensor_reading_t {
    std::int32_t temperature_centi_v {0};  ///< 温度(百分度)
    std::int32_t humidity_centi_v {0};      ///< 湿度(百分度)
    std::uint32_t timestamp_ms_v {0};       ///< 时间戳(ms)
};

}  // namespace code_project::driver
