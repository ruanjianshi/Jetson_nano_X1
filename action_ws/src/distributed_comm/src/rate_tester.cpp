/**
 * @file    rate_tester.cpp


 * @brief   WiFi throughput rate test: auto-ramp publish rate to find max stable throughput
 * @details Runs on PC. Gradually increases publish rate to /pc/pub_data while monitoring
 *          /jetson/pub_data receive rate. When received ratio drops below threshold, stops
 *          and reports the maximum stable rate.
 *
 * Usage:
 *   # Jetson side first: rosrun distributed_comm jetson_bridge _pub_rate:=200
 *   # PC side:
 *   export ROS_MASTER_URI=http://<Jetson_IP>:11311
 *   export ROS_IP=<PC_IP>
 *   rosrun distributed_comm rate_tester _start_hz:=50 _step_hz:=50 _interval_s:=5
 *
 * Parameters:
 *   _start_hz        (double, default 10)  -- starting frequency (Hz)
 *   _step_hz         (double, default 20)  -- increase per step (Hz)
 *   _interval_s      (double, default 5)   -- seconds per step
 *   _unstable_ratio  (double, default 0.85)-- recv/expect ratio threshold for unstable
 *   _msg_size        (int,    default 256) -- payload bytes per message
 *  作者: Qi Xiao\n *  邮箱: 2408128687@qq.com\n */

#include <ros/ros.h>
#include <std_msgs/String.h>
#include <sstream>
#include <iomanip>

//  作者: Qi Xiao
//  邮箱: 2408128687@qq.com

class RateTester {
public:
    RateTester(ros::NodeHandle& nh, ros::NodeHandle& pnh) {
        // Publisher to Jetson side
        pub_ = nh.advertise<std_msgs::String>("/pc/pub_data", 100);
        // Monitor Jetson's published messages
        sub_ = nh.subscribe("/jetson/pub_data", 100, &RateTester::callback, this);

        pnh.param("start_hz",       start_hz_,       10.0);
        pnh.param("step_hz",        step_hz_,        20.0);
        pnh.param("interval_s",     interval_s_,      5.0);
        pnh.param("unstable_ratio", unstable_ratio_,  0.85);
        pnh.param("msg_size",       msg_size_,        256);

        current_hz_     = start_hz_;
        last_ramp_      = ros::Time::now();
        max_stable_hz_  = 0.0;
        send_count_     = 0;
        recv_count_     = 0;
        recv_bytes_     = 0;
        latency_sum_    = 0.0;

        payload_ = std::string(msg_size_, 'T');

        ROS_INFO("============================================");
        ROS_INFO("  WiFi Throughput Rate Test");
        ROS_INFO("  start=%.0f Hz  step=%.0f  interval=%.0fs",
                 start_hz_, step_hz_, interval_s_);
        ROS_INFO("  unstable_ratio=%.0f%%  msg_size=%d bytes",
                 unstable_ratio_ * 100.0, msg_size_);
        ROS_INFO("============================================");
    }

    // Monitor /jetson/pub_data: count messages, measure latency
    void callback(const std_msgs::String::ConstPtr& msg) {
        recv_count_++;
        recv_bytes_ += msg->data.size();

        size_t p1 = msg->data.find(',');
        if (p1 != std::string::npos) {
            size_t p2 = msg->data.find(',', p1 + 1);
            if (p2 != std::string::npos) {
                double st = std::stod(msg->data.substr(p1 + 1, p2 - p1 - 1));
                latency_sum_ += (ros::Time::now().toSec() - st);
            }
        }
    }

    void run() {
        // Loop at least 500Hz to handle high publish rates without queue overflow
        ros::Rate r(std::max(500.0, current_hz_ * 3));
        int seq = 0;

        while (ros::ok()) {
            ros::Time now = ros::Time::now();
            double ramp_elapsed = (now - last_ramp_).toSec();

            // Ramp up rate after each interval
            if (ramp_elapsed >= interval_s_) {
                double recv_rate = recv_count_ / ramp_elapsed;
                double recv_kbps = (recv_bytes_ * 8.0 / 1000.0) / ramp_elapsed;
                double ratio = recv_rate / current_hz_;
                double avg_lat = recv_count_ > 0
                                 ? (latency_sum_ / recv_count_ * 1000.0) : 0.0;

                ROS_INFO("[%3.0f Hz] recv=%.0f  ratio=%3.0f%%  kbps=%.0f  lat=%.1f ms",
                         current_hz_, recv_rate, ratio * 100.0, recv_kbps, avg_lat);

                if (ratio >= unstable_ratio_) {
                    // Still stable, record and continue
                    max_stable_hz_ = current_hz_;
                    current_hz_ += step_hz_;
                } else {
                    // Unstable - print result and exit
                    double max_kbps = max_stable_hz_ * msg_size_ * 8.0 / 1000.0;
                    ROS_WARN("============================================");
                    ROS_WARN("  MAX STABLE THROUGHPUT");
                    ROS_WARN("  Rate:    %.0f Hz  |  %.0f msgs/s",
                             max_stable_hz_, max_stable_hz_);
                    ROS_WARN("  Bandwidth: %.0f kbps  |  %.2f Mbps",
                             max_kbps, max_kbps / 1000.0);
                    ROS_WARN("  Last test: %.0f Hz @ %.0f%% ratio",
                             current_hz_, ratio * 100.0);
                    ROS_WARN("============================================");
                    ros::shutdown();
                    return;
                }

                // Reset counters for next interval
                send_count_  = 0;
                recv_count_  = 0;
                recv_bytes_  = 0;
                latency_sum_ = 0.0;
                last_ramp_   = now;
            }

            // Publish message at current test rate
            seq++;
            std_msgs::String msg;
            std::ostringstream oss;
            oss << seq << ","
                << std::fixed << std::setprecision(6) << now.toSec() << ","
                << payload_;
            msg.data = oss.str();
            pub_.publish(msg);
            send_count_++;

            ros::spinOnce();
            r.sleep();
        }
    }

private:
    ros::Publisher  pub_;
    ros::Subscriber sub_;

    double start_hz_, step_hz_, interval_s_, unstable_ratio_;
    int    msg_size_;
    std::string payload_;

    double    current_hz_;
    ros::Time last_ramp_;
    double    max_stable_hz_;
    int       send_count_;
    int       recv_count_;
    int       recv_bytes_;
    double    latency_sum_;
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "rate_tester");
    ros::NodeHandle nh;
    ros::NodeHandle pnh("~");
    RateTester tester(nh, pnh);
    tester.run();
    return 0;
}
