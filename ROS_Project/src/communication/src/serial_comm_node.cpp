#include <ros/ros.h>
#include <std_msgs/String.h>
#include <communication/SerialCommunication.h>
#include "communication/serial_comm.h"

class SerialCommNode {
public:
    SerialCommNode() {
        nh_.param("serial_port", serial_port_, std::string("/dev/ttyUSB0"));
        nh_.param("baud_rate", baud_rate_, 115200);
        
        serial_comm_ = new communication::SerialComm(serial_port_, baud_rate_);
        
        if (!serial_comm_->connect()) {
            ROS_ERROR("Failed to connect to serial port %s", serial_port_.c_str());
        }
        
        tx_pub_ = nh_.advertise<std_msgs::String>("serial/tx", 10);
        rx_sub_ = nh_.subscribe("serial/rx", 10, &SerialCommNode::rxCallback, this);
        
        service_ = nh_.advertiseService("serial_comm", &SerialCommNode::serviceCallback, this);
        
        ROS_INFO("Serial Communication Node started on %s", serial_port_.c_str());
    }
    
    ~SerialCommNode() {
        delete serial_comm_;
    }
    
    void rxCallback(const std_msgs::String::ConstPtr& msg) {
        serial_comm_->write(msg->data);
    }
    
    bool serviceCallback(communication::SerialCommunication::Request& req,
                        communication::SerialCommunication::Response& res) {
        res.success = serial_comm_->write(req.data);
        res.response = res.success ? "Serial data sent" : "Serial send failed";
        return true;
    }
    
private:
    ros::NodeHandle nh_;
    communication::SerialComm* serial_comm_;
    ros::Publisher tx_pub_;
    ros::Subscriber rx_sub_;
    ros::ServiceServer service_;
    std::string serial_port_;
    int baud_rate_;
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "serial_comm_node");
    SerialCommNode node;
    ros::spin();
    return 0;
}