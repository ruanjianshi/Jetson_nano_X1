/*
 * Balance Control Server (URDF匹配版)
 * ====================================
 *
 * 基于 xqrobotV2 URDF: joint_1(X轴)/joint_2(Y轴)/joint_3(Y轴)/wheel(Y轴)
 * 关节命名: left_joint_1/2/3/wheel, right_joint_1/2/3/wheel
 *
 * Author: Qi Xiao
 * Date: 2026-05-06 / Revised: 2026-05-07 (URDF)
 */

#include <ros/ros.h>
#include <ros/package.h>
#include <actionlib/server/simple_action_server.h>
#include <sensor_msgs/Imu.h>
#include <sensor_msgs/JointState.h>
#include <dcu_driver_pkg/MotorCommand.h>
#include <balance_control/BalanceControlAction.h>

#include <map>
#include <string>
#include <memory>
#include <mutex>

#include "balance_algorithm_base.h"
#include "robot_hardware_params.h"
#include "../algorithms/lqr_controller.h"
#include "../algorithms/vmc_controller.h"
#include "../algorithms/mpc_controller.h"
#include "../algorithms/adp_controller.h"

namespace balance_control {

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

// Action command codes
static constexpr uint8_t CMD_STOP = 0;
static constexpr uint8_t CMD_ENABLE = 1;
static constexpr uint8_t CMD_DISABLE = 2;
static constexpr uint8_t CMD_SWITCH_ALGO = 3;
static constexpr uint8_t CMD_SET_TARGET = 4;

struct MotorChanConfig {
    std::string name;
    uint8_t leg;
    uint8_t joint;
    uint8_t motor_id;
    uint8_t channel;
    std::string motor_type;
    std::string joint_type;
    int8_t direction;
};

class BalanceControlServer {
public:
    BalanceControlServer()
        : action_server_(nh_, "balance_control",
            boost::bind(&BalanceControlServer::executeCB, this, _1), false)
        , control_enabled_(false)
        , target_roll_(0.0), target_pitch_(0.0), target_yaw_(0.0)
        , roll_(0.0), pitch_(0.0), yaw_(0.0)
        , angular_vel_x_(0.0), angular_vel_y_(0.0), angular_vel_z_(0.0)
        , print_counter_(0)
        , last_imu_time_(0.0)
        , imu_received_(false)
    {
        // 加载硬件参数 (优先ROS param, 其次package-relative默认路径)
        std::string yaml_path;
        nh_.param<std::string>("hardware_params_file", yaml_path, "");

        if (yaml_path.empty()) {
            const char* ws_path = std::getenv("HOME");
            if (ws_path) {
                yaml_path = std::string(ws_path)
                    + "/Desktop/Jetson_Nano/action_ws/src/balance_control/config/robot_hardware_params.yaml";
            }
        }

        try {
            params_.loadFromYaml(yaml_path);
            ROS_INFO("Hardware params loaded from: %s", yaml_path.c_str());
        } catch (...) {
            ROS_WARN("Failed to load yaml, using ROS param server");
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
        ROS_INFO("  Action: balance_control");
        ROS_INFO("  Algorithms: LQR, VMC, MPC, ADP (default: LQR)");
        ROS_INFO("  IMU topic: /imu_serial/data");
        ROS_INFO("  Motor cmd: /motor/command");
        ROS_INFO("  Config: %s", yaml_path.c_str());
        ROS_INFO("==========================================");
    }

    void loadAlgorithms() {
        algorithms_["LQR"] = std::make_shared<LQRController>();
        algorithms_["VMC"] = std::make_shared<VMCController>();
        algorithms_["MPC"] = std::make_shared<MPCController>();
        algorithms_["ADP"] = std::make_shared<ADPController>();
        current_algorithm_ = algorithms_["LQR"];
        ROS_INFO("Loaded algorithms: LQR, VMC, MPC, ADP");
    }

    void loadMotorConfigs() {
        const auto& motor_configs = params_.getMotorConfigs();
        if (!motor_configs.empty()) {
            motor_configs_.clear();
            for (const auto& cfg : motor_configs) {
                MotorChanConfig mc;
                mc.name = cfg.name;
                mc.motor_id = cfg.motor_id;
                mc.channel = cfg.channel;
                mc.motor_type = cfg.motor_type;
                mc.joint_type = cfg.joint_type;
                mc.direction = cfg.direction;

                // 确定腿侧 (基于关节名中的"left"/"right")
                mc.leg = (cfg.name.find("left") != std::string::npos) ? LEFT : RIGHT;

                // 确定关节类型
                if (cfg.joint_type == "hip_roll")      mc.joint = HIP_ROLL;
                else if (cfg.joint_type == "hip_pitch") mc.joint = HIP_PITCH;
                else if (cfg.joint_type == "knee_pitch") mc.joint = KNEE_PITCH;
                else                                     mc.joint = WHEEL;

                motor_configs_.push_back(mc);
            }
            ROS_INFO("Loaded %zu motor configs", motor_configs_.size());
        } else {
            // URDF默认配置
            motor_configs_ = {
                {"left_joint_1", LEFT, HIP_ROLL, 3, CTRL1, "POWER_FLOW_R86", "hip_roll", 1},
                {"left_joint_2", LEFT, HIP_PITCH, 3, CTRL1, "POWER_FLOW_R86", "hip_pitch", 1},
                {"left_joint_3", LEFT, KNEE_PITCH, 3, CTRL2, "POWER_FLOW_R52", "knee_pitch", 1},
                {"left_joint_wheel", LEFT, WHEEL, 3, CTRL2, "POWER_FLOW_R52", "wheel", 1},
                {"right_joint_1", RIGHT, HIP_ROLL, 2, CTRL1, "POWER_FLOW_R86", "hip_roll", -1},
                {"right_joint_2", RIGHT, HIP_PITCH, 2, CTRL1, "POWER_FLOW_R86", "hip_pitch", -1},
                {"right_joint_3", RIGHT, KNEE_PITCH, 5, CTRL2, "POWER_FLOW_R52", "knee_pitch", -1},
                {"right_joint_wheel", RIGHT, WHEEL, 5, CTRL2, "POWER_FLOW_R52", "wheel", -1}
            };
            ROS_INFO("Using default URDF motor configs");
        }
    }

    void imuCallback(const sensor_msgs::Imu::ConstPtr& msg) {
        std::lock_guard<std::mutex> lock(state_mutex_);
        double qw = msg->orientation.w;
        double qx = msg->orientation.x;
        double qy = msg->orientation.y;
        double qz = msg->orientation.z;

        roll_ = atan2(2.0 * (qw * qx + qy * qz), 1.0 - 2.0 * (qx * qx + qy * qy));
        pitch_ = asin(2.0 * (qw * qy - qz * qx));
        yaw_ = atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz));

