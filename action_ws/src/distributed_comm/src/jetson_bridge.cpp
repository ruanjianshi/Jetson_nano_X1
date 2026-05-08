/**
 * @file    jetson_bridge.cpp


 * @brief   Jetson Nano side: publishes to /jetson/pub_data, subscribes to /pc/pub_data
 * @details Runs on Jetson Nano B01. Run roscore first, then launch this node.
 *          The PC side runs pc_bridge to complete the bidirectional bridge.
 *
 * Topics:
 *   Publish:   /jetson/pub_data  (std_msgs/String, seq + timestamp + payload)
 *   Subscribe: /pc/pub_data      (std_msgs/String, from PC)
 *
 * Usage:
 *   rosrun distributed_comm jetson_bridge _pub_rate:=50 _msg_size:=256
 *
 * Parameters:
 *   _pub_rate  (double, default 50)  -- messages per second
 *   _msg_size  (int,    default 256) -- payload bytes per message
 *  作者: Qi Xiao\n *  邮箱: 2408128687@qq.com\n */

#include <ros/ros.h>
#include <std_msgs/String.h>
#include <sstream>
#include <iomanip>

//  作者: Qi Xiao
//  邮箱: 2408128687@qq.com

class JetsonBridge {
public:
    JetsonBridge(ros::NodeHandle& nh, ros::NodeHandle& pnh) {
        // Publisher: Jetson -> PC
        pub_ = nh.advertise<std_msgs::String>("/jetson/pub_data", 100);
        // Subscriber: PC -> Jetson
        sub_ = nh.subscribe("/pc/pub_data", 100, &JetsonBridge::callback, this);

        pnh.param("pub_rate", pub_rate_, 50.0);
        pnh.param("msg_size", msg_size_, 256);

        send_count_ = 0;
        send_seq_   = 0;
        recv_count_ = 0;
        recv_bytes_ = 0;
        last_print_ = ros::Time::now();

        // Fill payload with fixed char for consistent bandwidth measurement
        payload_ = std::string(msg_size_, 'A');

        ROS_INFO("[Jetson Bridge] started (pub=/jetson/pub_data sub=/pc/pub_data) rate=%.0f Hz",
                 pub_rate_);
    }

    // Callback for /pc/pub_data: count received messages
    void callback(const std_msgs::String::ConstPtr& msg) {
        recv_count_++;
        recv_bytes_ += msg->data.size();
    }

    void run() {
        // Loop at max(pub_rate * 2, 200) to avoid ROS queue overflow
        ros::Rate r(std::max(200.0, pub_rate_ * 2));

        while (ros::ok()) {
            ros::Time now = ros::Time::now();

            // Build message: seq, timestamp, payload
            send_seq_++;
            std_msgs::String msg;
            std::ostringstream oss;
            oss << send_seq_ << ","
                << std::fixed << std::setprecision(6) << now.toSec() << ","
                << payload_;
            msg.data = oss.str();
            pub_.publish(msg);
            send_count_++;

            // Print stats every 1 second
            double elapsed = (now - last_print_).toSec();
            if (elapsed >= 1.0) {
                double send_rate = send_count_ / elapsed;
                double recv_rate = recv_count_ / elapsed;
                double recv_kbps = (recv_bytes_ * 8.0 / 1000.0) / elapsed;

                ROS_INFO(" Send: %.1f msg/s | Recv: %.1f msg/s (%.1f kbps)",
                         send_rate, recv_rate, recv_kbps);

                send_count_ = 0;
                recv_count_ = 0;
                recv_bytes_ = 0;
                last_print_ = now;
            }

            ros::spinOnce();
            r.sleep();
        }
    }

private:
    ros::Publisher  pub_;
    ros::Subscriber sub_;

    double      pub_rate_;
    int         msg_size_;
    std::string payload_;

    int         send_count_;
    int         send_seq_;
    int         recv_count_;
    int         recv_bytes_;
    ros::Time   last_print_;
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "jetson_bridge");
    ros::NodeHandle nh;
    ros::NodeHandle pnh("~");   // private namespace for params
    JetsonBridge bridge(nh, pnh);
    bridge.run();
    return 0;
}
