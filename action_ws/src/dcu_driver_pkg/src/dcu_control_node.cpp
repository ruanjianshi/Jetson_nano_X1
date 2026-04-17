/*
 * Simple Topic-based DCU Control
 */

#include <ros/ros.h>
#include <std_msgs/Float64MultiArray.h>
#include <sensor_msgs/JointState.h>
#include <xyber_controller.h>
#include <common_type.h>
#include <vector>

class DCUControlNode
{
public:
    DCUControlNode()
        : nh_("~")
    {
        cmd_sub_ = nh_.subscribe("/dcu_cmd", 10, &DCUControlNode::cmdCB, this);
        joint_state_pub_ = nh_.advertise<sensor_msgs::JointState>("/joint_states", 100);
        
        loadMotorConfig();
        init();
        
        if (start("eth0", true, 1000000)) {
            ROS_INFO("DCU Control Node started successfully");
        } else {
            ROS_ERROR("Failed to start DCU");
        }
    }
    
    ~DCUControlNode() {
        if (xyber_ctrl_) xyber_ctrl_->Stop();
    }
    
    void loadMotorConfig()
    {
        XmlRpc::XmlRpcValue motor_list;
        if (!nh_.getParam("motors", motor_list)) {
            motors_.push_back({"joint1", 1, 3, xyber::CtrlChannel::CTRL_CH1, 
                              xyber::ActuatorType::POWER_FLOW_R86});
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
        std::map<uint8_t, std::string> dcu_map;
        for (const auto& m : motors_) {
            dcu_map[m.ethercat_id] = "dcu" + std::to_string(m.ethercat_id);
        }
        
        for (const auto& [ecat_id, dcu_name] : dcu_map) {
            if (!xyber_ctrl_->CreateDcu(dcu_name, ecat_id)) return false;
        }
        
        for (const auto& m : motors_) {
            std::string dcu_name = "dcu" + std::to_string(m.ethercat_id);
            if (!xyber_ctrl_->AttachActuator(dcu_name, m.can_channel, 
                                            m.actuator_type, m.name, m.can_node_id)) return false;
        }
        
        if (!xyber_ctrl_->Start(ifname, cycle_ns, enable_dc)) return false;
        
        ros::Duration(1.0).sleep();
        
        for (const auto& name : motor_names_) {
            xyber_ctrl_->SetMode(name, xyber::ActautorMode::MODE_MIT);
            ros::Duration(0.05).sleep();
        }
        
        ros::Duration(0.5).sleep();
        
        for (const auto& name : motor_names_) {
            for (int i = 0; i < 10; ++i) {
                xyber_ctrl_->EnableActuator(name);
                ros::Duration(0.02).sleep();
            }
        }
        
        ros::Duration(0.5).sleep();
        
        for (const auto& name : motor_names_) {
            auto state = xyber_ctrl_->GetPowerState(name);
            auto mode = xyber_ctrl_->GetMode(name);
            ROS_INFO("Motor %s: state=%d, mode=%d", name.c_str(), (int)state, (int)mode);
        }
        
        return true;
    }
    
    void cmdCB(const std_msgs::Float64MultiArray::ConstPtr& msg)
    {
        if (msg->data.size() < 3) {
            ROS_WARN("Command needs at least 3 values: pos, kp, kd");
            return;
        }
        
        float pos = msg->data[0];
        float kp = msg->data.size() > 1 ? msg->data[1] : 10.0f;
        float kd = msg->data.size() > 2 ? msg->data[2] : 1.0f;
        
        ROS_INFO("Received cmd: pos=%.3f, kp=%.1f, kd=%.1f", pos, kp, kd);
        
        for (const auto& name : motor_names_) {
            xyber_ctrl_->SetMitCmd(name, pos, 0.0f, 0.0f, kp, kd);
        }
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
        joint_state_pub_.publish(joint_state);
    }
    
    void spin()
    {
        ros::Rate rate(100);
        while (ros::ok()) {
            ros::spinOnce();
            publishStates();
            rate.sleep();
        }
    }
    
private:
    ros::NodeHandle nh_;
    ros::Subscriber cmd_sub_;
    ros::Publisher joint_state_pub_;
    xyber::XyberController* xyber_ctrl_;
    
    struct MotorConfig {
        std::string name;
        uint8_t ethercat_id;
        uint8_t can_node_id;
        xyber::CtrlChannel can_channel;
        xyber::ActuatorType actuator_type;
    };
    
    std::vector<MotorConfig> motors_;
    std::vector<std::string> motor_names_;
};

int main(int argc, char** argv)
{
    ros::init(argc, argv, "dcu_control_node");
    DCUControlNode node;
    node.spin();
    return 0;
}