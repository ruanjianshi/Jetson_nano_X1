/*
 * DCU CANFD Forwarding Test
 * 
 * This test specifically verifies DCU's CANFD message forwarding capability.
 * The DCU requires correct 'Cmd' field configuration to forward messages to CANFD bus.
 * 
 * Cmd values:
 *   - 0xFF: Broadcast mode - forwards all 64 bytes to CAN ID 0
 *   - 0x00: Silent mode - no forwarding
 *   - bitN=1: Forward to CAN ID N+1 (e.g., bit2=1 for CAN ID 3)
 */

#include <cstdint>
#include <iostream>
#include <thread>
#include <chrono>
#include <iomanip>
#include <signal.h>
#include <atomic>

#include "xyber_controller.h"

using namespace xyber;
using namespace std::chrono_literals;

static std::atomic<bool> g_running{true};

void signal_handler(int sig) {
    g_running = false;
}

void print_hex(const uint8_t* data, size_t len, const std::string& desc) {
    std::cout << desc << ": ";
    for (size_t i = 0; i < len && i < 64; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)data[i] << " ";
    }
    std::cout << std::dec << std::endl;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    
    std::string ifname = "eth0";
    std::string motor_name = "joint3";
    uint8_t can_id = 3;
    
    if (argc > 1) ifname = argv[1];
    if (argc > 2) motor_name = argv[2];
    if (argc > 3) can_id = std::stoi(argv[3]);
    
    std::cout << "========================================" << std::endl;
    std::cout << "  DCU CANFD Forwarding Test" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Interface: " << ifname << std::endl;
    std::cout << "Motor: " << motor_name << std::endl;
    std::cout << "CAN ID: " << (int)can_id << std::endl;
    std::cout << "========================================" << std::endl;
    
    XyberController* ctrl = XyberController::GetInstance();
    if (!ctrl) {
        std::cerr << "Failed to get XyberController instance" << std::endl;
        return 1;
    }
    
    std::cout << "[1/6] Creating DCU 'dcu1' with EtherCAT ID 1..." << std::endl;
    if (!ctrl->CreateDcu("dcu1", 1)) {
        std::cerr << "Failed to create DCU" << std::endl;
        return 1;
    }
    std::cout << "      DCU created successfully" << std::endl;
    
    std::cout << "[2/6] Attaching actuator to DCU CTRL1..." << std::endl;
    if (!ctrl->AttachActuator("dcu1", CtrlChannel::CTRL_CH1, 
                              ActuatorType::POWER_FLOW_R86,
                              motor_name, can_id)) {
        std::cerr << "Failed to attach actuator" << std::endl;
        return 1;
    }
    std::cout << "      Actuator '" << motor_name << "' attached (CAN ID=" << (int)can_id << ")" << std::endl;
    
    std::cout << "[3/6] Starting EtherCAT communication..." << std::endl;
    ctrl->SetRealtime(90, 1);
    if (!ctrl->Start(ifname, 1000000, true)) {
        std::cerr << "Failed to start EtherCAT" << std::endl;
        return 1;
    }
    std::cout << "      EtherCAT started successfully" << std::endl;
    
    std::this_thread::sleep_for(2s);
    
    std::cout << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "  TEST PHASE" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Watch your CAN analyzer for incoming frames" << std::endl;
    std::cout << std::endl;
    
    // Test 1: Read initial state
    std::cout << "[TEST 1] Reading initial motor state..." << std::endl;
    float pos = ctrl->GetPosition(motor_name);
    float vel = ctrl->GetVelocity(motor_name);
    float effort = ctrl->GetEffort(motor_name);
    auto state = ctrl->GetPowerState(motor_name);
    auto mode = ctrl->GetMode(motor_name);
    std::cout << "  Position: " << pos << " rad" << std::endl;
    std::cout << "  Velocity: " << vel << " rad/s" << std::endl;
    std::cout << "  Effort: " << effort << " Nm" << std::endl;
    std::cout << "  State: " << (int)state << ", Mode: " << (int)mode << std::endl;
    std::cout << std::endl;
    
    // Test 2: Set MIT Mode
    std::cout << "[TEST 2] Setting MIT mode (0x0B, 0x06)..." << std::endl;
    std::cout << "  Expected on CAN: [0B 06] command" << std::endl;
    if (ctrl->SetMode(motor_name, ActautorMode::MODE_MIT)) {
        std::cout << "  SetMode: SUCCESS" << std::endl;
    } else {
        std::cout << "  SetMode: FAILED" << std::endl;
    }
    std::this_thread::sleep_for(500ms);
    mode = ctrl->GetMode(motor_name);
    std::cout << "  Current mode: " << (int)mode << " (expected 6)" << std::endl;
    std::cout << std::endl;
    
    // Test 3: Enable Actuator
    std::cout << "[TEST 3] Sending Enable command (0x01, 0x01)..." << std::endl;
    std::cout << "  Expected on CAN: [01 01] command (5 times)" << std::endl;
    for (int i = 0; i < 5; ++i) {
        ctrl->EnableActuator(motor_name);
        std::cout << "  Enable attempt " << (i+1) << " sent" << std::endl;
        std::this_thread::sleep_for(100ms);
    }
    std::this_thread::sleep_for(500ms);
    state = ctrl->GetPowerState(motor_name);
    std::cout << "  State after enable: " << (int)state << std::endl;
    std::cout << std::endl;
    
    // Test 4: Send MIT Commands (Broadcast mode)
    std::cout << "[TEST 4] Sending MIT position commands (Broadcast mode)..." << std::endl;
    std::cout << "  Expected on CAN: ID=0, 64 bytes, MIT format data" << std::endl;
    std::cout << "  This uses Cmd=0xFF (broadcast) to force DCU forwarding" << std::endl;
    std::cout << std::endl;
    
    for (int i = 0; i < 10 && g_running; ++i) {
        float target_pos = (i % 2 == 0) ? 0.0f : 3.14f;
        std::cout << "  Step " << i << ": Sending pos=" << target_pos << std::endl;
        ctrl->SetMitCmd(motor_name, target_pos, 0.0f, 0.0f, 10.0f, 1.0f);
        std::this_thread::sleep_for(500ms);
    }
    
    // while (1) {
    //     float target_pos = 1.57f; // Example position command
    //     std::cout << "  Sending MIT pos=" << target_pos << std::endl;
    //     ctrl->SetMitCmd(motor_name, target_pos, 0.0f, 0.0f, 10.0f, 1.0f);
    //     std::this_thread::sleep_for(1ms);
    // }
    std::cout << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "  TEST COMPLETE" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "If CAN analyzer showed NO frames:" << std::endl;
    std::cout << "  1. Check DCU firmware supports broadcast forwarding" << std::endl;
    std::cout << "  2. Verify CANFD baudrate matches (1M/5M)" << std::endl;
    std::cout << "  3. Check physical CAN connection" << std::endl;
    std::cout << std::endl;
    std::cout << "If CAN analyzer showed frames:" << std::endl;
    std::cout << "  - Note the CAN ID used (0 for broadcast, " << (int)can_id << " for unicast)" << std::endl;
    std::cout << "  - Note the data format" << std::endl;
    std::cout << std::endl;
    
    std::cout << "Keeping process alive... Press Ctrl+C to exit" << std::endl;
    while (g_running) {
        std::this_thread::sleep_for(1s);
    }
    
    ctrl->Stop();
    std::cout << "Exiting..." << std::endl;
    return 0;
}