/**
 * @file    pc_bridge.cpp


 * @brief   PC side: publishes to /pc/pub_data, subscribes to /jetson/pub_data
 * @details Connects to Jetson's ROS master (ROS_MASTER_URI), measures
 *          bidirectional throughput and round-trip latency.
 *
 * Topics:
 *   Publish:   /pc/pub_data      (std_msgs/String, seq + timestamp + payload)
 *   Subscribe: /jetson/pub_data  (std_msgs/String, from Jetson)
 *
 * Usage:
 *   export ROS_MASTER_URI=http://<Jetson_IP>:11311
 *   export ROS_IP=<PC_IP>
 *   rosrun distributed_comm pc_bridge _pub_rate:=50 _msg_size:=256
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

class PCBridge {
public:
    PCBridge(ros::NodeHandle& nh, ros::NodeHandle& pnh) {
        // Publisher: PC -> Jetson
        pub_ = nh.advertise<std_msgs::String>("/pc/pub_data", 100);
        // Subscriber: Jetson -> PC
        sub_ = nh.subscribe("/jetson/pub_data", 100, &PCBridge::callback, this);

        pnh.param("pub_rate", pub_rate_, 50.0);
        pnh.param("msg_size", msg_size_, 256);

        send_count_  = 0;
        send_seq_    = 0;
        recv_count_  = 0;
        recv_bytes_  = 0;
        latency_sum_ = 0.0;
        last_print_  = ros::Time::now();

        payload_ = std::string(msg_size_, 'B');

        ROS_INFO("[PC Bridge] started (pub=/pc/pub_data sub=/jetson/pub_data) rate=%.0f Hz",
                 pub_rate_);
    }

    // Callback for /jetson/pub_data: count messages and measure latency
    void callback(const std_msgs::String::ConstPtr& msg) {
        recv_count_++;
        recv_bytes_ += msg->data.size();

        // Parse send_time from message: "seq,send_time,payload"
        size_t p1 = msg->data.find(',');
        if (p1 != std::string::npos) {
            size_t p2 = msg->data.find(',', p1 + 1);
            if (p2 != std::string::npos) {
                double send_time = std::stod(msg->data.substr(p1 + 1, p2 - p1 - 1));
                latency_sum_ += (ros::Time::now().toSec() - send_time);
            }
        }
    }

    void run() {
        ros::Rate r(std::max(200.0, pub_rate_ * 2));

        while (ros::ok()) {
            ros::Time now = ros::Time::now();

            // Build and publish message
            send_seq_++;
            std_msgs::String msg;
            std::ostringstream oss;
            oss << send_seq_ << ","
                << std::fixed << std::setprecision(6) << now.toSec() << ","
                << payload_;
            msg.data = oss.str();
            pub_.publish(msg);
            send_count_++;

            // Print throughput and latency stats every 1 second
            double elapsed = (now - last_print_).toSec();
            if (elapsed >= 1.0) {
                double send_rate = send_count_ / elapsed;
                double recv_rate = recv_count_ / elapsed;
                double recv_kbps = (recv_bytes_ * 8.0 / 1000.0) / elapsed;
                double avg_lat   = recv_count_ > 0
                                   ? (latency_sum_ / recv_count_ * 1000.0) : 0.0;

                ROS_INFO(" Send: %.1f msg/s | Recv: %.1f msg/s (%.1f kbps) | Latency: %.1f ms",
                         send_rate, recv_rate, recv_kbps, avg_lat);

                send_count_  = 0;
                recv_count_  = 0;
                recv_bytes_  = 0;
                latency_sum_ = 0.0;
                last_print_  = now;
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
    double      latency_sum_;
    ros::Time   last_print_;
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "pc_bridge");
    ros::NodeHandle nh;
    ros::NodeHandle pnh("~");
    PCBridge bridge(nh, pnh);
    bridge.run();
    return 0;
}
