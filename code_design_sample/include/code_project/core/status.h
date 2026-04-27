#pragma once

/**
 * @file status.h
 * @brief 通用状态码定义
 * @note 位于 include/code_project/core/ 目录下
 */

#include <cstdint>

namespace code_project::core {  // NOLINT

/**
 * @brief 通用状态码枚举
 * @note 所有模块共享此状态码定义
 */
enum class status_t : std::int32_t {
    OK = 0,               ///< 成功
    NULL_PTR = -1,        ///< 空指针错误
    NOT_INITIALIZED = -2, ///< 未初始化
    ALREADY_INITIALIZED = -3,   ///< 已初始化
    INVALID_ARGUMENT = -4,       ///< 无效参数
    IO_FAILED = -5,              ///< IO 操作失败
    TIMEOUT = -6,               ///< 操作超时
    CRC_FAILED = -7,            ///< CRC 校验失败
    BUFFER_OVERFLOW = -8,       ///< 缓冲区溢出
    DEVICE_ERROR = -9           ///< 设备错误
};

/**
 * @brief 判断状态是否为成功
 * @param[in] status 状态码
 * @return true 成功，false 失败
 */
constexpr bool is_success(status_t status) {
    return status == status_t::OK;
}

/**
 * @brief 判断状态是否为错误
 * @param[in] status 状态码
 * @return true 错误，false 成功
 */
constexpr bool is_error(status_t status) {
    return !is_success(status);
}

}  // namespace code_project::core
