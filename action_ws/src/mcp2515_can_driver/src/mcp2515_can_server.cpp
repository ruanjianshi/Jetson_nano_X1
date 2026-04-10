#include <ros/ros.h>
#include <actionlib/server/simple_action_server.h>
#include <mcp2515_can_driver/MCP2515CANCommAction.h>
#include <iostream>
#include <iomanip>
#include <cstring>
#include <atomic>
#include <iomanip>
#include "mcp2515_driver.h"

class MCP2515CANServer
{
protected:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<mcp2515_can_driver::MCP2515CANCommAction> as_;
    std::string action_name_;
    MCP2515Driver* driver_;
    bool enable_rx_thread_;
    bool enable_echo_;
    bool loopback_test_;
    std::thread* rx_thread_;
    bool rx_thread_running_;

public:
    MCP2515CANServer(const std::string& name, MCP2515Driver* driver)
        : as_(nh_, name, boost::bind(&MCP2515CANServer::executeCB, this, _1), false),
          action_name_(name),
          driver_(driver),
          rx_thread_(nullptr),
          rx_thread_running_(false),
          rx_count_(0),
          last_rx_time_(0.0),
          rx_rate_(0.0)
    {
        nh_.param("enable_rx_thread", enable_rx_thread_, true);
        nh_.param("enable_echo", enable_echo_, true);
        nh_.param("loopback_test", loopback_test_, false);

        if (enable_echo_) {
            driver_->setReceiveCallback([this](uint32_t id, const uint8_t* data,
                                                uint8_t dlc, bool extended, bool remote) {
                this->onCANFrameReceived(id, data, dlc, extended, remote);
            });
        }

        as_.start();
        ROS_INFO("OK: MCP2515 CAN Action Server started");
        ROS_INFO("   Action name: %s", action_name_.c_str());
        ROS_INFO("   RX thread: %s", enable_rx_thread_ ? "Enabled" : "Disabled");
        ROS_INFO("   Echo: %s", enable_echo_ ? "Enabled" : "Disabled");
    }

    ~MCP2515CANServer()
    {
        stopRxThread();
    }

    void startRxThread()
    {
        if (enable_rx_thread_) {
            driver_->startRxThread();
            rx_thread_running_ = true;
            rx_thread_ = new std::thread([this]() {
                this->rxLoop();
            });
            ROS_INFO("OK: RX thread started");
        }
    }

    void stopRxThread()
    {
        if (rx_thread_ != nullptr) {
            rx_thread_running_ = false;
            if (rx_thread_->joinable()) {
                rx_thread_->join();
            }
            delete rx_thread_;
            rx_thread_ = nullptr;
        }
    }

    void runLoopbackTest()
    {
        ROS_INFO("Running loopback test...");
        stopRxThread();

        if (driver_->loopbackTest(0x123, nullptr, 4)) {
            ROS_INFO("OK: Loopback test passed");
        } else {
            ROS_ERROR("ERROR: Loopback test failed");
        }
    }

    void executeCB(const mcp2515_can_driver::MCP2515CANCommGoalConstPtr& goal)
    {
        if (!driver_->isConnected()) {
            ROS_ERROR("ERROR: Device not connected");
            mcp2515_can_driver::MCP2515CANCommResult result;
            result.success = false;
            result.message = "Device not connected";
            as_.setAborted(result);
            return;
        }

        if (goal->dlc > 8) {
            ROS_ERROR("ERROR: Invalid DLC: %u", goal->dlc);
            mcp2515_can_driver::MCP2515CANCommResult result;
            result.success = false;
            result.message = "DLC must be between 0 and 8";
            as_.setAborted(result);
            return;
        }

        if (goal->extended && goal->can_id > 0x1FFFFFFF) {
            ROS_ERROR("ERROR: Extended ID out of range: 0x%X", goal->can_id);
            mcp2515_can_driver::MCP2515CANCommResult result;
            result.success = false;
            result.message = "Extended ID out of range (max 0x1FFFFFFF)";
            as_.setAborted(result);
            return;
        }

        if (!goal->extended && goal->can_id > 0x7FF) {
            ROS_ERROR("ERROR: Standard ID out of range: 0x%X", goal->can_id);
            mcp2515_can_driver::MCP2515CANCommResult result;
            result.success = false;
            result.message = "Standard ID out of range (max 0x7FF)";
            as_.setAborted(result);
            return;
        }

        std::string id_type = goal->extended ? "EXT" : "STD";
        std::string frame_type = goal->remote ? "RTR" : "DATA";
        ROS_INFO("TX: %s ID=0x%X %s DLC=%u", id_type.c_str(), goal->can_id,
                 frame_type.c_str(), goal->dlc);

        if (goal->dlc > 0) {
            std::cout << "    Data: [";
            for (size_t i = 0; i < goal->data.size() && i < goal->dlc; ++i) {
                std::cout << "0x" << std::hex << std::setw(2) << std::setfill('0')
                          << (int)goal->data[i] << std::dec;
                if (i < goal->dlc - 1) std::cout << ", ";
            }
            std::cout << "]" << std::endl;
        }

        mcp2515_can_driver::MCP2515CANCommFeedback feedback;
        feedback.status = "Sending CAN frame...";
        as_.publishFeedback(feedback);

        std::vector<uint8_t> data_vec(goal->data.begin(), goal->data.end());
        bool success = driver_->sendCanFrame(
            goal->can_id,
            data_vec.data(),
            goal->dlc,
            goal->extended,
            goal->remote
        );

        mcp2515_can_driver::MCP2515CANCommResult result;

        if (success) {
            ROS_INFO("OK: CAN frame sent successfully");

            result.success = true;
            result.message = "CAN frame sent successfully";
            for (int i = 0; i < 8; ++i) {
                result.received_data[i] = 0;
            }
            result.received_id = 0;
            result.received_dlc = 0;
            as_.setSucceeded(result);
        } else {
            ROS_ERROR("ERROR: Failed to send CAN frame");

            result.success = false;
            result.message = "Failed to send CAN frame";
            for (int i = 0; i < 8; ++i) {
                result.received_data[i] = 0;
            }
            result.received_id = 0;
            result.received_dlc = 0;
            as_.setAborted(result);
        }
    }

private:
    std::atomic<uint64_t> rx_count_;
    std::atomic<double> last_rx_time_;
    std::atomic<double> rx_rate_;

