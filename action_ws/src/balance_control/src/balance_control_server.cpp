/*
 * Balance Control Node
 * ====================
 *
 * This node combines both Action Server and Action Client functionality:
 * - Action Server: receives goals for balance control
 * - Action Client: sends commands to itself (for testing/integration)
 *
 * Usage:
 *   Server mode (default): rosrun balance_control balance_control_server
 *   Client mode:          rosrun balance_control balance_control_server _client_mode:=true
 *
 * Author: Jetson Nano
 * Date: 2026-05-06
 */

#include <ros/ros.h>
#include <actionlib/server/simple_action_server.h>
#include <sensor_msgs/Imu.h>
#include <sensor_msgs/JointState.h>
#include <dcu_driver_pkg/MotorCommand.h>
#include <balance_control/BalanceControlAction.h>

#include <map>
#include <string>
#include <memory>
#include <mutex>
#include <thread>

#include "balance_algorithm_base.h"
#include "robot_hardware_params.h"
#include "../algorithms/lqr_controller.h"
#include "../algorithms/vmc_controller.h"
#include "../algorithms/mpc_controller.h"
#include "../algorithms/adp_controller.h"

namespace balance_control {

/*
 * Constants
 */
static constexpr uint8_t HIP_ROLL = 0;
static constexpr uint8_t HIP_PITCH = 1;
static constexpr uint8_t KNEE_PITCH = 2;
static constexpr uint8_t WHEEL = 3;

static constexpr uint8_t LEFT = 0;
static constexpr uint8_t RIGHT = 1;

static constexpr uint8_t CTRL1 = 1;
static constexpr uint8_t CTRL2 = 2;

static constexpr uint8_t ALGORITHM_LQR = 0;
static constexpr uint8_t ALGORITHM_VMC = 1;
static constexpr uint8_t ALGORITHM_MPC = 2;
static constexpr uint8_t ALGORITHM_ADP = 3;

/*
 * Motor Channel Configuration (local mapping)
 */
struct MotorChanConfig {
    std::string name;
    uint8_t leg;
    uint8_t joint;
    uint8_t motor_id;
    uint8_t channel;
};

/*
 * Balance Control Action Server
 */
class BalanceControlServer {
public:
    BalanceControlServer()
        : action_server_(nh_, "balance_control",
            boost::bind(&BalanceControlServer::executeCB, this, _1), false)
        , control_enabled_(false)
        , target_roll_(0.0), target_pitch_(0.0), target_yaw_(0.0)
        , roll_(0.0), pitch_(0.0), yaw_(0.0)
        , print_counter_(0)
    {
        // Load hardware parameters
        // Priority: 1. explicit yaml_path param, 2. config/robot_hardware_params.yaml, 3. ROS parameter server
        std::string yaml_path;
        nh_.param("hardware_params_file", yaml_path, std::string(""));

        if (yaml_path.empty()) {
            // Try default config file location
            const char* ws_path = std::getenv("HOME");
            if (ws_path) {
                yaml_path = std::string(ws_path) + "/Desktop/Jetson_Nano/action_ws/src/balance_control/config/robot_hardware_params.yaml";
            }
        }

        if (!yaml_path.empty()) {
            try {
                params_.loadFromYaml(yaml_path);
                ROS_INFO("Hardware params loaded from: %s", yaml_path.c_str());
            } catch (...) {
                ROS_WARN("Failed to load yaml, falling back to ROS parameter server");
                params_.loadFromParamServer(nh_);
            }
        } else {
            params_.loadFromParamServer(nh_);
        }

        imu_sub_ = nh_.subscribe("/imu_serial/data", 100,
                                &BalanceControlServer::imuCallback, this);
        joint_states_sub_ = nh_.subscribe("/joint_states", 100,
                                         &BalanceControlServer::jointStatesCallback, this);
        motor_cmd_pub_ = nh_.advertise<dcu_driver_pkg::MotorCommand>("/motor/command", 100);

        loadAlgorithms();
        loadMotorConfigs();

        action_server_.start();

        ROS_INFO("==========================================");
        ROS_INFO("Balance Control Action Server Started");
        ROS_INFO("Action name: balance_control");
        ROS_INFO("Algorithms: LQR, VMC, MPC");
        ROS_INFO("IMU topic: /imu_serial/data");
        ROS_INFO("Motor command topic: /motor/command");
        ROS_INFO("Hardware params loaded from: %s", yaml_path.empty() ? "parameter server" : yaml_path.c_str());
        ROS_INFO("==========================================");
    }

    void loadAlgorithms() {
        algorithms_["LQR"] = std::make_shared<LQRController>();
        algorithms_["VMC"] = std::make_shared<VMCController>();
        algorithms_["MPC"] = std::make_shared<MPCController>();
        algorithms_["ADP"] = std::make_shared<ADPController>();
        current_algorithm_ = algorithms_["LQR"];
        ROS_INFO("Loaded algorithms: LQR, VMC, MPC, ADP (default: LQR)");
    }

