/*
 * DCU Driver Server Node - Topic based control
 */

#include <ros/ros.h>
#include <std_msgs/Float64MultiArray.h>
#include <sensor_msgs/JointState.h>
#include <actionlib/server/simple_action_server.h>
#include <dcu_driver_pkg/DCUControlAction.h>
#include <xyber_controller.h>
#include <common_type.h>
#include <vector>
#include <thread>

struct MotorConfig {
    std::string name;
    uint8_t ethercat_id;
    uint8_t can_node_id;
    xyber::CtrlChannel can_channel;
    xyber::ActuatorType actuator_type;
};

class DCUDriverServer
{
public:
    DCUDriverServer()
        : action_server_(nh_, "dcu_control", 
            boost::bind(&DCUDriverServer::executeCB, this, _1), false)
        , xyber_ctrl_(nullptr)
        , is_running_(false)
    {
        cmd_sub_ = nh_.subscribe("/dcu_cmd", 10, &DCUDriverServer::cmdCB, this);
        joint_states_pub_ = nh_.advertise<sensor_msgs::JointState>("/joint_states", 100);
        
        loadMotorConfig();
        action_server_.start();
        ROS_INFO("DCU Driver Server started");
    }

    ~DCUDriverServer()
    {
        stop();
    }

    void loadMotorConfig()
    {
        XmlRpc::XmlRpcValue motor_list;
        if (!nh_.getParam("motors", motor_list)) {
            ROS_WARN("No motors configured, using default (joint3, CAN ID=3)");
            motors_.push_back({"joint3", 1, 3, xyber::CtrlChannel::CTRL_CH1, 
                              xyber::ActuatorType::POWER_FLOW_R86});
            motor_names_.push_back("joint3");
            return;
        }

        for (int i = 0; i < motor_list.size(); ++i) {
            XmlRpc::XmlRpcValue& m = motor_list[i];
            MotorConfig motor;
            motor.name = static_cast<std::string>(m["name"]);
            motor.ethercat_id = static_cast<int>(m["ethercat_id"]);
            motor.can_node_id = static_cast<int>(m["can_node_id"]);
            
            std::string channel = static_cast<std::string>(m["can_channel"]);
            if (channel == "CTRL1") motor.can_channel = xyber::CtrlChannel::CTRL_CH1;
            else if (channel == "CTRL2") motor.can_channel = xyber::CtrlChannel::CTRL_CH2;
            else motor.can_channel = xyber::CtrlChannel::CTRL_CH3;

            std::string type = static_cast<std::string>(m["actuator_type"]);
            motor.actuator_type = xyber::StringToType(type);
            motors_.push_back(motor);
            motor_names_.push_back(motor.name);
        }
    }

    bool init()
    {
        xyber_ctrl_ = xyber::XyberController::GetInstance();
        return (xyber_ctrl_ != nullptr);
    }

    bool start(const std::string& ifname, bool enable_dc, uint64_t cycle_ns)
    {
        if (xyber_ctrl_ == nullptr) {
            ROS_ERROR("Controller not initialized");
            return false;
        }

        std::map<uint8_t, std::string> dcu_map;
        for (const auto& m : motors_) {
            dcu_map[m.ethercat_id] = "dcu" + std::to_string(m.ethercat_id);
        }

        for (const auto& [ecat_id, dcu_name] : dcu_map) {
            if (!xyber_ctrl_->CreateDcu(dcu_name, ecat_id)) {
                ROS_ERROR("Failed to create DCU: %s", dcu_name.c_str());
                return false;
            }
        }

        for (const auto& m : motors_) {
            std::string dcu_name = "dcu" + std::to_string(m.ethercat_id);
            if (!xyber_ctrl_->AttachActuator(dcu_name, m.can_channel, 
                                            m.actuator_type, m.name, m.can_node_id)) {
                ROS_ERROR("Failed to attach actuator: %s", m.name.c_str());
                return false;
            }
        }

        xyber_ctrl_->SetRealtime(90, 1);

        if (!xyber_ctrl_->Start(ifname, cycle_ns, enable_dc)) {
            ROS_ERROR("Failed to start EtherCAT");
            return false;
        }

        ros::Duration(2.0).sleep();

        ROS_INFO("Setting MIT mode...");
        for (const auto& name : motor_names_) {
            xyber_ctrl_->SetMode(name, xyber::ActautorMode::MODE_MIT);
            ros::Duration(0.05).sleep();
        }

        ros::Duration(0.5).sleep();

        ROS_INFO("Sending Enable commands...");
        for (const auto& name : motor_names_) {
            for (int i = 0; i < 5; ++i) {
                xyber_ctrl_->EnableActuator(name);
                ros::Duration(0.1).sleep();
            }
        }

        ros::Duration(0.5).sleep();

        for (const auto& name : motor_names_) {
            auto state = xyber_ctrl_->GetPowerState(name);
            auto mode = xyber_ctrl_->GetMode(name);
            ROS_INFO("Motor %s: state=%d, mode=%d", name.c_str(), (int)state, (int)mode);
        }

        is_running_ = true;
        ROS_INFO("DCU Driver running with %zu motors", motors_.size());
        
        mit_pos_ = 0.0f;
        mit_kp_ = 10.0f;
        mit_kd_ = 1.0f;
        startMitLoop();
        
        return true;
    }

