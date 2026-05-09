#include "gpio_control/gpio_control.h"
#include <ros/ros.h>

namespace gpio_control {

GPIOControlNode::GPIOControlNode(ros::NodeHandle& nh) 
    : nh_(nh) {
    
    nh_.param("gpio_pins", gpio_pins_, std::vector<int>{18, 19, 21, 22});
    
    if (!gpio_manager_.initialize()) {
        ROS_ERROR("Failed to initialize GPIO manager");
        return;
    }
    
    for (int pin : gpio_pins_) {
        if (!gpio_manager_.setupPin(pin, true)) {
            ROS_WARN("Failed to setup GPIO pin %d", pin);
        }
    }
    
    state_pub_ = nh_.advertise<std_msgs::Int32>("gpio/read", 10);
    command_sub_ = nh_.subscribe("gpio/write", 10, &GPIOControlNode::commandCallback, this);
    control_service_ = nh_.advertiseService("gpio_control", &GPIOControlNode::controlService, this);
    
    ROS_INFO("GPIO Control Node initialized");
}

GPIOControlNode::~GPIOControlNode() {
    gpio_manager_.cleanup();
}

void GPIOControlNode::commandCallback(const std_msgs::Int32::ConstPtr& msg) {
    int pin_index = msg->data;
    
    if (pin_index < 0 || pin_index >= static_cast<int>(gpio_pins_.size())) {
        ROS_WARN("Invalid pin index: %d", pin_index);
        return;
    }
    
    int pin = gpio_pins_[pin_index];
    
    if (!gpio_manager_.writePin(pin, true)) {
        ROS_ERROR("Failed to write to GPIO pin %d", pin);
        return;
    }
    
    ros::Duration(0.1).sleep();
    gpio_manager_.writePin(pin, false);
}

bool GPIOControlNode::controlService(gpio_control::GPIOControl::Request& req,
                                    gpio_control::GPIOControl::Response& res) {
    bool success = gpio_manager_.writePin(req.pin_number, req.state);
    res.success = success;
    res.message = success ? "GPIO control successful" : "GPIO control failed";
    return true;
}

void GPIOControlNode::publishState() {
    for (size_t i = 0; i < gpio_pins_.size(); ++i) {
        bool state;
        if (gpio_manager_.readPin(gpio_pins_[i], state)) {
            std_msgs::Int32 msg;
            msg.data = state;
            state_pub_.publish(msg);
        }
    }
}

void GPIOControlNode::run() {
    ros::Rate rate(10);
    
    while (ros::ok()) {
        publishState();
        ros::spinOnce();
        rate.sleep();
    }
}

} // namespace gpio_control

int main(int argc, char** argv) {
    ros::init(argc, argv, "gpio_control_node");
    ros::NodeHandle nh;
    
    gpio_control::GPIOControlNode node(nh);
    node.run();
    
    return 0;
}