    void loadMotorConfigs() {
        const auto& motor_configs = params_.getMotorConfigs();
        if (!motor_configs.empty()) {
            motor_configs_.clear();
            for (const auto& cfg : motor_configs) {
                MotorChanConfig mc;
                mc.name = cfg.name;
                mc.leg = (cfg.name.find("left") != std::string::npos) ? LEFT : RIGHT;
                mc.joint = (cfg.joint_type == "hip_roll") ? HIP_ROLL :
                           (cfg.joint_type == "hip_pitch") ? HIP_PITCH :
                           (cfg.joint_type == "knee_pitch") ? KNEE_PITCH : WHEEL;
                mc.motor_id = cfg.motor_id;
                mc.channel = cfg.channel;
                motor_configs_.push_back(mc);
            }
            ROS_INFO("Loaded %zu motor configs from hardware params", motor_configs_.size());
        } else {
            motor_configs_.push_back({"joint_left_leg_1", LEFT, HIP_ROLL, 3, CTRL1});
            motor_configs_.push_back({"joint_left_leg_2", LEFT, HIP_PITCH, 3, CTRL1});
            motor_configs_.push_back({"joint_left_leg_3", LEFT, KNEE_PITCH, 3, CTRL2});
            motor_configs_.push_back({"joint_left_leg_4", LEFT, WHEEL, 3, CTRL2});
            motor_configs_.push_back({"joint_right_leg_1", RIGHT, HIP_ROLL, 2, CTRL1});
            motor_configs_.push_back({"joint_right_leg_2", RIGHT, HIP_PITCH, 2, CTRL1});
            motor_configs_.push_back({"joint_right_leg_3", RIGHT, KNEE_PITCH, 5, CTRL2});
            motor_configs_.push_back({"joint_right_leg_4", RIGHT, WHEEL, 5, CTRL2});
            ROS_INFO("Using default motor configs");
        }
    }

    void imuCallback(const sensor_msgs::Imu::ConstPtr& msg) {
        std::lock_guard<std::mutex> lock(state_mutex_);
        roll_ = atan2(2.0 * (msg->orientation.w * msg->orientation.x + msg->orientation.y * msg->orientation.z),
                      1.0 - 2.0 * (msg->orientation.x * msg->orientation.x + msg->orientation.y * msg->orientation.y));
        pitch_ = asin(2.0 * (msg->orientation.w * msg->orientation.y - msg->orientation.z * msg->orientation.x));
        yaw_ = atan2(2.0 * (msg->orientation.w * msg->orientation.z + msg->orientation.x * msg->orientation.y),
                    1.0 - 2.0 * (msg->orientation.y * msg->orientation.y + msg->orientation.z * msg->orientation.z));
    }

    void jointStatesCallback(const sensor_msgs::JointState::ConstPtr& msg) {
        std::lock_guard<std::mutex> lock(state_mutex_);
        if (msg->position.size() >= 8) {
            // Store joint positions if needed
        }
    }

    void executeCB(const BalanceControlGoalConstPtr& goal) {
        BalanceControlResult result;
        BalanceControlFeedback feedback;

        ROS_INFO("==========================================");
        ROS_INFO("Received Goal: algorithm_id=%d, enable_control=%d",
                 goal->algorithm_id, goal->enable_control);
        ROS_INFO("Target pose: roll=%.3f, pitch=%.3f, yaw=%.3f",
                 goal->target_roll, goal->target_pitch, goal->target_yaw);

        if (goal->enable_control) {
            control_enabled_ = true;
            ROS_INFO("[Command] Balance control enabled");
        } else {
            control_enabled_ = false;
            sendZeroTorque();
            ROS_INFO("[Command] Balance control disabled");
        }

        std::string algo_name;
        switch (goal->algorithm_id) {
            case ALGORITHM_LQR: algo_name = "LQR"; break;
            case ALGORITHM_VMC: algo_name = "VMC"; break;
            case ALGORITHM_MPC: algo_name = "MPC"; break;
            case ALGORITHM_ADP: algo_name = "ADP"; break;
            default: algo_name = "LQR"; break;
        }

        if (algorithms_.find(algo_name) != algorithms_.end()) {
            current_algorithm_ = algorithms_[algo_name];
            ROS_INFO("[Command] Switched to algorithm: %s", algo_name.c_str());
        } else {
            ROS_WARN("[Command] Unknown algorithm: %s, using LQR", algo_name.c_str());
            current_algorithm_ = algorithms_["LQR"];
        }

        target_roll_ = goal->target_roll;
        target_pitch_ = goal->target_pitch;
        target_yaw_ = goal->target_yaw;
        ROS_INFO("[Command] Target pose set: roll=%.3f, pitch=%.3f, yaw=%.3f",
                 target_roll_, target_pitch_, target_yaw_);

        feedback.current_roll = roll_;
        feedback.current_pitch = pitch_;
        feedback.current_yaw = yaw_;
        feedback.algorithm_name = current_algorithm_->getName();
        feedback.control_enabled = control_enabled_;
        feedback.status_message = "Command executed";
        action_server_.publishFeedback(feedback);

        result.success = true;
        result.message = "Goal processed";
        action_server_.setSucceeded(result);

        ROS_INFO("Goal processed, algorithm: %s, control: %s",
                 current_algorithm_->getName().c_str(),
                 control_enabled_ ? "enabled" : "disabled");
        ROS_INFO("==========================================");
    }

