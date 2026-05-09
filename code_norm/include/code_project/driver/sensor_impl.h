#pragma once

/**
 * @file sensor_impl.h
 * @brief 传感器驱动 Pimpl 实现类声明
 * @note 位于 include/code_project/driver/ 目录下
 */

#include "sensor_base.h"
#include "utils/sensor_types.h"
#include <memory>
#include <mutex>

namespace code_project::driver {  // NOLINT

/**
 * @brief 传感器驱动 Pimpl 实现类
 * @details 使用 Pimpl 模式隐藏 I2C 依赖，隔离编译
 */
class sensor_impl_t final : public sensor_base_t {
public:
    /**
     * @brief 构造函数
     */
    sensor_impl_t();

    /**
     * @brief 析构函数
     */
    ~sensor_impl_t() override;

    sensor_impl_t(const sensor_impl_t&) = delete;
    sensor_impl_t& operator=(const sensor_impl_t&) = delete;
    sensor_impl_t(sensor_impl_t&&) noexcept = default;
    sensor_impl_t& operator=(sensor_impl_t&&) noexcept = default;

    /**
     * @brief 初始化传感器
     * @return 状态码
     * @retval OK 成功
     * @retval ALREADY_INITIALIZED 已初始化
     * @retval NULL_PTR 空指针错误
     */
    core::status_t initialize() override;

    /**
     * @brief 反初始化传感器
     * @return 状态码
     */
    core::status_t deinitialize() override;

    /**
     * @brief 读取一次传感器数据
     * @param[out] reading_s 读数结构体
     * @return 状态码
     */
    core::status_t read_once(sensor_reading_t& reading_s) override;

    /**
     * @brief 设置传感器配置
     * @param[in] config_s 配置结构体
     * @return 状态码
     */
    core::status_t set_config(const sensor_config_t& config_s) override;

    /**
     * @brief 获取传感器状态
     * @return 传感器状态
     */
    sensor_state_t get_state() const override;

    /**
     * @brief 获取最近错误码
     * @return 错误码
     */
    core::status_t get_error() const override;

private:
    class sensor_priv_t;  ///< 私有实现类
    std::unique_ptr<sensor_priv_t> p_impl_p;  ///< Pimpl 指针

    mutable std::mutex state_mutex_;  ///< 状态锁
    sensor_state_t state_v {sensor_state_t::IDLE};  ///< 当前状态
    core::status_t last_error_v {core::status_t::OK};  ///< 最近错误码
};

}  // namespace code_project::driver
