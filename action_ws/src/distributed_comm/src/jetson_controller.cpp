/**
 * @file    jetson_controller.cpp
 * @brief   Jetson Nano side: receives /pc/command from PC, publishes /jetson/telemetry
 * @details Simulates hardware (LED, motor, servo) and reports system telemetry.
 *          Paired with PC-side QT UI in pc_control/.
 *
 * Topics:
 *   Subscribe: /pc/command     (std_msgs/String, JSON commands)
 *   Publish:   /jetson/telemetry (std_msgs/String, JSON telemetry)
 *
 * Commands (JSON):  {"cmd":"led_on"} / {"cmd":"led_off"} / {"cmd":"motor","speed":80} /
 *                   {"cmd":"servo","angle":90} / {"cmd":"status"}
 *
 * Telemetry (JSON): {"cpu_temp":45.2,"uptime":3600,"led":0,"motor":0,"servo":90,
 *                     "mem_used":1.2,"mem_total":3.8,"cpu_percent":25}
 *  作者: Qi Xiao\n *  邮箱: 2408128687@qq.com\n */

#include <ros/ros.h>
#include <std_msgs/String.h>
#include <jsoncpp/json/json.h>
#include <fstream>
#include <sstream>
#include <string>
#include <cmath>
#include <unistd.h>

//  作者: Qi Xiao
//  邮箱: 2408128687@qq.com

class JetsonController {
public:
    JetsonController(ros::NodeHandle& nh, ros::NodeHandle& pnh) {
        cmd_sub_ = nh.subscribe("/pc/command", 10, &JetsonController::cmdCallback, this);
        tele_pub_ = nh.advertise<std_msgs::String>("/jetson/telemetry", 10);

        pnh.param("telemetry_rate", tele_rate_, 2.0);
        pnh.param("simulate_hw", simulate_hw_, true);

        led_state_   = false;
        motor_speed_ = 0;
        servo_angle_ = 90;
        cmd_count_   = 0;

        ROS_INFO("[Jetson Controller] started (sub=/pc/command pub=/jetson/telemetry) tele_rate=%.0f Hz simulate=%d",
                 tele_rate_, simulate_hw_);
    }

    void cmdCallback(const std_msgs::String::ConstPtr& msg) {
        Json::Value root;
        Json::Reader reader;
        if (!reader.parse(msg->data, root)) {
            ROS_WARN("[Controller] Invalid JSON: %s", msg->data.c_str());
            return;
        }

        std::string cmd = root.get("cmd", "").asString();
        cmd_count_++;

        if (cmd == "led_on") {
            led_state_ = true;
            ROS_INFO("[Controller] LED ON (cmd #%d)", cmd_count_);
        } else if (cmd == "led_off") {
            led_state_ = false;
            ROS_INFO("[Controller] LED OFF (cmd #%d)", cmd_count_);
        } else if (cmd == "motor") {
            motor_speed_ = root.get("speed", motor_speed_).asInt();
            ROS_INFO("[Controller] Motor speed = %d (cmd #%d)", motor_speed_, cmd_count_);
        } else if (cmd == "servo") {
            servo_angle_ = root.get("angle", servo_angle_).asInt();
            ROS_INFO("[Controller] Servo angle = %d (cmd #%d)", servo_angle_, cmd_count_);
        } else if (cmd == "status") {
            ROS_INFO("[Controller] Status request (cmd #%d)", cmd_count_);
        } else {
            ROS_WARN("[Controller] Unknown command: %s", cmd.c_str());
        }
    }

    void publishTelemetry() {
        Json::Value tele;
        tele["cpu_temp"]    = readCpuTemp();
        tele["cpu_percent"] = readCpuPercent();
        tele["uptime"]      = static_cast<int>(readUptime());
        tele["mem_used"]    = round(readMemUsed() * 10) / 10;
        tele["mem_total"]   = round(readMemTotal() * 10) / 10;
        tele["led"]         = led_state_ ? 1 : 0;
        tele["motor"]       = motor_speed_;
        tele["servo"]       = servo_angle_;

        std_msgs::String msg;
        msg.data = Json::FastWriter().write(tele);
        tele_pub_.publish(msg);
    }

    void run() {
        ros::Rate r(tele_rate_);
        while (ros::ok()) {
            ros::spinOnce();
            publishTelemetry();
            r.sleep();
        }
    }

private:
    ros::Subscriber cmd_sub_;
    ros::Publisher  tele_pub_;

    double tele_rate_;
    bool   simulate_hw_;
    bool   led_state_;
    int    motor_speed_;
    int    servo_angle_;
    int    cmd_count_;

    float readCpuTemp() {
        std::ifstream f("/sys/class/thermal/thermal_zone0/temp");
        int temp;
        if (f >> temp) return temp / 1000.0f;
        return -1.0f;
    }

    int readCpuPercent() {
        std::ifstream f("/proc/stat");
        std::string line;
        std::getline(f, line);
        std::istringstream ss(line);
        std::string cpu;
        long user, nice, system, idle;
        ss >> cpu >> user >> nice >> system >> idle;
        static long prev_total = 0, prev_idle = 0;
        long total = user + nice + system + idle;
        long diff_total = total - prev_total;
        long diff_idle  = idle  - prev_idle;
        prev_total = total; prev_idle = idle;
        if (diff_total == 0) return -1;
        return static_cast<int>(100 - (diff_idle * 100 / diff_total));
    }

    long readUptime() {
        std::ifstream f("/proc/uptime");
        double up;
        if (f >> up) return static_cast<long>(up);
        return -1;
    }

    float readMemUsed() {
        std::ifstream f("/proc/meminfo");
        std::string key;
        long total = 0, avail = 0, val;
        while (f >> key >> val) {
            f.ignore(256, '\n');
            if (key == "MemTotal:") total = val;
            if (key == "MemAvailable:") avail = val;
            if (total && avail) break;
        }
        if (total) return (total - avail) / 1024.0f / 1024.0f;
        return -1;
    }

    float readMemTotal() {
        std::ifstream f("/proc/meminfo");
        std::string key;
        long total = 0, val;
        while (f >> key >> val) {
            f.ignore(256, '\n');
            if (key == "MemTotal:") { total = val; break; }
        }
        return total / 1024.0f / 1024.0f;
    }
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "jetson_controller");
    ros::NodeHandle nh;
    ros::NodeHandle pnh("~");
    JetsonController controller(nh, pnh);
    controller.run();
    return 0;
}
