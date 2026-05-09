/**
 * @file sensor_impl.cpp
 * @brief 传感器驱动 Pimpl 实现
 * @note 位于 src/code_project/driver/ 目录下
 */

#include "sensor_impl.h"
#include "utils/sensor_types.h"
#include "protocol/i2c_bus_base.h"
#include <memory>

namespace code_project::driver {  // NOLINT

namespace {

/**
 * @brief 温度寄存器地址
 */
constexpr std::uint8_t reg_temperature_v {0x01};

/**
 * @brief 湿度寄存器地址
 */
constexpr std::uint8_t reg_humidity_v {0x02};

/**
 * @brief 状态寄存器地址
 */
constexpr std::uint8_t reg_status_v {0x03};

/**
 * @brief CRC 校验
 * @param[in] data 数据
 * @param[in] expected_crc 期望的 CRC 值
 * @return true 校验通过
 */
constexpr bool verify_crc(std::uint8_t data, std::uint8_t expected_crc) {
    return (data & 0xFF) == expected_crc;
}

}  // namespace

/**
 * @brief 传感器私有实现类
 * @details 隐藏 I2C 总线依赖，实现传感器数据读写
 */
class sensor_impl_t::sensor_priv_t {
public:
    /**
     * @brief 构造函数
     * @param[in] bus_p I2C 总线抽象指针
     */
    explicit sensor_priv_t(std::unique_ptr<i2c_bus_base_t> bus_p)
        : i2c_bus_p_(std::move(bus_p)) {}

    ~sensor_priv_t() = default;

    sensor_priv_t(const sensor_priv_t&) = delete;
    sensor_priv_t& operator=(const sensor_priv_t&) = delete;
    sensor_priv_t(sensor_priv_t&&) noexcept = default;
    sensor_priv_t& operator=(sensor_priv_t&&) noexcept = default;

    /**
     * @brief 初始化 I2C 总线和传感器
     * @return 状态码
     */
    core::status_t initialize() {
        if (!i2c_bus_p_) {
            return core::status_t::NULL_PTR;
        }

        std::uint8_t status {};
        auto result = i2c_bus_p_->read_reg(reg_status_v, status);
        if (core::is_error(result)) {
            return core::status_t::IO_FAILED;
        }

        if ((status & 0x01) == 0) {
            return core::status_t::DEVICE_ERROR;
        }

        return core::status_t::OK;
    }

    /**
     * @brief 读取传感器数据
     * @param[out] reading_s 读数结构体
     * @return 状态码
     */
    core::status_t read_data(sensor_reading_t& reading_s) {
        if (!i2c_bus_p_) {
            return core::status_t::NULL_PTR;
        }

        std::uint8_t temp_data[2] {};
        auto result = i2c_bus_p_->read_regs(reg_temperature_v, temp_data, 2);
        if (core::is_error(result)) {
            return result;
        }

        if (!verify_crc(temp_data[0], temp_data[1])) {
            return core::status_t::CRC_FAILED;
        }

        std::uint8_t hum_data[2] {};
        result = i2c_bus_p_->read_regs(reg_humidity_v, hum_data, 2);
        if (core::is_error(result)) {
            return result;
        }

        if (!verify_crc(hum_data[0], hum_data[1])) {
            return core::status_t::CRC_FAILED;
        }

        reading_s.temperature_centi_v = static_cast<std::int32_t>(temp_data[0]) * 100;
        reading_s.humidity_centi_v = static_cast<std::int32_t>(hum_data[0]) * 100;
        reading_s.timestamp_ms_v = 0;

        return core::status_t::OK;
    }

    sensor_config_t config_v {};  ///< 配置
    std::unique_ptr<i2c_bus_base_t> i2c_bus_p_;  ///< I2C 总线指针
};

/**
 * @brief 构造函数
 */
sensor_impl_t::sensor_impl_t()
    : p_impl_p_(nullptr) {}

/**
 * @brief 析构函数
 */
sensor_impl_t::~sensor_impl_t() = default;

/**
 * @brief 初始化传感器
 */
core::status_t sensor_impl_t::initialize() {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_v != sensor_state_t::IDLE) {
        if (state_v == sensor_state_t::INITIALIZED) {
            return core::status_t::ALREADY_INITIALIZED;
        }
        return core::status_t::INVALID_ARGUMENT;
    }

    auto status = p_impl_p_->initialize();
    if (core::is_error(status)) {
        state_v = sensor_state_t::ERROR_STATE;
        last_error_v = status;
        return status;
    }

    state_v = sensor_state_t::INITIALIZED;
    return core::status_t::OK;
}

/**
 * @brief 反初始化传感器
 */
core::status_t sensor_impl_t::deinitialize() {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_v == sensor_state_t::IDLE) {
        return core::status_t::OK;
    }

    p_impl_p_.reset();
    state_v = sensor_state_t::IDLE;
    last_error_v = core::status_t::OK;
    return core::status_t::OK;
}

/**
 * @brief 读取一次传感器数据
 */
core::status_t sensor_impl_t::read_once(sensor_reading_t& reading_s) {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_v != sensor_state_t::INITIALIZED && state_v != sensor_state_t::RUNNING) {
        return core::status_t::NOT_INITIALIZED;
    }

    auto result = p_impl_p_->read_data(reading_s);
    if (core::is_error(result)) {
        state_v = sensor_state_t::ERROR_STATE;
        last_error_v = result;
        return result;
    }

    state_v = sensor_state_t::RUNNING;
    return core::status_t::OK;
}

/**
 * @brief 设置传感器配置
 */
core::status_t sensor_impl_t::set_config(const sensor_config_t& config_s) {
    std::lock_guard<std::mutex> lock(state_mutex_);

    if (state_v == sensor_state_t::RUNNING) {
        return core::status_t::INVALID_ARGUMENT;
    }

    p_impl_p_->config_v = config_s;
    return core::status_t::OK;
}

/**
 * @brief 获取传感器状态
 */
sensor_state_t sensor_impl_t::get_state() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return state_v;
}

/**
 * @brief 获取最近错误码
 */
core::status_t sensor_impl_t::get_error() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return last_error_v;
}

}  // namespace code_project::driver
