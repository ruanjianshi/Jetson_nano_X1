/*
 * ========================================
 * 脉塔智能 USBCAN-II CAN 通信 C++ Client
 * ========================================
 * 功能说明:
 *   - C++ 版本的 CAN 客户端
 *   - 用于测试 C++ Server
 *
 * 编译:
 *   catkin_make
 *
 * 运行:
 *   source devel/setup.bash
 *   rosrun maita_can_comm can_comm_maita_client_cpp
 *
 * 参数:
 *   _can_id:=0x123
 *   _data:="[1, 2, 3]"
 *   _dlc:=3
 *   _extended:=false
 *   _channel:=0
 *
 * 作者: Jetson Nano
 * 日期: 2026-04-02
 */

#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <maita_can_comm/CANCommAction.h>
#include <iostream>

int main(int argc, char** argv) {
    ros::init(argc, argv, "can_comm_maita_client_cpp");

    // 获取参数
    int can_id = 0x123;
    std::vector<uint8_t> data = {0x01, 0x02, 0x03};
    int dlc = 3;
    bool extended = false;
    int channel = 0;

    ros::NodeHandle nh("~");
    nh.param("can_id", can_id, (int)0x123);
    nh.param("dlc", dlc, 3);
    nh.param("extended", extended, false);
    nh.param("channel", channel, 0);

    // 获取数据参数
    std::string data_str;
    if (nh.getParam("data", data_str)) {
        // 解析数据字符串 "[1, 2, 3]" 或 "[0xDE, 0xAD]"
        if (data_str.find("[") == 0 && data_str.find("]") == data_str.length() - 1) {
            data_str = data_str.substr(1, data_str.length() - 2);
            std::stringstream ss(data_str);
            std::string item;
            data.clear();
            while (std::getline(ss, item, ',')) {
                // 去除空格
                item.erase(0, item.find_first_not_of(" \t"));
                item.erase(item.find_last_not_of(" \t") + 1);
                // 支持十六进制 (0xDE) 和十进制 (222)
                data.push_back(std::stoi(item, nullptr, 0));
            }
        }
    }

    // 创建 Action Client
    actionlib::SimpleActionClient<maita_can_comm::CANCommAction> ac("can_comm", true);

    std::cout << "等待 CAN 通信 Action Server..." << std::endl;
    ac.waitForServer();

    std::cout << "✅ Action Server 已连接" << std::endl;

    // 创建 Goal
    maita_can_comm::CANCommGoal goal;
    goal.can_id = can_id;
    goal.data = data;
    goal.dlc = dlc;
    goal.extended = extended;
    goal.channel = channel;

    std::cout << "📤 发送 CAN 帧:" << std::endl;
    std::cout << "   CAN ID: 0x" << std::hex << can_id << std::dec << std::endl;
    std::cout << "   数据长度: " << dlc << std::endl;
    std::cout << "   数据: ";
    for (size_t i = 0; i < data.size(); i++) {
        std::cout << "0x" << std::hex << (int)data[i] << std::dec << " ";
    }
    std::cout << std::endl;
    std::cout << "   扩展帧: " << (extended ? "是" : "否") << std::endl;
    std::cout << "   通道: " << channel << std::endl;

    // 发送 Goal
    ac.sendGoal(goal);

    // 等待结果
    bool finished_before_timeout = ac.waitForResult(ros::Duration(30.0));

    if (finished_before_timeout) {
        actionlib::SimpleClientGoalState state = ac.getState();
        if (state == actionlib::SimpleClientGoalState::SUCCEEDED) {
            std::cout << "✅ " << ac.getResult()->message << std::endl;
        } else {
            std::cout << "❌ " << ac.getResult()->message << std::endl;
        }
    } else {
        std::cout << "❌ 操作超时" << std::endl;
    }

    return 0;
}