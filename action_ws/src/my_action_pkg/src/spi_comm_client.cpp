// SPDX-License-Identifier: BSD-3-Clause

/**
 * @file spi_comm_client.cpp
 * @brief SPI 通信 Action Client (C++ 版本)
 * 
 * 功能说明:
 *   - 作为 ROS Action 客户端，向服务器发送 SPI 通信请求
 *   - 接收服务器的反馈信息（Feedback）
 *   - 等待并处理服务器的最终结果（Result）
 *   - 显示写入和读取的数据对比
 * 
 * 使用方法:
 *   source install/setup.bash
 *   rosrun my_action_pkg spi_comm_client_cpp \
 *       _spi_bus:=0 \
 *       _device_address:=0 \
 *       _write_data:=0xAA \
 *       _read_after_write:=true
 * 
 * 作者: Jetson Nano
 * 日期: 2026-04-01
 */

#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <my_action_pkg/SPICommAction.h>

#include <cstdlib>

class SPICommClient {
private:
    actionlib::SimpleActionClient<my_action_pkg::SPICommAction> client_;
    
    void feedbackCb(const my_action_pkg::SPICommFeedbackConstPtr &feedback)
    {
        ROS_INFO("Feedback: %s (Data: 0x%02X)", 
                 feedback->status.data.c_str(), 
                 feedback->current_data);
    }
    
    void activeCb()
    {
        ROS_INFO("Goal activated");
    }
    
    void doneCb(const actionlib::SimpleClientGoalState &state,
               const my_action_pkg::SPICommResultConstPtr &result)
    {
        if (state == actionlib::SimpleClientGoalState::SUCCEEDED) {
            ROS_INFO("Result: Goal succeeded");
        } else if (state == actionlib::SimpleClientGoalState::ABORTED) {
            ROS_INFO("Result: Goal aborted");
        } else if (state == actionlib::SimpleClientGoalState::PREEMPTED) {
            ROS_INFO("Result: Goal preempted");
        } else {
            ROS_INFO("Result: Goal failed");
        }
    }

public:
    SPICommClient(uint8_t spi_bus, uint8_t device_address, 
                   uint8_t write_data, bool read_after_write) : 
        client_("spi_comm", true)
    {
        ROS_INFO("Waiting for Action Server...");
        client_.waitForServer();
        ROS_INFO("Action Server connected");
        
        my_action_pkg::SPICommGoal goal;
        goal.spi_bus = spi_bus;
        goal.device_address = device_address;
        goal.write_data = write_data;
        goal.read_after_write = read_after_write;
        
        ROS_INFO("Sending Goal:");
        ROS_INFO("   SPI bus: %d", spi_bus);
        ROS_INFO("   Device address: %d", device_address);
        ROS_INFO("   Write data: 0x%02X (%d)", write_data, write_data);
        ROS_INFO("   Read after write: %s", read_after_write ? "true" : "false");
        
        client_.sendGoal(goal,
                       boost::bind(&SPICommClient::doneCb, this, _1, _2),
                       boost::bind(&SPICommClient::activeCb, this),
                       boost::bind(&SPICommClient::feedbackCb, this, _1));
        
        ROS_INFO("Waiting for result...");
        
        bool finished_before_timeout = client_.waitForResult(ros::Duration(5.0));
        
        if (finished_before_timeout) {
            actionlib::SimpleClientGoalState state = client_.getState();
            const my_action_pkg::SPICommResultConstPtr &result = client_.getResult();
            
            if (state == actionlib::SimpleClientGoalState::SUCCEEDED && result->success) {
                ROS_INFO("=============================================================");
                ROS_INFO("SPI communication succeeded!");
                ROS_INFO("   Written data: 0x%02X (%d)", write_data, write_data);
                if (read_after_write) {
                    ROS_INFO("   Read data: 0x%02X (%d)", result->received_data, result->received_data);
                }
                ROS_INFO("=============================================================");
            } else {
                ROS_WARN("=============================================================");
                ROS_WARN("SPI communication failed!");
                ROS_WARN("=============================================================");
            }
        } else {
            ROS_ERROR("Timeout waiting for result (5 seconds)");
        }
    }
};

int main(int argc, char **argv)
{
    ros::init(argc, argv, "spi_comm_client_cpp");
    ros::NodeHandle nh;
    ros::NodeHandle private_nh("~");
    
    ROS_INFO("Initializing SPI communication Action Client...");
    
    int spi_bus_int = 0, device_address_int = 0, write_data_int = 0xAA;
    bool read_after_write = true;
    
    private_nh.getParam("spi_bus", spi_bus_int);
    private_nh.getParam("device_address", device_address_int);
    private_nh.getParam("write_data", write_data_int);
    private_nh.getParam("read_after_write", read_after_write);
    
    uint8_t spi_bus = (uint8_t)spi_bus_int;
    uint8_t device_address = (uint8_t)device_address_int;
    uint8_t write_data = (uint8_t)write_data_int;
    
    ROS_INFO("========================================");
    ROS_INFO("SPI Communication Action Client");
    ROS_INFO("========================================");
    
    SPICommClient client(spi_bus, device_address, write_data, read_after_write);
    
    return 0;
}