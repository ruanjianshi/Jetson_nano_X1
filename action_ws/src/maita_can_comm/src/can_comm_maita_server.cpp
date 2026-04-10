/*
 * ========================================
 * 脉塔智能 USBCAN-II CAN 通信 C++ Server
 * ========================================
 * 功能说明:
 *   - 基于 libusbcan.so 驱动库实现
 *   - 使用最高速率 (1Mbps)
 *   - 支持双通道 CAN
 *   - ROS Action 接口
 *   - 支持标准帧和扩展帧
 *
 * 注意: 终端输出使用英文以避免乱码，注释使用中文方便阅读
 *
 * 编译:
 *   cd /home/jetson/Desktop/Jetson_Nano/action_ws
 *   catkin_make
 *
 * 运行:
 *   source devel/setup.bash
 *   rosrun maita_can_comm can_comm_maita_server_cpp
 *
 * 作者: Jetson Nano
 * 日期: 2026-04-02
 */

#include <ros/ros.h>
#include <actionlib/server/simple_action_server.h>
#include <maita_can_comm/CANCommAction.h>
#include <dlfcn.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/stat.h>
#include <cstring>
#include <iostream>
#include <sstream>

// 加载官方驱动头文件
#include "controlcan.h"

// 设备类型定义
#define USBCAN_II  4  // USBCAN-II/II+
#define MAX_CHANNELS 2

// 波特率配置（使用最高速率 1Mbps）
#define BAUD_RATE_1M  0x1400  // 1M (75%)

