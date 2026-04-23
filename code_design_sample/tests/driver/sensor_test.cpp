#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "sensor_impl.h"
#include "i2c_bus_base.h"

namespace {

using code_project::core::status_t;
using code_project::driver::sensor_impl_t;
using code_project::driver::sensor_reading_t;
using code_project::driver::sensor_state_t;

class mock_i2c_bus_t : public code_project::driver::i2c_bus_base_t {
public:
    MOCK_METHOD(status_t, write_reg, (std::uint8_t reg, std::uint8_t value), (override));
    MOCK_METHOD(status_t, read_reg, (std::uint8_t reg, std::uint8_t& value), (override));
    MOCK_METHOD(status_t, read_regs, (std::uint8_t reg, std::uint8_t* data_p, std::size_t len), (override));
};

class sensor_test_t : public ::testing::Test {
protected:
    void SetUp() override {
        mock_bus_p_ = std::make_unique<mock_i2c_bus_t>();
    }

    std::unique_ptr<mock_i2c_bus_t> mock_bus_p_;
};

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

TEST_F(sensor_test_t, initialize_null_bus) {
    sensor_impl_t sensor {};
    auto result = sensor.initialize();

    EXPECT_TRUE(code_project::core::is_error(result));
}

TEST_F(sensor_test_t, initialize_device_error) {
    EXPECT_CALL(*mock_bus_p_, read_reg(testing::_, testing::_))
        .WillOnce(testing::Return(status_t::DEVICE_ERROR));

    sensor_impl_t sensor {};
    auto result = sensor.initialize();

    EXPECT_TRUE(code_project::core::is_error(result));
    EXPECT_EQ(sensor.get_error(), status_t::DEVICE_ERROR);
}

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

TEST_F(sensor_test_t, read_once_not_initialized) {
    sensor_impl_t sensor {};

    sensor_reading_t reading {};
    auto result = sensor.read_once(reading);

    EXPECT_TRUE(code_project::core::is_error(result));
    EXPECT_EQ(result, status_t::NOT_INITIALIZED);
}

TEST_F(sensor_test_t, deinitialize_idle_sensor) {
    sensor_impl_t sensor {};
    auto result = sensor.deinitialize();

    EXPECT_TRUE(code_project::core::is_success(result));
    EXPECT_EQ(sensor.get_state(), sensor_state_t::IDLE);
}

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
