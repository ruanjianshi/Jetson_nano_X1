#pragma once

#include <cstdint>
#include <limits>

namespace code_project::core {

template<typename T>
class result_t {
public:
    using value_type = T;
    using error_type = std::int32_t;

    result_t() = delete;

    constexpr result_t(T value) noexcept
        : value_(value), error_(0), has_value_(true) {}

    constexpr result_t(error_type error) noexcept
        : value_{}, error_(error), has_value_(false) {}

    constexpr bool has_value() const noexcept { return has_value_; }
    constexpr explicit operator bool() const noexcept { return has_value_; }

    constexpr const T& value() const& {
        return value_;
    }

    constexpr T& value() & {
        return value_;
    }

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