    void rxLoop()
    {
        while (rx_thread_running_ && ros::ok()) {
            ros::Duration(0.001).sleep();
        }
    }

    void onCANFrameReceived(uint32_t can_id, const uint8_t* data, uint8_t dlc,
                              bool extended, bool remote)
    {
        ros::Time now = ros::Time::now();
        double current_time = now.toSec();

        auto update_rate = [this, current_time]() {
            if (last_rx_time_ > 0) {
                double dt = current_time - last_rx_time_;
                if (dt > 0) {
                    rx_rate_ = 1.0 / dt;
                }
            }
            last_rx_time_ = current_time;
            rx_count_++;
        };

        update_rate();

        std::string id_type = extended ? "EXT" : "STD";
        std::string frame_type = remote ? "RTR" : "DATA";

        std::cout << "\n========================================" << std::endl;
        std::cout << "[" << std::fixed << std::setprecision(3) << current_time << "] CAN帧接收" << std::endl;
        std::cout << "----------------------------------------" << std::endl;
        std::cout << "  ID类型: " << id_type << "  CAN ID: 0x" << std::uppercase << std::hex
                  << std::setw(3) << std::setfill('0') << can_id << std::dec << std::nouppercase << std::endl;
        std::cout << "  帧类型: " << frame_type << "  DLC: " << (int)dlc << " bytes" << std::endl;

        if (dlc > 0 && !remote) {
            std::cout << "  数据: [";
            for (size_t i = 0; i < dlc; ++i) {
                std::cout << "0x" << std::hex << std::setw(2) << std::setfill('0')
                          << (int)data[i] << std::dec;
                if (i < dlc - 1) std::cout << ", ";
            }
            std::cout << "]" << std::endl;
        }

        std::cout << "----------------------------------------" << std::endl;
        std::cout << "  接收计数: " << rx_count_ << "  采样率: " << std::fixed
                  << std::setprecision(2) << rx_rate_ << " Hz" << std::endl;
        std::cout << "========================================" << std::endl;
    }

public:
    uint64_t getRxCount() const { return rx_count_; }
    double getRxRate() const { return rx_rate_; }
};

int main(int argc, char** argv)
{
    ros::init(argc, argv, "mcp2515_can_server");

    std::cout << "========================================" << std::endl;
    std::cout << "MCP2515 SPI-to-CAN C++ Action Server" << std::endl;
    std::cout << "========================================" << std::endl;

    int spi_bus = 0, spi_device = 0;
    int bitrate = 500000;
    int sampling_point = 75;
    bool loopback_test = false;

    ros::NodeHandle nh("~");
    nh.param("spi_bus", spi_bus, 0);
    nh.param("spi_device", spi_device, 0);
    nh.param("bitrate", bitrate, 500000);
    nh.param("sampling_point", sampling_point, 75);
    nh.param("loopback_test", loopback_test, false);

    ROS_INFO("Configuration:");
    ROS_INFO("   SPI bus: %d", spi_bus);
    ROS_INFO("   SPI device: %d", spi_device);
    ROS_INFO("   Bitrate: %d bps", bitrate);
    ROS_INFO("   Sampling point: %d%%", sampling_point);

    MCP2515Driver driver(spi_bus, spi_device, bitrate, sampling_point);

    if (!driver.connect()) {
        ROS_ERROR("ERROR: Failed to connect to MCP2515");
        return -1;
    }

    if (!driver.initialize()) {
        ROS_ERROR("ERROR: Failed to initialize MCP2515");
        driver.disconnect();
        return -1;
    }

    MCP2515CANServer server("mcp2515_can_comm", &driver);

    if (loopback_test) {
        server.runLoopbackTest();
        driver.disconnect();
        return 0;
    }

    server.startRxThread();

    ROS_INFO("Server running, waiting for goals...");

    ros::spin();

    server.stopRxThread();
    driver.disconnect();

    ROS_INFO("Server exited");
    return 0;
}