        angular_vel_x_ = msg->angular_velocity.x;
        angular_vel_y_ = msg->angular_velocity.y;
        angular_vel_z_ = msg->angular_velocity.z;

        last_imu_time_ = msg->header.stamp.toSec();
        imu_received_ = true;
    }

    void jointStatesCallback(const sensor_msgs::JointState::ConstPtr& msg) {
        std::lock_guard<std::mutex> lock(state_mutex_);
        // Store joint positions for feedback (used in URDF-based FK)
        joint_positions_.clear();
        joint_velocities_.clear();
        for (size_t i = 0; i < msg->position.size() && i < msg->velocity.size(); ++i) {
            joint_positions_.push_back(msg->position[i]);
            joint_velocities_.push_back(msg->velocity[i]);
        }
    }

    void executeCB(const balance_control::BalanceControlGoalConstPtr& goal) {
        BalanceControlResult result;
        BalanceControlFeedback feedback;

        ROS_INFO("==========================================");
        ROS_INFO("Goal: command=%d, algorithm=%d", goal->command, goal->algorithm);
        ROS_INFO("Target: roll=%.3f, pitch=%.3f, yaw=%.3f",
                 goal->target_roll, goal->target_pitch, goal->target_yaw);

        switch (goal->command) {
            case CMD_ENABLE:
                control_enabled_ = true;
                ROS_INFO("[Command] Balance control ENABLED");
                break;

            case CMD_DISABLE:
            case CMD_STOP:
                control_enabled_ = false;
                sendZeroTorque();
                ROS_INFO("[Command] Balance control DISABLED");
                break;

            case CMD_SWITCH_ALGO: {
                std::string algo_name;
                switch (goal->algorithm) {
                    case ALGORITHM_LQR: algo_name = "LQR"; break;
                    case ALGORITHM_VMC: algo_name = "VMC"; break;
                    case ALGORITHM_MPC: algo_name = "MPC"; break;
                    case ALGORITHM_ADP: algo_name = "ADP"; break;
                    default: algo_name = "LQR"; break;
                }
                if (algorithms_.find(algo_name) != algorithms_.end()) {
                    current_algorithm_ = algorithms_[algo_name];
                    ROS_INFO("[Command] Switched to: %s", algo_name.c_str());
                }
                break;
            }

            case CMD_SET_TARGET:
                control_enabled_ = true;
                target_roll_ = goal->target_roll;
                target_pitch_ = goal->target_pitch;
                target_yaw_ = goal->target_yaw;
                ROS_INFO("[Command] Target: roll=%.3f, pitch=%.3f, yaw=%.3f",
                         target_roll_, target_pitch_, target_yaw_);

                // Also switch algorithm if specified
                if (goal->algorithm > 0) {
                    std::string algo_name;
                    switch (goal->algorithm) {
                        case ALGORITHM_LQR: algo_name = "LQR"; break;
                        case ALGORITHM_VMC: algo_name = "VMC"; break;
                        case ALGORITHM_MPC: algo_name = "MPC"; break;
                        case ALGORITHM_ADP: algo_name = "ADP"; break;
                        default: algo_name = "LQR";
                    }
                    if (algorithms_.find(algo_name) != algorithms_.end()) {
                        current_algorithm_ = algorithms_[algo_name];
                    }
                }
                break;

            default:
                ROS_WARN("[Command] Unknown command: %d", goal->command);
                break;
        }

        feedback.current_roll = roll_;
        feedback.current_pitch = pitch_;
        feedback.current_yaw = yaw_;
        feedback.algorithm_name = current_algorithm_->getName();
        feedback.control_enabled = control_enabled_;
        feedback.status_message = "Command processed";
        action_server_.publishFeedback(feedback);

        result.success = true;
        result.message = "Goal processed";
        action_server_.setSucceeded(result);

        ROS_INFO("Control: %s, Algorithm: %s",
                 control_enabled_ ? "enabled" : "disabled",
                 current_algorithm_->getName().c_str());
        ROS_INFO("==========================================");
    }