// ========================================
// CAN 接口封装类
// ========================================
#define LOAD_SYMBOL(name) \
    name = (name##_t)dlsym(lib_handle, #name); \
    if (!name) { \
        std::cerr << "ERROR: Failed to load function: " #name << std::endl; \
        return false; \
    }

class MaitaCAN {
public:
    // 函数指针类型定义
    typedef DWORD (*VCI_OpenDevice_t)(DWORD, DWORD, DWORD);
    typedef DWORD (*VCI_CloseDevice_t)(DWORD, DWORD);
    typedef DWORD (*VCI_InitCAN_t)(DWORD, DWORD, DWORD, PVCI_INIT_CONFIG);
    typedef DWORD (*VCI_StartCAN_t)(DWORD, DWORD, DWORD);
    typedef DWORD (*VCI_ResetCAN_t)(DWORD, DWORD, DWORD);
    typedef ULONG (*VCI_Transmit_t)(DWORD, DWORD, DWORD, PVCI_CAN_OBJ, UINT);
    typedef ULONG (*VCI_Receive_t)(DWORD, DWORD, DWORD, PVCI_CAN_OBJ, UINT, INT);
    typedef ULONG (*VCI_GetReceiveNum_t)(DWORD, DWORD, DWORD);
    typedef DWORD (*VCI_ReadBoardInfo_t)(DWORD, DWORD, PVCI_BOARD_INFO);

    MaitaCAN() : lib_handle(nullptr), connected(false) {
        VCI_OpenDevice = nullptr;
        VCI_CloseDevice = nullptr;
        VCI_InitCAN = nullptr;
        VCI_StartCAN = nullptr;
        VCI_ResetCAN = nullptr;
        VCI_Transmit = nullptr;
        VCI_Receive = nullptr;
        VCI_GetReceiveNum = nullptr;
        VCI_ReadBoardInfo = nullptr;
    }

    ~MaitaCAN() {
        close();
    }

    bool loadLibrary(const std::string& lib_path) {
        lib_handle = dlopen(lib_path.c_str(), RTLD_LAZY);
        if (!lib_handle) {
            std::cerr << "ERROR: Failed to load library: " << dlerror() << std::endl;
            return false;
        }

        LOAD_SYMBOL(VCI_OpenDevice);
        LOAD_SYMBOL(VCI_CloseDevice);
        LOAD_SYMBOL(VCI_InitCAN);
        LOAD_SYMBOL(VCI_StartCAN);
        LOAD_SYMBOL(VCI_ResetCAN);
        LOAD_SYMBOL(VCI_Transmit);
        LOAD_SYMBOL(VCI_Receive);
        LOAD_SYMBOL(VCI_GetReceiveNum);
        LOAD_SYMBOL(VCI_ReadBoardInfo);

        std::cout << "OK: Library loaded successfully: " << lib_path << std::endl;
        return true;
    }

    bool openDevice(DWORD device_type = USBCAN_II, DWORD device_index = 0) {
        if (!VCI_OpenDevice) {
            std::cerr << "ERROR: VCI_OpenDevice function not loaded" << std::endl;
            return false;
        }

        DWORD ret = VCI_OpenDevice(device_type, device_index, 0);
        if (ret == 0) {
            std::cerr << "ERROR: Failed to open device" << std::endl;
            connected = false;
            return false;
        }

        this->device_type = device_type;
        this->device_index = device_index;
        connected = true;

        std::cout << "OK: Device opened successfully" << std::endl;
        readBoardInfo();
        return true;
    }

    void readBoardInfo() {
        if (!VCI_ReadBoardInfo || !connected) return;

        VCI_BOARD_INFO info;
        DWORD ret = VCI_ReadBoardInfo(device_type, device_index, &info);
        if (ret == 1) {
            std::cout << "   Device Information:" << std::endl;
            std::cout << "     Serial Number: " << std::string(info.str_Serial_Num, 20) << std::endl;
            std::cout << "     Hardware Type: " << std::string(info.str_hw_Type, 40) << std::endl;
            std::cout << "     Hardware Version: " << info.hw_Version << std::endl;
            std::cout << "     Firmware Version: " << info.fw_Version << std::endl;
        }
    }

    bool initCAN(DWORD channel, DWORD baudrate = BAUD_RATE_1M) {
        if (!connected || !VCI_InitCAN || !VCI_StartCAN) {
            return false;
        }

        VCI_INIT_CONFIG config;
        config.AccCode = 0;
        config.AccMask = 0xFFFFFFFF;
        config.Reserved = 0;
        config.Filter = 1;
        config.Timing0 = baudrate & 0xFF;
        config.Timing1 = baudrate >> 8;
        config.Mode = 0;

        DWORD ret = VCI_InitCAN(device_type, device_index, channel, &config);
        if (ret == 0) {
            std::cerr << "ERROR: Failed to initialize CAN " << channel << std::endl;
            return false;
        }

        std::cout << "OK: Initialized CAN " << channel << std::endl;

        ret = VCI_StartCAN(device_type, device_index, channel);
        if (ret == 0) {
            std::cerr << "ERROR: Failed to start CAN " << channel << std::endl;
            return false;
        }

        std::cout << "OK: Started CAN " << channel << std::endl;
        return true;
    }

    bool transmit(DWORD channel, UINT can_id, const uint8_t* data, UINT dlc, bool extended = false) {
        if (!connected || !VCI_Transmit) {
            return false;
        }

        VCI_CAN_OBJ can_obj;
        std::memset(&can_obj, 0, sizeof(can_obj));

        can_obj.ID = can_id;
        can_obj.SendType = 0;
        can_obj.RemoteFlag = 0;
        can_obj.ExternFlag = extended ? 1 : 0;
        can_obj.DataLen = dlc;

        for (UINT i = 0; i < dlc && i < 8; i++) {
            can_obj.Data[i] = data[i];
        }

        ULONG ret = VCI_Transmit(device_type, device_index, channel, &can_obj, 1);
        return ret == 1;
    }

    bool receive(DWORD channel, VCI_CAN_OBJ* can_obj, UINT wait_ms = 100) {
        if (!connected || !VCI_Receive) {
            return false;
        }

        ULONG count = VCI_GetReceiveNum(device_type, device_index, channel);
        if (count == 0) {
            return false;
        }

        ULONG ret = VCI_Receive(device_type, device_index, channel, can_obj, 1, wait_ms);
        return ret > 0;
    }

    void close() {
        if (!connected || !VCI_CloseDevice) {
            return;
        }

        for (int i = 0; i < MAX_CHANNELS; i++) {
            if (VCI_ResetCAN) {
                VCI_ResetCAN(device_type, device_index, i);
            }
        }

        DWORD ret = VCI_CloseDevice(device_type, device_index);
        if (ret == 1) {
            std::cout << "OK: Device closed" << std::endl;
        }

        if (lib_handle) {
            dlclose(lib_handle);
            lib_handle = nullptr;
        }

        connected = false;
    }

    bool isConnected() const { return connected; }

private:
    void* lib_handle;
    bool connected;
    DWORD device_type;
    DWORD device_index;

    // 函数指针
    VCI_OpenDevice_t VCI_OpenDevice;
    VCI_CloseDevice_t VCI_CloseDevice;
    VCI_InitCAN_t VCI_InitCAN;
    VCI_StartCAN_t VCI_StartCAN;
    VCI_ResetCAN_t VCI_ResetCAN;
    VCI_Transmit_t VCI_Transmit;
    VCI_Receive_t VCI_Receive;
    VCI_GetReceiveNum_t VCI_GetReceiveNum;
    VCI_ReadBoardInfo_t VCI_ReadBoardInfo;
};

// ========================================
// 接收线程类
// ========================================
class CANReceiverThread {
public:
    CANReceiverThread(MaitaCAN* can) : can(can), running(false) {}

    void start() {
        running = true;
        pthread_create(&thread, nullptr, receiverThreadFunc, this);
    }

    void stop() {
        running = false;
        pthread_join(thread, nullptr);
    }

private:
    MaitaCAN* can;
    pthread_t thread;
    bool running;

    static void* receiverThreadFunc(void* arg) {
        CANReceiverThread* obj = static_cast<CANReceiverThread*>(arg);
        obj->run();
        return nullptr;
    }

    void run() {
        while (running) {
            for (int ch = 0; ch < MAX_CHANNELS; ch++) {
                VCI_CAN_OBJ can_obj;
                if (can->receive(ch, &can_obj)) {
                    std::cout << "RX CAN" << ch << " Received: ";
                    std::cout << "ID=0x" << std::hex << can_obj.ID << std::dec;
                    std::cout << " " << (can_obj.ExternFlag ? "Ext Frame" : "Std Frame");

                    if (can_obj.RemoteFlag == 0) {
                        std::cout << " Data: ";
                        for (int i = 0; i < can_obj.DataLen; i++) {
                            std::cout << std::hex << std::setw(2) << std::setfill('0') 
                                      << (int)can_obj.Data[i] << " " << std::dec;
                        }
                    } else {
                        std::cout << " Remote Frame";
                    }
                    std::cout << std::endl;
                }
            }
            usleep(10000);  // 10ms
        }
    }
};

// ========================================
// ROS Action Server 类
// ========================================
class CANCommActionServer {
protected:
    ros::NodeHandle nh_;
    actionlib::SimpleActionServer<maita_can_comm::CANCommAction> as_;
    std::string action_name_;
    MaitaCAN* can_;
    CANReceiverThread* receiver_;

public:
    CANCommActionServer(std::string name, MaitaCAN* can, CANReceiverThread* receiver)
        : as_(nh_, name, boost::bind(&CANCommActionServer::executeCB, this, _1), false),
          action_name_(name),
          can_(can),
          receiver_(receiver) {
        as_.start();
        ROS_INFO("OK: CAN Communication Action Server started");
        ROS_INFO("   Action name: %s", action_name_.c_str());
    }

    ~CANCommActionServer() {}

    void executeCB(const maita_can_comm::CANCommGoalConstPtr &goal) {
        if (!can_->isConnected()) {
            ROS_ERROR("ERROR: Device not connected, cannot execute task");
            maita_can_comm::CANCommResult result;
            result.success = false;
            result.message = "Device not connected";
            as_.setAborted(result);
            return;
        }

        if (goal->channel >= MAX_CHANNELS) {
            ROS_ERROR("ERROR: Invalid channel number: %u", goal->channel);
            maita_can_comm::CANCommResult result;
            result.success = false;
            result.message = "Invalid channel number";
            as_.setAborted(result);
            return;
        }

        if (goal->dlc < 0 || goal->dlc > 8) {
            ROS_ERROR("ERROR: Invalid data length: %u", goal->dlc);
            maita_can_comm::CANCommResult result;
            result.success = false;
            result.message = "Data length must be between 0 and 8";
            as_.setAborted(result);
            return;
        }

        ROS_INFO("Received Goal:");
        ROS_INFO("   CAN ID: 0x%03X", goal->can_id);
        ROS_INFO("   Data length: %u", goal->dlc);
        ROS_INFO("   Extended frame: %s", goal->extended ? "Yes" : "No");
        ROS_INFO("   Channel: %u", goal->channel);

        maita_can_comm::CANCommFeedback feedback;
        feedback.status = "Sending CAN frame...";
        as_.publishFeedback(feedback);

        std::vector<uint8_t> data(goal->data.begin(), goal->data.end());

        bool success = can_->transmit(
            goal->channel,
            goal->can_id,
            data.data(),
            goal->dlc,
            goal->extended
        );

        if (success) {
            ROS_INFO("TX: CAN frame sent: ID=0x%03X, DLC=%u", goal->can_id, goal->dlc);

            maita_can_comm::CANCommResult result;
            result.success = true;
            result.message = "CAN frame sent successfully";
            as_.setSucceeded(result);
            ROS_INFO("OK: Goal execution succeeded");
        } else {
            ROS_ERROR("ERROR: Failed to send CAN frame");

            maita_can_comm::CANCommResult result;
            result.success = false;
            result.message = "Failed to send CAN frame";
            as_.setAborted(result);
        }
    }
};

// ========================================
// 主函数
// ========================================
int main(int argc, char** argv) {
    ros::init(argc, argv, "can_comm_maita_server_cpp");

    std::cout << "========================================" << std::endl;
    std::cout << "Maita USBCAN-II CAN Communication C++ Server" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Maximum speed: 1 Mbps" << std::endl;
    std::cout << std::endl;

    int device_type = USBCAN_II;
    int baudrate = BAUD_RATE_1M;
    bool enable_receiver = true;

    ros::NodeHandle nh("~");
    nh.param("device_type", device_type, (int)USBCAN_II);
    nh.param("baudrate", baudrate, (int)BAUD_RATE_1M);
    nh.param("enable_receiver", enable_receiver, true);

    MaitaCAN can;

    std::string lib_path = "/lib/libusbcan.so";
    
    struct stat buffer;
    if (stat(lib_path.c_str(), &buffer) != 0) {
        char* catkin_ws = getenv("CATKIN_WORKSPACE");
        if (catkin_ws) {
            lib_path = std::string(catkin_ws) + "/src/maita_can_comm/usbcan_ii_libusb_aarch64/libusbcan.so";
        } else {
            lib_path = "./usbcan_ii_libusb_aarch64/libusbcan.so";
        }
    }
    
    if (!can.loadLibrary(lib_path)) {
        ROS_ERROR("ERROR: Failed to load driver library: %s", lib_path.c_str());
        ROS_ERROR("Please run: sudo cp src/maita_can_comm/usbcan_ii_libusb_aarch64/libusbcan.so /lib/");
        return -1;
    }

    if (!can.openDevice(device_type, 0)) {
        ROS_ERROR("ERROR: Failed to open device");
        return -1;
    }

    for (int i = 0; i < MAX_CHANNELS; i++) {
        if (!can.initCAN(i, baudrate)) {
            ROS_ERROR("ERROR: Failed to initialize CAN %d", i);
            return -1;
        }
    }

    CANReceiverThread receiver(&can);
    if (enable_receiver) {
        receiver.start();
        ROS_INFO("OK: Receiver thread started");
    }

    CANCommActionServer server("can_comm", &can, enable_receiver ? &receiver : nullptr);

    ROS_INFO("Action Server running, waiting for Goal requests...");
    ROS_INFO("   Baudrate: 1 Mbps");
    ROS_INFO("   Receiver thread: %s", enable_receiver ? "Enabled" : "Disabled");

    ros::spin();

    if (enable_receiver) {
        receiver.stop();
    }

    can.close();

    ROS_INFO("Program exited");
    return 0;
}