#ifndef GPIO_CONTROL_H
#define GPIO_CONTROL_H

#include <ros/ros.h>
#include <std_msgs/Int32.h>
#include <gpio_control/GPIOControl.h>
#include "gpio_manager.h"

namespace gpio_control {

class GPIOControlNode {
public:
    GPIOControlNode(ros::NodeHandle& nh);
    ~GPIOControlNode();
    
    void run();
    
private:
    ros::NodeHandle& nh_;
    GPIOManager gpio_manager_;
    
    ros::Publisher state_pub_;
    ros::Subscriber command_sub_;
    ros::ServiceServer control_service_;
    
    std::vector<int> gpio_pins_;
    
    void commandCallback(const std_msgs::Int32::ConstPtr& msg);
    bool controlService(gpio_control::GPIOControl::Request& req,
                       gpio_control::GPIOControl::Response& res);
    void publishState();
};

} // namespace gpio_control

#endif // GPIO_CONTROL_H