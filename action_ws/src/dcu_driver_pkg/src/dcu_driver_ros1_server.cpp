#include <ros/ros.h>
#include <actionlib/server/simple_action_server.h>
#include <dcu_driver_pkg/DCUControlAction.h>
#include <sensor_msgs/JointState.h>
#include <sensor_msgs/Imu.h>
#include <xyber_controller.h>
#include <common_type.h>
#include <sched.h>
#include <pthread.h>
#include <errno.h>
#include <string.h>
#include <vector>

struct MotorConfig {
    std::string name;
    uint8_t ethercat_id;
    uint8_t can_node_id;
    xyber::CtrlChannel can_channel;
    xyber::ActuatorType actuator_type;
};

class DCUDriverActionServer
{
public:
    DCUDriverActionServer()
        : action_server_(nh_, "dcu_control", boost::bind(&DCUDriverActionServer::executeCB, this, _1), false)
        , xyber_ctrl_(nullptr)
        , is_running_(false)
    {
        joint_states_pub_ = nh_.advertise<sensor_msgs::JointState>("/joint_states", 100);
        imu_data_pub_ = nh_.advertise<sensor_msgs::Imu>("/imu/data", 100);

        loadMotorConfig();

        action_server_.start();

        ROS_INFO("DCU Driver Action Server started");
    }

    ~DCUDriverActionServer()
    {
        stop();
    }

    void loadMotorConfig()
    {
        XmlRpc::XmlRpcValue motor_list;
        if (!nh_.getParam("motors", motor_list)) {
            ROS_WARN("No motors configured, using default config (1 motor R86, CAN ID=3)");
            motors_.push_back({"joint1", 1, 3, xyber::CtrlChannel::CTRL_CH1, xyber::ActuatorType::POWER_FLOW_R86});
            return;
        }

        ROS_ASSERT(motor_list.getType() == XmlRpc::XmlRpcValue::TypeArray);
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
            ROS_INFO("Loaded motor: %s (ECAT:%d, CAN:%d, Type:%s)", 
                     motor.name.c_str(), motor.ethercat_id, motor.can_node_id, type.c_str());
        }
    }

    bool init()
    {
        xyber::XyberController* ctrl = xyber::XyberController::GetInstance();
        if (ctrl == nullptr) {
            ROS_ERROR("Failed to get XyberController instance");
            return false;
        }
        xyber_ctrl_ = ctrl;
        return true;
    }

    bool start(const std::string& ifname, bool enable_dc, uint64_t cycle_ns,
               int rt_priority, int bind_cpu)
    {
        if (xyber_ctrl_ == nullptr) {
            ROS_ERROR("Controller not initialized");
            return false;
        }

        if (rt_priority > 0) {
            ROS_INFO("Setting realtime priority: %d, bind_cpu: %d", rt_priority, bind_cpu);
            xyber_ctrl_->SetRealtime(rt_priority, bind_cpu);
        }

        std::map<uint8_t, std::string> dcu_map;
        for (const auto& motor : motors_) {
            dcu_map[motor.ethercat_id] = "dcu" + std::to_string(motor.ethercat_id);
        }

        for (const auto& [ecat_id, dcu_name] : dcu_map) {
            ROS_INFO("Creating DCU: %s at EtherCAT ID %d", dcu_name.c_str(), ecat_id);
            if (!xyber_ctrl_->CreateDcu(dcu_name, ecat_id)) {
                ROS_ERROR("Failed to create DCU: %s", dcu_name.c_str());
                return false;
            }
        }

        for (const auto& motor : motors_) {
            std::string dcu_name = "dcu" + std::to_string(motor.ethercat_id);
            ROS_INFO("Attaching actuator: %s to %s (CAN ID: %d)", 
                     motor.name.c_str(), dcu_name.c_str(), motor.can_node_id);
            if (!xyber_ctrl_->AttachActuator(dcu_name, motor.can_channel, 
                                            motor.actuator_type, motor.name, motor.can_node_id)) {
                ROS_ERROR("Failed to attach actuator: %s", motor.name.c_str());
                return false;
            }
            motor_names_.push_back(motor.name);
        }

        if (!xyber_ctrl_->Start(ifname, cycle_ns, enable_dc)) {
            ROS_ERROR("Failed to start EtherCAT");
            return false;
        }

        ros::Duration(2.0).sleep();

ROS_INFO("Testing initial motor state...");
        for (const auto& name : motor_names_) {
            float pos = xyber_ctrl_->GetPosition(name);
            float vel = xyber_ctrl_->GetVelocity(name);
            float effort = xyber_ctrl_->GetEffort(name);
            xyber::ActautorState state = xyber_ctrl_->GetPowerState(name);
            xyber::ActautorMode mode = xyber_ctrl_->GetMode(name);
            ROS_INFO("  %s - pos: %.3f, vel: %.3f, effort: %.3f, state: %d, mode: %d", 
                     name.c_str(), pos, vel, effort, (int)state, (int)mode);
        }

ROS_INFO("Setting MIT mode for all motors...");
        for (const auto& name : motor_names_) {
            xyber_ctrl_->SetMode(name, xyber::MODE_MIT);
            xyber::ActautorMode mode = xyber_ctrl_->GetMode(name);
            ROS_INFO("  %s set to MIT mode, current mode=%d", name.c_str(), (int)mode);
        }

        ros::Duration(0.5).sleep();

        ROS_INFO("Checking mode before MIT commands...");
        for (const auto& name : motor_names_) {
            xyber::ActautorMode mode = xyber_ctrl_->GetMode(name);
            ROS_INFO("  %s mode: %d", name.c_str(), (int)mode);
        }

ROS_INFO("Sending enable commands...");
        for (int i = 0; i < 10; i++) {
            xyber_ctrl_->EnableActuator(motor_names_[0]);
            ros::Duration(0.02).sleep();
        }

        ros::Duration(1.0).sleep();

        ROS_INFO("Checking mode before MIT commands...");
        for (const auto& name : motor_names_) {
            xyber::ActautorMode mode = xyber_ctrl_->GetMode(name);
            ROS_INFO("  %s mode: %d", name.c_str(), (int)mode);
        }

        ros::Duration(1.0).sleep();

        ROS_INFO("Testing MIT commands - sending step position changes...");
        for (int i = 0; i < 10; i++) {
            float target_pos = (i % 2 == 0) ? 0.0 : 3.14;
            for (const auto& name : motor_names_) {
                xyber_ctrl_->SetMitCmd(name, target_pos, 0.0, 0.0, 10.0, 1.0);
            }
            ros::Duration(0.5).sleep();
            
            float pos = xyber_ctrl_->GetPosition(motor_names_[0]);
            ROS_INFO("  Step %d: target=%.2f, actual=%.3f", i, target_pos, pos);
        }

        ROS_INFO("Checking final motor state...");
        for (const auto& name : motor_names_) {
            xyber::ActautorState state = xyber_ctrl_->GetPowerState(name);
            ROS_INFO("  %s final state: %d", name.c_str(), (int)state);
        }

        is_running_ = true;
        ROS_INFO("DCU Driver started with %zu motors", motors_.size());
        return true;
    }

    void stop()
    {
        if (xyber_ctrl_ != nullptr) {
            xyber_ctrl_->Stop();
        }
        is_running_ = false;
        ROS_INFO("DCU Driver stopped");
    }

    void executeCB(const dcu_driver_pkg::DCUControlGoalConstPtr& goal)
    {
        dcu_driver_pkg::DCUControlResult result;
        dcu_driver_pkg::DCUControlFeedback feedback;

        ROS_INFO("Received DCU control goal with %zu joints", goal->joint_names.size());

        if (goal->joint_names.size() != goal->positions.size()) {
            result.success = false;
            result.message = "joint_names and positions size mismatch";
            action_server_.setAborted(result);
            return;
        }

        for (size_t i = 0; i < goal->joint_names.size(); ++i) {
            float pos = static_cast<float>(goal->positions[i]);
            float vel = i < goal->velocities.size() ? static_cast<float>(goal->velocities[i]) : 0.0f;
            float effort = i < goal->efforts.size() ? static_cast<float>(goal->efforts[i]) : 0.0f;
            float kp = i < goal->stiffness.size() ? static_cast<float>(goal->stiffness[i]) : 0.0f;
            float kd = i < goal->damping.size() ? static_cast<float>(goal->damping[i]) : 0.0f;

            xyber_ctrl_->SetMitCmd(goal->joint_names[i], pos, vel, effort, kp, kd);

            feedback.current_positions.push_back(pos);
            feedback.current_velocities.push_back(vel);
            feedback.current_efforts.push_back(effort);
        }

        action_server_.publishFeedback(feedback);
        ros::Duration(0.01).sleep();

        result.success = true;
        result.message = "Control command executed";
        action_server_.setSucceeded(result);
    }

    void publishStates()
    {
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

    xyber::XyberController* xyber_ctrl_;
    std::vector<MotorConfig> motors_;
    std::vector<std::string> motor_names_;
    bool is_running_;

    ros::Publisher joint_states_pub_;
    ros::Publisher imu_data_pub_;
};

