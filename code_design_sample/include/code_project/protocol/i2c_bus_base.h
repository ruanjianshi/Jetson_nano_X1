#pragma once

/**
 * @file i2c_bus_base.h
 * @brief I2C 总线抽象接口
 * @note 位于 include/code_project/protocol/ 目录下
 */

#include <cstdint>
#include <functional>

namespace code_project::driver {  // NOLINT

/**
 * @brief 数据就绪回调类型
 * @param temperature_v 温度值(百分度)
 * @param humidity_v 湿度值(百分度)
 */
using data_ready_cb_t = std::function<void(std::int32_t temperature_v, std::int32_t humidity_v)>;

/**
 * @brief I2C 总线抽象接口
 * @details 定义 I2C 寄存器读写操作，具体实现由子类提供
 */
class i2c_bus_base_t {
public:
    /**
     * @brief 虚析构函数
     */
    virtual ~i2c_bus_base_t() = default;

    /**
     * @brief 写入单个寄存器
     * @param[in] reg 寄存器地址
     * @param[in] value 写入值
     * @return 状态码
     */
    virtual core::status_t write_reg(std::uint8_t reg, std::uint8_t value) = 0;

    /**
     * @brief 读取单个寄存器
     * @param[in] reg 寄存器地址
     * @param[out] value 读取值
     * @return 状态码
     */
    virtual core::status_t read_reg(std::uint8_t reg, std::uint8_t& value) = 0;

    /**
     * @brief 读取多个寄存器
     * @param[in] reg 起始寄存器地址
     * @param[out] data_p 数据缓冲区
     * @param[in] len 读取长度
     * @return 状态码
     */
    virtual core::status_t read_regs(std::uint8_t reg, std::uint8_t* data_p, std::size_t len) = 0;
};

}  // namespace code_project::driver