    void update() {
        std::lock_guard<std::mutex> lock(state_mutex_);

        if (!control_enabled_ || !imu_received_) {
            return;
        }

        // 6维状态: [roll, pitch, yaw, omega_x, omega_y, omega_z]
        Eigen::VectorXd state(6);
        state << roll_, pitch_, yaw_,
                 angular_vel_x_, angular_vel_y_, angular_vel_z_;

        Eigen::VectorXd target(6);
        target << target_roll_, target_pitch_, target_yaw_, 0.0, 0.0, 0.0;

        Eigen::VectorXd output(8);
        output.setZero();
        current_algorithm_->computeControl(state, target, output);

        publishMotorCommands(output, "SPEED");
    }

    void publishMotorCommands(const Eigen::VectorXd& torques, const std::string& mode) {
        for (size_t i = 0; i < motor_configs_.size() && i < 8; ++i) {
            const auto& config = motor_configs_[i];

            dcu_driver_pkg::MotorCommand cmd;
            cmd.cmd = 4;  // MIT 模式
            cmd.motor_id = config.motor_id;
            cmd.channel = config.channel;
            cmd.q = 0.0;
            cmd.dq = 0.0;

            // 轮子使用速度接口 (VelocityJointInterface)
            if (config.joint == WHEEL && mode == "SPEED") {
                cmd.tau = 0.0;
                cmd.kp = 0.0;
                cmd.kd = 0.0;
                cmd.dq = torques(i);
            } else {
                // 力矩控制 (乘以方向因子)
                cmd.tau = torques(i) * config.direction;
                cmd.kp = 20.0;
                cmd.kd = 2.0;
            }

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
        ROS_DEBUG("Zero torque sent");
    }

    void spin() {
        ros::Rate rate(500);
        ROS_INFO("Entering control loop (500Hz)");

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
        ROS_INFO("[Debug] Omega: wx=%.3f, wy=%.3f, wz=%.3f",
                 angular_vel_x_, angular_vel_y_, angular_vel_z_);
        ROS_INFO("[Debug] Target: roll=%.3f, pitch=%.3f, yaw=%.3f",
                 target_roll_, target_pitch_, target_yaw_);
        ROS_INFO("[Debug] Control: %s | Algo: %s | IMU: %s",
                 control_enabled_ ? "ENABLED" : "DISABLED",
                 current_algorithm_->getName().c_str(),
                 imu_received_ ? "OK" : "NO DATA");

        Eigen::VectorXd state(6);
        state << roll_, pitch_, yaw_, angular_vel_x_, angular_vel_y_, angular_vel_z_;
        Eigen::VectorXd target(6);
        target << target_roll_, target_pitch_, target_yaw_, 0.0, 0.0, 0.0;
        Eigen::VectorXd output(8);
        output.setZero();
        current_algorithm_->computeControl(state, target, output);

        ROS_INFO("[Debug] Motor Torques:");
        for (size_t i = 0; i < motor_configs_.size() && i < 8; ++i) {
            ROS_INFO("  [%zu] %-20s tau=%7.3f Nm", i,
                     motor_configs_[i].name.c_str(), output(i));
        }
        ROS_INFO("----------------------------------------");
    }

private:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<balance_control::BalanceControlAction> action_server_;
    ros::Subscriber imu_sub_;
    ros::Subscriber joint_states_sub_;
    ros::Publisher motor_cmd_pub_;

    std::mutex state_mutex_;
    double roll_, pitch_, yaw_;
    double angular_vel_x_, angular_vel_y_, angular_vel_z_;
    double target_roll_, target_pitch_, target_yaw_;
    bool control_enabled_;
    bool imu_received_;
    double last_imu_time_;

    std::vector<double> joint_positions_;
    std::vector<double> joint_velocities_;

    std::map<std::string, std::shared_ptr<BalanceAlgorithm>> algorithms_;
    std::shared_ptr<BalanceAlgorithm> current_algorithm_;
    std::vector<MotorChanConfig> motor_configs_;
    RobotHardwareParams params_;

    int print_counter_;
    static constexpr int PRINT_INTERVAL = 50;
};

} // namespace balance_control

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
