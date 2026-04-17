/*
 * DCU Driver Client Node
 * 
 * Simple client for sending motor control commands via ROS Action
 * 
 * Usage:
 *   rostopic pub /dcu_control/goal dcu_driver_pkg/DCUControlActionGoal "goal: {joint_names: ['joint1'], positions: [3.14], velocities: [0], efforts: [0], stiffness: [10], damping: [1]}"
 */

#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <dcu_driver_pkg/DCUControlAction.h>
#include <sensor_msgs/JointState.h>
#include <vector>
#include <iostream>

typedef actionlib::SimpleActionClient<dcu_driver_pkg::DCUControlAction> Client;

class DCUClient
{
public:
    DCUClient()
        : client_("dcu_control", true)
    {
        ROS_INFO("Waiting for dcu_control server...");
        client_.waitForServer();
        ROS_INFO("Connected to dcu_control server");
        
        joint_state_sub_ = nh_.subscribe("/joint_states", 100, &DCUClient::jointStateCB, this);
    }

    void jointStateCB(const sensor_msgs::JointState::ConstPtr& msg)
    {
        latest_joint_state_ = msg;
    }

    void sendCommand(const std::vector<std::string>& joint_names,
                     const std::vector<double>& positions,
                     const std::vector<double>& velocities = {},
                     const std::vector<double>& efforts = {},
                     const std::vector<double>& stiffness = {},
                     const std::vector<double>& damping = {})
    {
        dcu_driver_pkg::DCUControlGoal goal;
        goal.joint_names = joint_names;
        goal.positions = positions;
        goal.velocities = velocities;
        goal.efforts = efforts;
        goal.stiffness = stiffness;
        goal.damping = damping;

        ROS_INFO("Sending command to %zu joints", joint_names.size());
        client_.sendGoal(goal,
            boost::bind(&DCUClient::doneCB, this, _1, _2),
            boost::bind(&DCUClient::activeCB, this),
            boost::bind(&DCUClient::feedbackCB, this, _1));

        client_.waitForResult(ros::Duration(5.0));

        auto state = client_.getState();
        auto result = client_.getResult();

        if (state == actionlib::SimpleClientGoalState::SUCCEEDED) {
            ROS_INFO("Command succeeded: %s", result->message.c_str());
        } else {
            ROS_ERROR("Command failed: %s", state.toString().c_str());
        }
    }

    void doneCB(const actionlib::SimpleClientGoalState& state,
                const dcu_driver_pkg::DCUControlResultConstPtr& result)
    {
        ROS_INFO("Goal finished with state: %s", state.toString().c_str());
        if (result->success) {
            ROS_INFO("Result: %s", result->message.c_str());
        }
    }

    void activeCB()
    {
        ROS_DEBUG("Goal just went active");
    }

    void feedbackCB(const dcu_driver_pkg::DCUControlFeedbackConstPtr& feedback)
    {
        std::string pos_str, vel_str, eff_str;
        for (size_t i = 0; i < feedback->current_positions.size(); ++i) {
            pos_str += std::to_string(feedback->current_positions[i]) + " ";
            vel_str += std::to_string(feedback->current_velocities[i]) + " ";
            eff_str += std::to_string(feedback->current_efforts[i]) + " ";
        }
        ROS_INFO("Feedback - pos: [%s], vel: [%s], effort: [%s]",
                 pos_str.c_str(), vel_str.c_str(), eff_str.c_str());
    }

    void printJointStates()
    {
        if (latest_joint_state_) {
            ROS_INFO("Current Joint States:");
            for (size_t i = 0; i < latest_joint_state_->name.size(); ++i) {
                ROS_INFO("  %s: pos=%.3f, vel=%.3f, effort=%.3f",
                         latest_joint_state_->name[i].c_str(),
                         latest_joint_state_->position[i],
                         latest_joint_state_->velocity[i],
                         latest_joint_state_->effort[i]);
            }
        }
    }

    sensor_msgs::JointState::ConstPtr getLatestJointState()
    {
        return latest_joint_state_;
    }

private:
    ros::NodeHandle nh_;
    Client client_;
    ros::Subscriber joint_state_sub_;
    sensor_msgs::JointState::ConstPtr latest_joint_state_;
};

int main(int argc, char** argv)
{
    ros::init(argc, argv, "dcu_driver_client");

    std::string ifname = "eth0";
    bool enable_dc = true;
    int cycle_ns = 1000000;
    int rt_priority = -1;
    int bind_cpu = -1;

    ros::NodeHandle nh;
    nh.getParam("ethercat_if", ifname);
    nh.getParam("enable_dc", enable_dc);
    nh.getParam("cycle_ns", cycle_ns);
    nh.getParam("rt_priority", rt_priority);
    nh.getParam("bind_cpu", bind_cpu);

    DCUClient client;
    ros::Duration(1.0).sleep();

    std::string mode = "control";
    if (argc > 1) {
        mode = argv[1];
    }

    if (mode == "control") {
        std::cout << "\n=== DCU Motor Control ===" << std::endl;
        std::cout << "Sending MIT position commands..." << std::endl;

        std::vector<std::string> joint_names = {"joint1"};
        std::vector<double> positions = {3.14};
        std::vector<double> velocities = {0.0};
        std::vector<double> efforts = {0.0};
        std::vector<double> stiffness = {50.0};
        std::vector<double> damping = {1.0};

        client.sendCommand(joint_names, positions, velocities, efforts, stiffness, damping);
    }
    else if (mode == "monitor") {
        std::cout << "\n=== Monitoring Joint States ===" << std::endl;
        ros::Rate rate(10);
        while (ros::ok()) {
            ros::spinOnce();
            client.printJointStates();
            rate.sleep();
        }
    }
    else {
        std::cout << "Usage: " << argv[0] << " [control|monitor]" << std::endl;
        std::cout << "  control - send one MIT command and exit" << std::endl;
        std::cout << "  monitor - continuously print joint states" << std::endl;
    }

    return 0;
}