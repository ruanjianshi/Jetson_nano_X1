/**
 * @file sensor_test.cpp
 * @brief 传感器驱动单元测试
 * @note 位于 tests/code_project/driver/ 目录下
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "driver/sensor_impl.h"
#include "protocol/i2c_bus_base.h"

namespace {  // NOLINT

using code_project::core::status_t;
using code_project::driver::sensor_impl_t;
using code_project::driver::sensor_reading_t;
using code_project::driver::sensor_state_t;

/**
 * @brief Mock I2C 总线类
 * @details 用于测试的 I2C 总线模拟实现
 */
class mock_i2c_bus_t : public code_project::driver::i2c_bus_base_t {
public:
    MOCK_METHOD(status_t, write_reg, (std::uint8_t reg, std::uint8_t value), (override));
    MOCK_METHOD(status_t, read_reg, (std::uint8_t reg, std::uint8_t& value), (override));
    MOCK_METHOD(status_t, read_regs, (std::uint8_t reg, std::uint8_t* data_p, std::size_t len), (override));
};

/**
 * @brief 传感器测试 fixture
 * @details 提供传感器测试的公共设置和资源
 */
class sensor_test_t : public ::testing::Test {
protected:
    /**
     * @brief 测试初始化
     */
    void SetUp() override {
        mock_bus_p_ = std::make_unique<mock_i2c_bus_t>();
    }

    std::unique_ptr<mock_i2c_bus_t> mock_bus_p_;  ///< Mock I2C 总线指针
};

/**
 * @brief 测试：初始化成功
 * @details 验证在 I2C 总线正常时初始化成功
 */
TEST_F(sensor_test_t, initialize_success) {
    EXPECT_CALL(*mock_bus_p_, read_reg(testing::_, testing::_))
        .WillOnce(testing::DoAll(
            testing::SetArgReferee<1>(0x03),
            testing::Return(status_t::OK)));

    sensor_impl_t sensor {};
    auto result = sensor.initialize();

    EXPECT_TRUE(code_project::core::is_success(result));
    EXPECT_EQ(sensor.get_state(), sensor_state_t::INITIALIZED);
}

/**
 * @brief 测试：初始化空总线
 * @details 验证当 I2C 总线为空时返回错误
 */
TEST_F(sensor_test_t, initialize_null_bus) {
    sensor_impl_t sensor {};
    auto result = sensor.initialize();

    EXPECT_TRUE(code_project::core::is_error(result));
}

/**
 * @brief 测试：设备错误
 * @details 验证当设备返回错误时初始化失败
 */
TEST_F(sensor_test_t, initialize_device_error) {
    EXPECT_CALL(*mock_bus_p_, read_reg(testing::_, testing::_))
        .WillOnce(testing::Return(status_t::DEVICE_ERROR));

    sensor_impl_t sensor {};
    auto result = sensor.initialize();

    EXPECT_TRUE(code_project::core::is_error(result));
    EXPECT_EQ(sensor.get_error(), status_t::DEVICE_ERROR);
}

/**
 * @brief 测试：读取成功
 * @details 验证初始化后读取数据成功
 */
TEST_F(sensor_test_t, read_once_success) {
    EXPECT_CALL(*mock_bus_p_, read_reg(testing::_, testing::_))
        .WillOnce(testing::DoAll(
            testing::SetArgReferee<1>(0x03),
            testing::Return(status_t::OK)));

    EXPECT_CALL(*mock_bus_p_, read_regs(testing::_, testing::_, testing::_))
        .WillOnce(testing::Return(status_t::OK));

    sensor_impl_t sensor {};
    sensor.initialize();

    sensor_reading_t reading {};
    auto result = sensor.read_once(reading);

    EXPECT_TRUE(code_project::core::is_success(result));
}

/**
 * @brief 测试：未初始化时读取
 * @details 验证未初始化时调用读取返回 NOT_INITIALIZED
 */
TEST_F(sensor_test_t, read_once_not_initialized) {
    sensor_impl_t sensor {};

    sensor_reading_t reading {};
    auto result = sensor.read_once(reading);

    EXPECT_TRUE(code_project::core::is_error(result));
    EXPECT_EQ(result, status_t::NOT_INITIALIZED);
}

/**
 * @brief 测试：空闲状态反初始化
 * @details 验证对空闲状态传感器反初始化成功
 */
TEST_F(sensor_test_t, deinitialize_idle_sensor) {
    sensor_impl_t sensor {};
    auto result = sensor.deinitialize();

    EXPECT_TRUE(code_project::core::is_success(result));
    EXPECT_EQ(sensor.get_state(), sensor_state_t::IDLE);
}

/**
 * @brief 测试：状态线程安全
 * @details 验证多线程并发访问状态不会崩溃
 */
TEST_F(sensor_test_t, state_thread_safety) {
    sensor_impl_t sensor {};

    std::atomic<bool> running {true};
    std::vector<std::thread> threads;

    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() {
            while (running.load()) {
                volatile auto state = sensor.get_state();
                (void)state;
            }
        });
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    running = false;

    for (auto& t : threads) {
        t.join();
    }
}

}  // namespace