    void update() {
        std::lock_guard<std::mutex> lock(state_mutex_);

        if (!control_enabled_) {
            return;
        }

        Eigen::VectorXd state(6);
        state << roll_, pitch_, yaw_, 0.0, 0.0, 0.0;

        Eigen::VectorXd target(6);
        target << target_roll_, target_pitch_, target_yaw_, 0.0, 0.0, 0.0;

        Eigen::VectorXd output(12);
        current_algorithm_->computeControl(state, target, output);

        publishMotorCommands(output);
    }

    void publishMotorCommands(const Eigen::VectorXd& output) {
        Eigen::VectorXd torques = output.segment<8>(0);

        for (size_t i = 0; i < motor_configs_.size(); ++i) {
            const auto& config = motor_configs_[i];

            dcu_driver_pkg::MotorCommand cmd;
            cmd.cmd = 4;
            cmd.motor_id = config.motor_id;
            cmd.channel = config.channel;
            cmd.q = 0.0;
            cmd.dq = 0.0;
            cmd.tau = torques(i);
            cmd.kp = 20.0;
            cmd.kd = 2.0;

            motor_cmd_pub_.publish(cmd);
        }
    }

    void sendZeroTorque() {
        for (const auto& config : motor_configs_) {
            dcu_driver_pkg::MotorCommand cmd;
            cmd.cmd = 4;
            cmd.motor_id = config.motor_id;
            cmd.channel = config.channel;
            cmd.q = 0.0;
            cmd.dq = 0.0;
            cmd.tau = 0.0;
            cmd.kp = 0.0;
            cmd.kd = 0.0;
            motor_cmd_pub_.publish(cmd);
        }
        ROS_DEBUG("Zero torque sent to all motors");
    }

    void spin() {
        ros::Rate rate(500);
        ROS_INFO("Entering control loop (500Hz)");
        ROS_INFO("Debug output: printing every %d iterations (~10Hz)", PRINT_INTERVAL);

        while (ros::ok()) {
            ros::spinOnce();
            update();

            print_counter_++;
            if (print_counter_ >= PRINT_INTERVAL) {
                print_counter_ = 0;
                printDebugInfo();
            }

            rate.sleep();
        }
    }

    void printDebugInfo() {
        std::lock_guard<std::mutex> lock(state_mutex_);

        ROS_INFO("----------------------------------------");
        ROS_INFO("[Debug] IMU: roll=%.3f, pitch=%.3f, yaw=%.3f", roll_, pitch_, yaw_);
        ROS_INFO("[Debug] Target: roll=%.3f, pitch=%.3f, yaw=%.3f", target_roll_, target_pitch_, target_yaw_);
        ROS_INFO("[Debug] Control: %s, Algorithm: %s",
                 control_enabled_ ? "enabled" : "disabled",
                 current_algorithm_->getName().c_str());

        Eigen::VectorXd state(6);
        state << roll_, pitch_, yaw_, 0.0, 0.0, 0.0;
        Eigen::VectorXd target(6);
        target << target_roll_, target_pitch_, target_yaw_, 0.0, 0.0, 0.0;
        Eigen::VectorXd output(12);
        current_algorithm_->computeControl(state, target, output);

        ROS_INFO("[Debug] Motor Torques:");
        for (size_t i = 0; i < motor_configs_.size() && i < 8; ++i) {
            const auto& config = motor_configs_[i];
            ROS_INFO("  [%zu] %s: tau=%.3f Nm", i, config.name.c_str(), output(i));
        }
        ROS_INFO("----------------------------------------");
    }

    bool isControlEnabled() const { return control_enabled_; }
    double getRoll() const { return roll_; }
    double getPitch() const { return pitch_; }
    double getYaw() const { return yaw_; }

private:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<balance_control::BalanceControlAction> action_server_;
    ros::Subscriber imu_sub_;
    ros::Subscriber joint_states_sub_;
    ros::Publisher motor_cmd_pub_;

    std::mutex state_mutex_;
    double roll_, pitch_, yaw_;
    double target_roll_, target_pitch_, target_yaw_;
    bool control_enabled_;

    std::map<std::string, std::shared_ptr<BalanceAlgorithm>> algorithms_;
    std::shared_ptr<BalanceAlgorithm> current_algorithm_;
    std::vector<MotorChanConfig> motor_configs_;
    RobotHardwareParams params_;

    int print_counter_;
    static constexpr int PRINT_INTERVAL = 50;
};

} // namespace balance_control

/*
 * Main Entry Point
 * ================
 */
int main(int argc, char** argv) {
    ros::init(argc, argv, "balance_control_server");

    try {
        balance_control::BalanceControlServer server;
        server.spin();
    } catch (const std::exception& e) {
        ROS_ERROR("Exception: %s", e.what());
        return 1;
    }

    return 0;
}