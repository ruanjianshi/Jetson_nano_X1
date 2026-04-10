#include <ros/ros.h>
#include <std_msgs/String.h>
#include <communication/NetworkCommunication.h>
#include "communication/network_comm.h"

class NetworkCommNode {
public:
    NetworkCommNode() {
        nh_.param("server_ip", server_ip_, std::string("0.0.0.0"));
        nh_.param("server_port", server_port_, 5000);
        
        network_comm_ = new communication::NetworkComm(server_ip_, server_port_);
        
        if (!network_comm_->startServer()) {
            ROS_ERROR("Failed to start network server");
        }
        
        tx_pub_ = nh_.advertise<std_msgs::String>("network/tx", 10);
        rx_sub_ = nh_.subscribe("network/rx", 10, &NetworkCommNode::rxCallback, this);
        
        service_ = nh_.advertiseService("network_comm", &NetworkCommNode::serviceCallback, this);
        
        ROS_INFO("Network Communication Node started on %s:%d", server_ip_.c_str(), server_port_);
    }
    
    ~NetworkCommNode() {
        delete network_comm_;
    }
    
    void rxCallback(const std_msgs::String::ConstPtr& msg) {
        network_comm_->broadcast(msg->data);
    }
    
    bool serviceCallback(communication::NetworkCommunication::Request& req,
                        communication::NetworkCommunication::Response& res) {
        res.success = network_comm_->broadcast(req.message);
        res.response = res.success ? "Network message sent" : "Network send failed";
        return true;
    }
    
private:
    ros::NodeHandle nh_;
    communication::NetworkComm* network_comm_;
    ros::Publisher tx_pub_;
    ros::Subscriber rx_sub_;
    ros::ServiceServer service_;
    std::string server_ip_;
    int server_port_;
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "network_comm_node");
    NetworkCommNode node;
    ros::spin();
    return 0;
}