static bool setRealtimeScheduler(int priority)
{
    if (priority <= 0) {
        ROS_INFO("Realtime scheduling disabled");
        return true;
    }

    struct sched_param param;
    memset(&param, 0, sizeof(param));
    param.sched_priority = priority;

    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &param) != 0) {
        ROS_WARN("Failed to set SCHED_FIFO: %s", strerror(errno));
        return false;
    }

    ROS_INFO("Set realtime scheduler: SCHED_FIFO priority=%d", priority);
    return true;
}

int main(int argc, char** argv)
{
    ros::init(argc, argv, "dcu_driver_server");
    ros::NodeHandle nh;

    std::string ifname = "eth0";
    bool enable_dc = true;
    int cycle_ns_int = 1000000;
    int rt_priority = -1;
    int bind_cpu = -1;

    nh.getParam("ethercat_if", ifname);
    nh.getParam("enable_dc", enable_dc);
    nh.getParam("cycle_ns", cycle_ns_int);
    nh.getParam("rt_priority", rt_priority);
    nh.getParam("bind_cpu", bind_cpu);

    setRealtimeScheduler(rt_priority > 0 ? rt_priority : 0);

    uint64_t cycle_ns = static_cast<uint64_t>(cycle_ns_int);

    DCUDriverActionServer server;

    if (!server.init()) {
        ROS_ERROR("Failed to initialize DCU driver");
        return 1;
    }

    if (!server.start(ifname, enable_dc, cycle_ns, rt_priority, bind_cpu)) {
        ROS_WARN("Failed to start EtherCAT - running in simulation mode");
    }

    server.spin();
    server.stop();

    return 0;
}
