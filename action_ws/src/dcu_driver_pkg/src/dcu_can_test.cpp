/*
 * DCU CAN Communication Test Node
 * Tests if DCU is sending CAN messages by sending commands and checking output
 */

#include <ros/ros.h>
#include <xyber_controller.h>
#include <common_type.h>
#include <thread>
#include <chrono>

int main(int argc, char** argv)
{
    ros::init(argc, argv, "dcu_can_test");
    ros::NodeHandle nh;
    
    std::string ifname = "eth0";
    std::string motor_name = "joint3";
    int can_id_int = 3;
    
    nh.getParam("ethercat_if", ifname);
    nh.getParam("motor_name", motor_name);
    nh.getParam("can_id", can_id_int);
    uint8_t can_id = static_cast<uint8_t>(can_id_int);
    
    ROS_INFO("=== DCU CAN Test ===");
    ROS_INFO("Interface: %s", ifname.c_str());
    ROS_INFO("Motor: %s, CAN ID: %d", motor_name.c_str(), can_id);
    
    // Get XyberController instance
    xyber::XyberController* ctrl = xyber::XyberController::GetInstance();
    if (!ctrl) {
        ROS_ERROR("Failed to get XyberController instance");
        return 1;
    }
    ROS_INFO("XyberController instance created");
    
    // Create DCU
    if (!ctrl->CreateDcu("dcu1", 1)) {
        ROS_ERROR("Failed to create DCU");
        return 1;
    }
    ROS_INFO("DCU created");
    
    // Attach actuator
    if (!ctrl->AttachActuator("dcu1", xyber::CtrlChannel::CTRL_CH1,
                               xyber::ActuatorType::POWER_FLOW_R86,
                               motor_name, can_id)) {
        ROS_ERROR("Failed to attach actuator");
        return 1;
    }
    ROS_INFO("Actuator attached: %s (CAN ID: %d)", motor_name.c_str(), can_id);
    
    // Start EtherCAT
    if (!ctrl->Start(ifname, 1000000, true)) {
        ROS_ERROR("Failed to start EtherCAT");
        return 1;
    }
    ROS_INFO("EtherCAT started");
    
    // Wait for initialization
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    ROS_INFO("");
    ROS_INFO("=== Test 1: Read Initial State ===");
    float pos = ctrl->GetPosition(motor_name);
    float vel = ctrl->GetVelocity(motor_name);
    float effort = ctrl->GetEffort(motor_name);
    xyber::ActautorState state = ctrl->GetPowerState(motor_name);
    xyber::ActautorMode mode = ctrl->GetMode(motor_name);
    ROS_INFO("Position: %.3f rad", pos);
    ROS_INFO("Velocity: %.3f rad/s", vel);
    ROS_INFO("Effort: %.3f Nm", effort);
    ROS_INFO("State: %d, Mode: %d", (int)state, (int)mode);
    
    ROS_INFO("");
    ROS_INFO("=== Test 2: Set MIT Mode (0x0B, 0x06) ===");
    ROS_INFO("Watch CAN analyzer for: [0B 06 ...]");
    if (ctrl->SetMode(motor_name, xyber::ActautorMode::MODE_MIT)) {
        ROS_INFO("SetMode SUCCESS");
    } else {
        ROS_ERROR("SetMode FAILED");
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    mode = ctrl->GetMode(motor_name);
    ROS_INFO("Mode after SetMode: %d (expected 6)", (int)mode);
    
    ROS_INFO("");
    ROS_INFO("=== Test 3: Send Enable Command (0x01, 0x01) ===");
    ROS_INFO("Watch CAN analyzer for: [01 01 ...]");
    for (int i = 0; i < 5; i++) {
        ctrl->EnableActuator(motor_name);
        ROS_INFO("Enable attempt %d sent", i + 1);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    state = ctrl->GetPowerState(motor_name);
    ROS_INFO("State after enable: %d", (int)state);
    
    ROS_INFO("");
    ROS_INFO("=== Test 4: Send MIT Position Commands ===");
    ROS_INFO("Watch CAN analyzer for MIT format data");
    
    for (int i = 0; i < 10; i++) {
        float target_pos = (i % 2 == 0) ? 0.0f : 3.14f;
        ctrl->SetMitCmd(motor_name, target_pos, 0.0f, 0.0f, 10.0f, 1.0f);
        
        pos = ctrl->GetPosition(motor_name);
        ROS_INFO("Step %d: sent pos=%.2f, read pos=%.3f", i, target_pos, pos);
        
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    
    ROS_INFO("");
    ROS_INFO("=== Test Complete ===");
    ROS_INFO("If CAN analyzer did NOT see messages, check:");
    ROS_INFO("  1. DCU CAN cable connection to CTRL1");
    ROS_INFO("  2. CAN analyzer baud rate (should be 1M/5M for CANFD)");
    ROS_INFO("  3. CAN analyzer termination resistors");
    
    // Keep running
    ros::spin();
    
    ctrl->Stop();
    return 0;
}