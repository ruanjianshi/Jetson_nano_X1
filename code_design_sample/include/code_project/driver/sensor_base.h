#pragma once

/**
 * @file sensor_base.h
 * @brief 传感器驱动抽象接口
 * @note 位于 include/code_project/driver/ 目录下
 */

#include "utils/sensor_types.h"
#include "core/status.h"

namespace code_project::driver {  // NOLINT

/**
 * @brief 传感器驱动抽象基类
 * @details 定义传感器驱动的公共接口，使用抽象基类便于测试时使用 mock
 */
class sensor_base_t {
public:
    /**
     * @brief 虚析构函数
     */
    virtual ~sensor_base_t() = default;

    /**
     * @brief 初始化传感器
     * @return 状态码
     * @retval OK 成功
     * @retval NULL_PTR 空指针
     * @retval DEVICE_ERROR 设备错误
     */
    virtual core::status_t initialize() = 0;

    /**
     * @brief 反初始化传感器
     * @return 状态码
     */
    virtual core::status_t deinitialize() = 0;

    /**
     * @brief 读取一次传感器数据
     * @param[out] reading_s 读数结构体
     * @return 状态码
     * @retval OK 成功
     * @retval NOT_INITIALIZED 未初始化
     * @retval CRC_FAILED CRC 校验失败
     */
    virtual core::status_t read_once(sensor_reading_t& reading_s) = 0;

    /**
     * @brief 设置传感器配置
     * @param[in] config_s 配置结构体
     * @return 状态码
     */
    virtual core::status_t set_config(const sensor_config_t& config_s) = 0;

    /**
     * @brief 获取传感器状态
     * @return 传感器状态
     */
    virtual sensor_state_t get_state() const = 0;

    /**
     * @brief 获取最近错误码
     * @return 错误码
     */
    virtual core::status_t get_error() const = 0;
};

}  // namespace code_project::driver
