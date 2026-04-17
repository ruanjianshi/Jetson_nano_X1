/*
 * CANFD Receive Test - 实时显示CAN总线接收数据
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

void print_hex(const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)data[i] << " ";
    }
    std::cout << std::dec << std::endl;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    
    std::string ifname = "eth0";
    int channel = 0;  // 0=CTRL1, 1=CTRL2, 2=CTRL3
    
    if (argc > 1) ifname = argv[1];
    if (argc > 2) channel = std::stoi(argv[2]);
    
    std::cout << "CANFD Receive Test" << std::endl;
    std::cout << "Interface: " << ifname << ", Channel: CTRL" << (channel + 1) << std::endl;
    std::cout << "Press Ctrl+C to exit" << std::endl;
    std::cout << std::endl;
    
    XyberController* ctrl = XyberController::GetInstance();
    if (!ctrl) {
        std::cerr << "Failed to get XyberController" << std::endl;
        return 1;
    }
    
    if (!ctrl->CreateDcu("dcu1", 1)) {
        std::cerr << "Failed to create DCU" << std::endl;
        return 1;
    }
    
    if (!ctrl->AttachActuator("dcu1", CtrlChannel::CTRL_CH1, 
                              ActuatorType::POWER_FLOW_R86, "motor1", 1)) {
        std::cerr << "Failed to attach actuator" << std::endl;
        return 1;
    }
    
    if (!ctrl->Start(ifname, 1000000, true)) {
        std::cerr << "Failed to start EtherCAT" << std::endl;
        return 1;
    }
    
    std::cout << "Listening for CANFD data..." << std::endl;
    
    uint8_t raw_data[64];
    uint8_t last_data[64];
    size_t data_len = 0;
    int count = 0;
    memset(last_data, 0, 64);
    
    while (g_running) {
        ctrl->GetRawCanfdData("motor1", CtrlChannel::CTRL_CH1, raw_data, &data_len);
        
        if (data_len > 0) {
            bool all_zero = true;
            for (size_t i = 0; i < 64; ++i) {
                if (raw_data[i] != 0) {
                    all_zero = false;
                    break;
                }
            }
            
            if (!all_zero && memcmp(raw_data, last_data, 64) != 0) {
                memcpy(last_data, raw_data, 64);
                std::cout << "[" << count++ << "] ";
                print_hex(raw_data, 64);
            }
        }
        
        std::this_thread::sleep_for(50ms);
    }
    
    ctrl->Stop();
    return 0;
}