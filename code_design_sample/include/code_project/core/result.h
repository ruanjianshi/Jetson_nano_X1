#pragma once

/**
 * @file result.h
 * @brief 结果类型模板
 * @note 位于 include/code_project/core/ 目录下
 */

#include <cstdint>
#include <limits>

namespace code_project::core {  // NOLINT

/**
 * @brief 结果类型模板类
 * @tparam T 值类型
 * @details 用于替代异常处理，统一错误返回方式
 */
template<typename T>
class result_t {
public:
    using value_type = T;    ///< 值类型别名
    using error_type = std::int32_t;  ///< 错误类型别名

    result_t() = delete;

    /**
     * @brief 构造成功结果
     * @param[in] value 值
     */
    constexpr result_t(T value) noexcept
        : value_(value), error_(0), has_value_(true) {}

    /**
     * @brief 构造错误结果
     * @param[in] error 错误码
     */
    constexpr result_t(error_type error) noexcept
        : value_{}, error_(error), has_value_(false) {}

    /**
     * @brief 是否有值
     * @return true 有值，false 无值
     */
    constexpr bool has_value() const noexcept { return has_value_; }

    /**
     * @brief 布尔转换
     * @return true 有值，false 无值
     */
    constexpr explicit operator bool() const noexcept { return has_value_; }

    /**
     * @brief 获取值（左值引用）
     * @return 值引用
     */
    constexpr const T& value() const& {
        return value_;
    }

    /**
     * @brief 获取值（左值引用）
     * @return 值引用
     */
    constexpr T& value() & {
        return value_;
    }

    /**
     * @brief 获取错误码
     * @return 错误码
     */
    constexpr error_type error() const noexcept { return error_; }

    constexpr const T* operator->() const { return &value_; }
    constexpr T* operator->() { return &value_; }

    constexpr const T& operator*() const& { return value_; }
    constexpr T& operator*() & { return value_; }

private:
    T value_;
    error_type error_;
    bool has_value_;
};

/**
 * @brief void 类型结果特化
 */
template<>
class result_t<void> {
public:
    using error_type = std::int32_t;

    result_t() noexcept : error_(0), has_value_(true) {}
    constexpr result_t(error_type error) noexcept : error_(error), has_value_(false) {}

    constexpr bool has_value() const noexcept { return has_value_; }
    constexpr explicit operator bool() const noexcept { return has_value_; }
    constexpr error_type error() const noexcept { return error_; }

private:
    error_type error_;
    bool has_value_;
};

}  // namespace code_project::core
