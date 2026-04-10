#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <mcp2515_can_driver/MCP2515CANCommAction.h>
#include <iostream>
#include <iomanip>
#include <vector>

void feedbackCallback(const mcp2515_can_driver::MCP2515CANCommFeedbackConstPtr& feedback)
{
    ROS_INFO("Feedback: %s", feedback->status.c_str());
}

int main(int argc, char** argv)
{
    ros::init(argc, argv, "mcp2515_can_client");
    ROS_INFO("MCP2515 CAN Client started");

    std::string action_name = "mcp2515_can_comm";
    actionlib::SimpleActionClient<mcp2515_can_driver::MCP2515CANCommAction> ac(action_name, true);

    ROS_INFO("Waiting for action server...");
    if (!ac.waitForServer(ros::Duration(10.0))) {
        ROS_ERROR("ERROR: Action server not available");
        return -1;
    }
    ROS_INFO("OK: Connected to action server");

    int can_id = 0x123;
    int dlc = 4;
    std::vector<uint8_t> data_vec = {0x11, 0x22, 0x33, 0x44, 0x00, 0x00, 0x00, 0x00};
    bool extended = false;
    bool remote = false;

    ros::NodeHandle nh("~");
    nh.param("can_id", can_id, 0x123);
    nh.param("dlc", dlc, 4);
    nh.param("extended", extended, false);
    nh.param("remote", remote, false);

    std::string id_type = extended ? "EXT" : "STD";
    std::string frame_type = remote ? "RTR" : "DATA";
    ROS_INFO("Sending goal: %s ID=0x%X %s DLC=%u", id_type.c_str(), can_id,
             frame_type.c_str(), dlc);

    mcp2515_can_driver::MCP2515CANCommGoal goal;
    goal.can_id = can_id;
    goal.dlc = dlc;
    for (size_t i = 0; i < data_vec.size() && i < 8; ++i) {
        goal.data[i] = data_vec[i];
    }
    goal.extended = extended;
    goal.remote = remote;

    ac.sendGoal(goal, NULL, NULL, boost::bind(&feedbackCallback, _1));

    ROS_INFO("Waiting for result...");
    bool finished = ac.waitForResult(ros::Duration(10.0));

    if (finished) {
        actionlib::SimpleClientGoalState state = ac.getState();
        ROS_INFO("Action finished: %s", state.toString().c_str());

        mcp2515_can_driver::MCP2515CANCommResultConstPtr result = ac.getResult();
        if (result) {
            ROS_INFO("Result:");
            ROS_INFO("   success: %s", result->success ? "true" : "false");
            ROS_INFO("   message: %s", result->message.c_str());

            if (result->success) {
                std::cout << "   received_data: [";
                for (size_t i = 0; i < result->received_data.size(); ++i) {
                    std::cout << "0x" << std::hex << std::setw(2) << std::setfill('0')
                              << (int)result->received_data[i] << std::dec;
                    if (i < result->received_data.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                ROS_INFO("   received_id: 0x%X", result->received_id);
                ROS_INFO("   received_dlc: %u", result->received_dlc);
            }
        }
    } else {
        ROS_WARN("Action did not finish before timeout");
    }

    ROS_INFO("Client test complete");
    return 0;
}