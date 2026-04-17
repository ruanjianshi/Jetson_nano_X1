/*
 * DCU CANFD Receive Test
 * 
 * Tests receiving data from CAN bus through DCU.
 * The DCU receives CANFD messages from motors and exposes them via EtherCAT PDO.
 * 
 * CAN Message Format (8 bytes):
 *   Byte 0-1: Position (16-bit)
 *   Byte 2-3: Velocity (12-bit) + State (4-bit)
 *   Byte 3-4: Current/Effort (12-bit)
 *   Byte 4: Heartbeat + Error flags
 *   Byte 5: State
 *   Byte 6-7: Temperature
 */

#include <cstdint>
#include <iostream>
#include <thread>
#include <chrono>
#include <iomanip>
#include <signal.h>
#include <atomic>
#include <cstring>

#include "xyber_controller.h"

using namespace xyber;
using namespace std::chrono_literals;

static std::atomic<bool> g_running{true};

void signal_handler(int sig) {
    g_running = false;
}

void print_separator() {
    std::cout << "========================================" << std::endl;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    
    std::string ifname = "eth0";
    std::string motor_name = "joint3";
    uint8_t can_id = 3;
    
    if (argc > 1) ifname = argv[1];
    if (argc > 2) motor_name = argv[2];
    if (argc > 3) can_id = std::stoi(argv[3]);
    
    print_separator();
    std::cout << "  DCU CANFD Receive Test" << std::endl;
    print_separator();
    std::cout << "Interface: " << ifname << std::endl;
    std::cout << "Motor: " << motor_name << std::endl;
    std::cout << "CAN ID: " << (int)can_id << std::endl;
    print_separator();
    
    XyberController* ctrl = XyberController::GetInstance();
    if (!ctrl) {
        std::cerr << "Failed to get XyberController instance" << std::endl;
        return 1;
    }
    
    std::cout << "[1/5] Creating DCU 'dcu1'..." << std::endl;
    if (!ctrl->CreateDcu("dcu1", 1)) {
        std::cerr << "Failed to create DCU" << std::endl;
        return 1;
    }
    std::cout << "      DCU created" << std::endl;
    
    std::cout << "[2/5] Attaching actuator..." << std::endl;
    if (!ctrl->AttachActuator("dcu1", CtrlChannel::CTRL_CH1, 
                              ActuatorType::POWER_FLOW_R86,
                              motor_name, can_id)) {
        std::cerr << "Failed to attach actuator" << std::endl;
        return 1;
    }
    std::cout << "      Actuator attached" << std::endl;
    
    std::cout << "[3/5] Starting EtherCAT..." << std::endl;
    ctrl->SetRealtime(90, 1);
    if (!ctrl->Start(ifname, 1000000, true)) {
        std::cerr << "Failed to start EtherCAT" << std::endl;
        return 1;
    }
    std::cout << "      EtherCAT started" << std::endl;
    
    std::this_thread::sleep_for(2s);
    
    std::cout << "[4/5] Enabling actuator and setting MIT mode..." << std::endl;
    
    if (ctrl->SetMode(motor_name, ActautorMode::MODE_MIT)) {
        std::cout << "      MIT mode set: SUCCESS" << std::endl;
    } else {
        std::cout << "      MIT mode set: FAILED" << std::endl;
    }
    
    for (int i = 0; i < 5; ++i) {
        ctrl->EnableActuator(motor_name);
        std::this_thread::sleep_for(100ms);
    }
    
    auto state = ctrl->GetPowerState(motor_name);
    std::cout << "      Power state: " << (int)state << std::endl;
    std::cout << std::endl;
    
    print_separator();
    std::cout << "  Receive Test - Watch for Data Updates" << std::endl;
    print_separator();
    std::cout << "Send commands and read back motor state" << std::endl;
    std::cout << "If motor is connected, you should see changing values" << std::endl;
    std::cout << "If no motor, values will be frozen or invalid" << std::endl;
    std::cout << std::endl;
    
    print_separator();
    std::cout << std::setw(6) << "Step"
              << std::setw(12) << "Position"
              << std::setw(12) << "Velocity"
              << std::setw(12) << "Effort"
              << std::setw(8) << "State"
              << std::setw(8) << "Mode"
              << std::endl;
    print_separator();
    
    int step = 0;
    while (g_running) {
        float target_pos = (step % 2 == 0) ? 0.0f : 3.14f;
        
        ctrl->SetMitCmd(motor_name, target_pos, 0.0f, 0.0f, 10.0f, 1.0f);
        
        float pos = ctrl->GetPosition(motor_name);
        float vel = ctrl->GetVelocity(motor_name);
        float effort = ctrl->GetEffort(motor_name);
        auto motor_state = ctrl->GetPowerState(motor_name);
        auto mode = ctrl->GetMode(motor_name);
        
        std::cout << std::setw(6) << step
                  << std::setw(12) << std::fixed << std::setprecision(3) << pos
                  << std::setw(12) << std::fixed << std::setprecision(3) << vel
                  << std::setw(12) << std::fixed << std::setprecision(3) << effort
                  << std::setw(8) << (int)motor_state
                  << std::setw(8) << (int)mode
                  << "  | Cmd: " << (step % 2 == 0 ? "0.0" : "3.14")
                  << std::endl;
        
        step++;
        std::this_thread::sleep_for(500ms);
    }
    
    std::cout << std::endl;
    std::cout << "Stopping..." << std::endl;
    ctrl->Stop();
    
    return 0;
}