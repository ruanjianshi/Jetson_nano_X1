// SPDX-License-Identifier: BSD-3-Clause

/**
 * @file spi_comm_server.cpp
 * @brief SPI 通信 Action Server (C++ 版本)
 * 
 * 功能说明:
 *   - 实现 ROS Action 接口，接收客户端发送的 SPI 通信请求
 *   - 使用 spidev 库通过 SPI 总线与设备通信
 *   - 支持写入数据并读取回环数据
 *   - 支持参数配置（SPI 总线、设备地址等）
 * 
 * 硬件连接:
 *   Jetson Nano SPI1 (/dev/spidev0.0):
 *     - 引脚 19 (GPIO 16/MOSI1): MOSI 主出从入
 *     - 引脚 21 (GPIO 17/MISO1): MISO 主入从出
 *     - 引脚 23 (GPIO 18/SCLK1): SCLK 时钟
 *     - 引脚 24 (GPIO 19/CE0): CE0 片选 0
 *     - 引脚 26 (GPIO 20/CE1): CE1 片选 1
 * 
 * 使用方法:
 *   source install/setup.bash
 *   rosrun my_action_pkg spi_comm_server_cpp
 * 
 * 作者: Jetson Nano
 * 日期: 2026-04-01
 */

#include <ros/ros.h>
#include <actionlib/server/simple_action_server.h>
#include <my_action_pkg/SPICommAction.h>

#include <fcntl.h>
#include <linux/spi/spidev.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <cstring>
#include <cstdlib>

class SPICommServer {
private:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<my_action_pkg::SPICommAction> server_;
    
    int spi_fd_;
    bool connected_;
    std::string enable_echo_;
    
public:
    SPICommServer() : 
        server_(nh_, "spi_comm", boost::bind(&SPICommServer::execute, this, _1), false),
        spi_fd_(-1),
        connected_(false)
    {
        nh_.param("enable_echo", enable_echo_, std::string("true"));
        
        ROS_INFO("Initializing SPI communication Action Server...");
        
        server_.start();
        
        ROS_INFO("SPI communication Action Server started");
        ROS_INFO("   Action name: spi_comm");
    }
    
    ~SPICommServer()
    {
        if (spi_fd_ >= 0) {
            close(spi_fd_);
            ROS_INFO("SPI bus closed");
        }
    }
    
    bool initSPI(uint8_t spi_bus, uint8_t device_address)
    {
        char device_path[32];
        snprintf(device_path, sizeof(device_path), "/dev/spidev%d.%d", spi_bus, device_address);
        
        if (spi_fd_ >= 0) {
            close(spi_fd_);
        }
        
        spi_fd_ = open(device_path, O_RDWR);
        if (spi_fd_ < 0) {
            ROS_ERROR("Failed to open SPI device: %s (Error: %s)", device_path, strerror(errno));
            connected_ = false;
            return false;
        }
        
        uint8_t mode = SPI_MODE_0;
        uint8_t bits = 8;
        uint32_t speed = 1000000;
        
        if (ioctl(spi_fd_, SPI_IOC_WR_MODE, &mode) < 0) {
            ROS_ERROR("Failed to set SPI mode");
            close(spi_fd_);
            connected_ = false;
            return false;
        }
        
        if (ioctl(spi_fd_, SPI_IOC_WR_BITS_PER_WORD, &bits) < 0) {
            ROS_ERROR("Failed to set SPI bits per word");
            close(spi_fd_);
            connected_ = false;
            return false;
        }
        
        if (ioctl(spi_fd_, SPI_IOC_WR_MAX_SPEED_HZ, &speed) < 0) {
            ROS_ERROR("Failed to set SPI clock speed");
            close(spi_fd_);
            connected_ = false;
            return false;
        }
        
        connected_ = true;
        ROS_INFO("SPI device opened successfully: %s", device_path);
        
        return true;
    }
    
    void execute(const my_action_pkg::SPICommGoalConstPtr &goal)
    {
        uint8_t spi_bus = goal->spi_bus;
        uint8_t device_address = goal->device_address;
        uint8_t write_data = goal->write_data;
        bool read_after_write = goal->read_after_write;
        
        ROS_INFO("Received Goal:");
        ROS_INFO("   SPI bus: %d", spi_bus);
        ROS_INFO("   Device address: %d", device_address);
        ROS_INFO("   Write data: 0x%02X (%d)", write_data, write_data);
        ROS_INFO("   Read after write: %s", read_after_write ? "true" : "false");
        
        if (!connected_) {
            if (!initSPI(spi_bus, device_address)) {
                my_action_pkg::SPICommResult result;
                result.received_data = 0;
                result.success = false;
                server_.setAborted(result);
                return;
            }
        }
        
        if (!connected_) {
            ROS_ERROR("SPI not connected, cannot execute task");
            my_action_pkg::SPICommResult result;
            result.received_data = 0;
            result.success = false;
            server_.setAborted(result);
            return;
        }
        
        my_action_pkg::SPICommFeedback feedback;
        feedback.status.data = "Writing data 0x" + std::to_string(write_data);
        feedback.current_data = write_data;
        server_.publishFeedback(feedback);
        
        try {
            if (enable_echo_ == "true") {
                ROS_INFO("Writing data: 0x%02X", write_data);
            }
            
            uint8_t received_data = 0;
            struct spi_ioc_transfer tr = {};
            tr.tx_buf = (unsigned long)&write_data;
            tr.rx_buf = (unsigned long)&received_data;
            tr.len = 1;
            tr.speed_hz = 1000000;
            tr.bits_per_word = 8;
            
            if (ioctl(spi_fd_, SPI_IOC_MESSAGE(1), &tr) < 0) {
                ROS_ERROR("SPI communication error: %s", strerror(errno));
                my_action_pkg::SPICommResult result;
                result.received_data = 0;
                result.success = false;
                server_.setAborted(result);
                return;
            }
            
            if (read_after_write) {
                if (enable_echo_ == "true") {
                    ROS_INFO("Read data: 0x%02X (%d)", received_data, received_data);
                }
                
                feedback.status.data = "Read data: 0x" + std::to_string(received_data);
                feedback.current_data = received_data;
                server_.publishFeedback(feedback);
                
                my_action_pkg::SPICommResult result;
                result.received_data = received_data;
                result.success = true;
                
                server_.setSucceeded(result);
                ROS_INFO("SPI communication succeeded");
            } else {
                if (enable_echo_ == "true") {
                    ROS_INFO("Data written successfully, no read");
                }
                
                my_action_pkg::SPICommResult result;
                result.received_data = 0;
                result.success = true;
                
                server_.setSucceeded(result);
                ROS_INFO("SPI write succeeded");
            }
            
        } catch (const std::exception& e) {
            ROS_ERROR("SPI communication error: %s", e.what());
            my_action_pkg::SPICommResult result;
            result.received_data = 0;
            result.success = false;
            server_.setAborted(result);
        }
    }
};

int main(int argc, char **argv)
{
    ros::init(argc, argv, "spi_comm_server_cpp");
    
    SPICommServer server;
    
    ROS_INFO("Action Server running, waiting for Goal requests...");
    
    ros::spin();
    
    return 0;
}