    void stop()
    {
        is_running_ = false;
        if (mit_thread_.joinable()) mit_thread_.join();
        if (xyber_ctrl_ != nullptr) xyber_ctrl_->Stop();
    }

    void startMitLoop()
    {
        if (mit_thread_.joinable()) mit_thread_.join();
        
        mit_thread_ = std::thread([this]() {
            while (is_running_ && ros::ok()) {
                for (const auto& name : motor_names_) {
                    xyber_ctrl_->SetMitCmd(name, mit_pos_, 0.0f, 0.0f, mit_kp_, mit_kd_);
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        });
    }

    void cmdCB(const std_msgs::Float64MultiArray::ConstPtr& msg)
    {
        if (msg->data.empty()) return;
        
        mit_pos_ = msg->data[0];
        mit_kp_ = (msg->data.size() > 1) ? msg->data[1] : 10.0f;
        mit_kd_ = (msg->data.size() > 2) ? msg->data[2] : 1.0f;
        
        ROS_INFO("Received cmd: pos=%.3f, kp=%.1f, kd=%.1f", mit_pos_, mit_kp_, mit_kd_);
    }

    void executeCB(const dcu_driver_pkg::DCUControlGoalConstPtr& goal)
    {
        dcu_driver_pkg::DCUControlResult result;
        dcu_driver_pkg::DCUControlFeedback feedback;

        ROS_INFO("Action goal received: %zu joints", goal->joint_names.size());

        if (goal->joint_names.size() != goal->positions.size()) {
            result.success = false;
            result.message = "Size mismatch";
            action_server_.setAborted(result);
            return;
        }

        float pos = static_cast<float>(goal->positions[0]);
        float kp = (goal->stiffness.size() > 0) ? static_cast<float>(goal->stiffness[0]) : 10.0f;
        float kd = (goal->damping.size() > 0) ? static_cast<float>(goal->damping[0]) : 1.0f;

        ROS_INFO("Action: sending MIT cmd for 5s: pos=%.3f, kp=%.1f, kd=%.1f", pos, kp, kd);

        mit_pos_ = pos;
        mit_kp_ = kp;
        mit_kd_ = kd;

        ros::Time start = ros::Time::now();
        while ((ros::Time::now() - start).toSec() < 5.0 && ros::ok()) {
            for (const auto& name : motor_names_) {
                xyber_ctrl_->SetMitCmd(name, mit_pos_, 0.0f, 0.0f, mit_kp_, mit_kd_);
            }
            ros::Duration(0.001).sleep();
        }

        feedback.current_positions.push_back(xyber_ctrl_->GetPosition(motor_names_[0]));
        feedback.current_velocities.push_back(xyber_ctrl_->GetVelocity(motor_names_[0]));
        feedback.current_efforts.push_back(xyber_ctrl_->GetEffort(motor_names_[0]));

        action_server_.publishFeedback(feedback);
        result.success = true;
        result.message = "Command executed";
        action_server_.setSucceeded(result);
    }

    void publishStates()
    {
        if (!is_running_) return;
        
        sensor_msgs::JointState joint_state;
        joint_state.header.stamp = ros::Time::now();

        for (const auto& name : motor_names_) {
            joint_state.name.push_back(name);
            joint_state.position.push_back(xyber_ctrl_->GetPosition(name));
            joint_state.velocity.push_back(xyber_ctrl_->GetVelocity(name));
            joint_state.effort.push_back(xyber_ctrl_->GetEffort(name));
        }
        joint_states_pub_.publish(joint_state);
    }

    void spin()
    {
        ros::Rate rate(100);
        while (ros::ok()) {
            ros::spinOnce();
            if (is_running_) {
                publishStates();
            }
            rate.sleep();
        }
    }

private:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<dcu_driver_pkg::DCUControlAction> action_server_;
    ros::Subscriber cmd_sub_;
    ros::Publisher joint_states_pub_;
    
    xyber::XyberController* xyber_ctrl_;
    std::vector<MotorConfig> motors_;
    std::vector<std::string> motor_names_;
    std::thread mit_thread_;
    bool is_running_;
    
    float mit_pos_ = 0.0f;
    float mit_kp_ = 10.0f;
    float mit_kd_ = 1.0f;
};

int main(int argc, char** argv)
{
    ros::init(argc, argv, "dcu_driver_server");
    ros::NodeHandle nh;

    std::string ifname = "eth0";
    bool enable_dc = true;
    int cycle_ns = 1000000;

    nh.getParam("ethercat_if", ifname);
    nh.getParam("enable_dc", enable_dc);
    nh.getParam("cycle_ns", cycle_ns);

    DCUDriverServer server;

    if (!server.init()) {
        ROS_ERROR("Failed to initialize");
        return 1;
    }

    if (!server.start(ifname, enable_dc, cycle_ns)) {
        ROS_ERROR("Failed to start EtherCAT");
        return 1;
    }

    server.spin();
    return 0;
}