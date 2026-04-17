/*
 * DCU CANFD Raw Data Receive Test
 * 
 * Tests receiving raw CANFD data from DCU without sending commands.
 * Uses the GetRawCanfdData API to access raw received bytes.
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

void print_hex(const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)data[i] << " ";
    }
    std::cout << std::dec << std::endl;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    
    std::string ifname = "eth0";
    std::string motor_name = "joint3";
    uint8_t can_id = 3;
    int channel = 0;  // 0=CTRL1, 1=CTRL2, 2=CTRL3
    
    if (argc > 1) ifname = argv[1];
    if (argc > 2) motor_name = argv[2];
    if (argc > 3) can_id = std::stoi(argv[3]);
    if (argc > 4) channel = std::stoi(argv[4]);
    
    std::cout << "========================================" << std::endl;
    std::cout << "  DCU CANFD Raw Receive Test" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Interface: " << ifname << std::endl;
    std::cout << "Motor: " << motor_name << " (CAN ID " << (int)can_id << ")" << std::endl;
    std::cout << "Channel: CTRL" << (channel + 1) << std::endl;
    std::cout << "========================================" << std::endl;
    
    XyberController* ctrl = XyberController::GetInstance();
    if (!ctrl) {
        std::cerr << "Failed to get XyberController instance" << std::endl;
        return 1;
    }
    
    std::cout << "[1/4] Creating DCU..." << std::endl;
    if (!ctrl->CreateDcu("dcu1", 1)) {
        std::cerr << "Failed to create DCU" << std::endl;
        return 1;
    }
    
    std::cout << "[2/4] Attaching actuator..." << std::endl;
    if (!ctrl->AttachActuator("dcu1", CtrlChannel::CTRL_CH1, 
                              ActuatorType::POWER_FLOW_R86,
                              motor_name, can_id)) {
        std::cerr << "Failed to attach actuator" << std::endl;
        return 1;
    }
    
    std::cout << "[3/4] Starting EtherCAT..." << std::endl;
    if (!ctrl->Start(ifname, 1000000, true)) {
        std::cerr << "Failed to start EtherCAT" << std::endl;
        return 1;
    }
    
    std::this_thread::sleep_for(2s);
    std::cout << std::endl;
    
    std::cout << "========================================" << std::endl;
    std::cout << "  Listening for CANFD Data on CTRL1" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Press Ctrl+C to exit" << std::endl;
    std::cout << std::endl;
    
    uint8_t raw_data[64];
    size_t data_len = 0;
    int count = 0;
    bool has_data = false;
    
    while (g_running) {
        ctrl->GetRawCanfdData(motor_name, CtrlChannel::CTRL_CH1, raw_data, &data_len);
        
        if (data_len > 0) {
            bool all_zero = true;
            for (size_t i = 0; i < 64; ++i) {
                if (raw_data[i] != 0) {
                    all_zero = false;
                    break;
                }
            }
            if (!all_zero) {
                has_data = true;
                std::cout << "[" << count++ << "] RAW CANFD (64 bytes): ";
                print_hex(raw_data, 64);
            }
        }
        
        std::this_thread::sleep_for(100ms);
    }
    
    if (!has_data) {
        std::cout << "No non-zero data received" << std::endl;
    }
    
    std::cout << "Stopping..." << std::endl;
    ctrl->Stop();
    
    return 0;
}