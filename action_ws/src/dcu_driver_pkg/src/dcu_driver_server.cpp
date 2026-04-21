/*
 * DCU Driver Server Node - 直流电机驱动服务节点
 * 
 * 功能: 通过 EtherCAT 总线控制智元科技 PowerFlow R 系列执行器
 * 
 * =============================================================================
 * 硬件架构:
 *   Jetson Nano (EtherCAT) → DCU (域控制器) → CANFD → PowerFlow R 执行器
 * =============================================================================
 * 
 * 控制协议 (参考智元官方文档):
 *   - 使能/禁能: CAN ID = motor_id, DLC=2, 数据 [0x01, 状态]
 *   - MIT模式: 广播帧 CAN ID=0, 64字节, 每个电机根据ID取8字节
 * 
 * 使用方法:
 *   # 1. 使能电机 (cmd=1)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 3}"
 *   
 *   # 2. 设置控制模式 (cmd=3, mode=6=MIT)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 3, mode: 6}"
 *   
 *   # 3. MIT控制 (cmd=1 带控制参数时执行MIT控制)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 3, q: 0.0, kp: 10.0, kd: 1.0}"
 *   
 *   # 4. 禁能电机 (cmd=2)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 2, motor_id: 3}"
 * 
 * =============================================================================
 * SDK 提供的API (xyber_controller.h):
 *   - EnableActuator(name) / DisableActuator(name)  // 使能/禁能单个执行器
 *   - SetMode(name, mode)                         // 设置控制模式
 *   - SetMitCmd(name, pos, vel, effort, kp, kd)   // MIT模式控制 (唯一控制指令)
 *   - GetPosition/Velocity/Effort(name)           // 读取位置/速度/力矩
 * 
 * 注意: SDK没有独立的力矩/速度/位置控制API，这些都通过SetMitCmd参数组合实现
 * =============================================================================
 */

#include <ros/ros.h>
#include <std_msgs/Float64MultiArray.h>
#include <sensor_msgs/JointState.h>
#include <actionlib/server/simple_action_server.h>
#include <dcu_driver_pkg/DCUControlAction.h>
#include <dcu_driver_pkg/MotorCommand.h>
#include <xyber_controller.h>
#include <common_type.h>
#include <vector>
#include <thread>
#include <mutex>
#include <algorithm>
#include <unordered_map>

// =============================================================================
// 电机配置结构体
// =============================================================================
// 用于存储从 ROS 参数服务器加载的电机配置信息
// 每个电机在参数文件中定义如下:
//   motors:
//     - name: "joint1"
//       ethercat_id: 1        # EtherCAT从站ID (DCU的ID)
//       can_node_id: 1        # CAN总线上的节点ID (电机的ID, 1-8)
//       can_channel: "CTRL1"  # CANFD通道 (CTRL1/CTRL2/CTRL3)
//       actuator_type: "POWER_FLOW_R86"  # 电机类型
// =============================================================================
struct MotorConfig {
    std::string name;              // 电机名称,用于SDK调用 (如 "joint1")
    uint8_t ethercat_id;          // EtherCAT从站ID (通常是1)
    uint8_t can_node_id;          // CAN节点ID (电机ID, 范围1-8)
    xyber::CtrlChannel can_channel;  // CANFD通道 (CTRL_CH1/2/3)
    xyber::ActuatorType actuator_type;  // 电机类型 (POWER_FLOW_R86/R52/L28)
};

// =============================================================================
// DCU驱动服务类
// =============================================================================
// 核心类,管理EtherCAT通信和电机控制
// 主要功能:
//   1. 加载电机配置并创建DCU和执行器
//   2. 启动EtherCAT通信
//   3. 订阅 /motor/command 话题,解析控制指令
//   4. 发布 /joint_states 话题,发布电机状态
//   5. 启动状态监控线程,实时显示电机状态
// =============================================================================
class DCUDriverServer
{
public:
    // =========================================================================
    // 构造函数
    // =========================================================================
    // 初始化ROS节点,创建订阅者/发布者,加载配置,启动Action服务
    DCUDriverServer()
        : action_server_(nh_, "dcu_control",  // Action服务名称
            boost::bind(&DCUDriverServer::executeCB, this, _1), false)
        , xyber_ctrl_(nullptr)              // XyberController单例指针
        , is_running_(false)                // 运行状态标志
    {
        // 订阅电机控制指令话题
        // 消息类型: MotorCommand (cmd/motor_id/mode/q/dq/kp/kd)
        motor_cmd_sub_ = nh_.subscribe("/motor/command", 100, &DCUDriverServer::motorCmdCB, this);
        
        // 发布电机状态话题
        // 消息类型: sensor_msgs/JointState (name/position/velocity/effort)
        joint_states_pub_ = nh_.advertise<sensor_msgs::JointState>("/joint_states", 100);
        
        // 从参数服务器加载电机配置
        loadMotorConfig();
        
        // 构建 motor_id → name 的映射表,用于根据ID查找电机
        buildMotorIdMap();
        
        // 启动ROS Action服务 (用于多电机控制)
        action_server_.start();
        
        ROS_INFO("DCU Driver Server started (Zhiyuan Protocol)");
    }

    // =========================================================================
    // 析构函数
    // =========================================================================
    ~DCUDriverServer()
    {
        stop();
    }

    // =========================================================================
    // 加载电机配置
    // =========================================================================
    // 从ROS参数服务器读取motors参数,解析并存储到motors_向量中
    // 参数格式:
    //   motors:
    //     - name: "joint1"
    //       ethercat_id: 1
    //       can_node_id: 1
    //       can_channel: "CTRL1"
    //       actuator_type: "POWER_FLOW_R86"
    // =========================================================================
    void loadMotorConfig()
    {
        XmlRpc::XmlRpcValue motor_list;
        
        // 尝试获取motors参数
        if (!nh_.getParam("motors", motor_list)) {
            // 参数不存在时使用默认配置
            ROS_WARN("No motors configured, using default (joint3, CAN ID=3)");
            motors_.push_back({"joint3", 1, 3, xyber::CtrlChannel::CTRL_CH1, 
                              xyber::ActuatorType::POWER_FLOW_R86});
            motor_names_.push_back("joint3");
            return;
        }

        // 解析每个电机的配置
        for (int i = 0; i < motor_list.size(); ++i) {
            XmlRpc::XmlRpcValue& m = motor_list[i];
            MotorConfig motor;
            
            // 解析基本参数
            motor.name = static_cast<std::string>(m["name"]);
            motor.ethercat_id = static_cast<int>(m["ethercat_id"]);
            motor.can_node_id = static_cast<int>(m["can_node_id"]);
            
            // 解析CAN通道
            std::string channel = static_cast<std::string>(m["can_channel"]);
            if (channel == "CTRL1") motor.can_channel = xyber::CtrlChannel::CTRL_CH1;
            else if (channel == "CTRL2") motor.can_channel = xyber::CtrlChannel::CTRL_CH2;
            else motor.can_channel = xyber::CtrlChannel::CTRL_CH3;

            // 解析电机类型
            std::string type = static_cast<std::string>(m["actuator_type"]);
            motor.actuator_type = xyber::StringToType(type);
            
            // 存储配置
            motors_.push_back(motor);
            motor_names_.push_back(motor.name);
        }
    }

    // =========================================================================
    // 构建电机ID映射表
    // =========================================================================
    // 将 can_node_id (电机ID) 映射到 name (电机名称)
    // 用于根据用户发送的motor_id找到对应的SDK调用名称
    // 例如: motor_id_map_[3] = "joint3"
    // =========================================================================
    void buildMotorIdMap()
    {
        motor_id_map_.clear();
        for (const auto& m : motors_) {
            motor_id_map_[m.can_node_id] = m.name;
        }
        ROS_INFO("Motor ID map: %zu motors", motor_id_map_.size());
        for (const auto& [id, name] : motor_id_map_) {
            ROS_INFO("  ID %d -> %s", id, name.c_str());
        }
    }

    // =========================================================================
    // 根据电机ID获取电机名称
    // =========================================================================
    // 参数: motor_id - CAN节点ID (用户发送的ID)
    // 返回: 对应的电机名称 (用于SDK调用)
    //       如果找不到返回空字符串
    // =========================================================================
    std::string getMotorNameById(uint8_t motor_id)
    {
        auto it = motor_id_map_.find(motor_id);
        if (it != motor_id_map_.end()) {
            return it->second;
        }
        return "";
    }

    // =========================================================================
    // 初始化XyberController单例
    // =========================================================================
    bool init()
    {
        xyber_ctrl_ = xyber::XyberController::GetInstance();
        return (xyber_ctrl_ != nullptr);
    }

    // =========================================================================
    // 启动EtherCAT通信
    // =========================================================================
    // 执行步骤:
    //   1. 创建DCU实例
    //   2. 挂载执行器到DCU
    //   3. 设置实时优先级
    //   4. 启动EtherCAT通信
    //   5. 启动状态监控线程
    // =========================================================================
    bool start(const std::string& ifname, bool enable_dc, uint64_t cycle_ns)
    {
        if (xyber_ctrl_ == nullptr) {
            ROS_ERROR("Controller not initialized");
            return false;
        }

        // 创建DCU实例 (按ethercat_id分组)
        std::map<uint8_t, std::string> dcu_map;
        for (const auto& m : motors_) {
            dcu_map[m.ethercat_id] = "dcu" + std::to_string(m.ethercat_id);
        }

        // 创建每个DCU
        for (const auto& [ecat_id, dcu_name] : dcu_map) {
            if (!xyber_ctrl_->CreateDcu(dcu_name, ecat_id)) {
                ROS_ERROR("Failed to create DCU: %s", dcu_name.c_str());
                return false;
            }
        }

        // 挂载执行器到DCU
        for (const auto& m : motors_) {
            std::string dcu_name = "dcu" + std::to_string(m.ethercat_id);
            if (!xyber_ctrl_->AttachActuator(dcu_name, m.can_channel, 
                                            m.actuator_type, m.name, m.can_node_id)) {
                ROS_ERROR("Failed to attach actuator: %s", m.name.c_str());
                return false;
            }
        }

        // 设置实时优先级 (RT thread priority 90, bind to CPU 1)
        xyber_ctrl_->SetRealtime(90, 1);

        // 启动EtherCAT通信
        if (!xyber_ctrl_->Start(ifname, cycle_ns, enable_dc)) {
            ROS_ERROR("Failed to start EtherCAT");
            return false;
        }

        // 等待EtherCAT稳定
        ros::Duration(2.0).sleep();

        ROS_INFO("DCU Driver started. Use /motor/command to control motors.");
        is_running_ = true;
        
        // 启动状态监控线程
        startStateMonitor();
        
        return true;
    }

    // =========================================================================
    // 停止EtherCAT通信
    // =========================================================================
    void stop()
    {
        is_running_ = false;
        
        // 等待状态监控线程退出
        if (state_monitor_thread_.joinable()) {
            state_monitor_thread_.join();
        }
        
        if (xyber_ctrl_ != nullptr) xyber_ctrl_->Stop();
    }

    // =========================================================================
    // 将消息中的mode转换为SDK的ActautorMode枚举
    // =========================================================================
    // 参数:
    //   mode - 用户发送的控制模式 (0-6)
    //     0: MODE_CURRENT       - 电流环模式
    //     1: MODE_CURRENT_RAMP  - 电流环梯形加减速
    //     2: MODE_VELOCITY      - 速度环模式
    //     3: MODE_VELOCITY_RAMP - 速度环梯形加减速
    //     4: MODE_POSITION       - 位置环模式
    //     5: MODE_POSITION_RAMP  - 位置环梯形加减速
    //     6: MODE_MIT           - MIT混合控制模式 (默认)
    // =========================================================================
    xyber::ActautorMode modeToXyberMode(uint8_t mode)
    {
        switch (mode) {
            case 0: return xyber::ActautorMode::MODE_CURRENT;
            case 1: return xyber::ActautorMode::MODE_CURRENT_RAMP;
            case 2: return xyber::ActautorMode::MODE_VELOCITY;
            case 3: return xyber::ActautorMode::MODE_VELOCITY_RAMP;
            case 4: return xyber::ActautorMode::MODE_POSITION;
            case 5: return xyber::ActautorMode::MODE_POSITION_RAMP;
            case 6: return xyber::ActautorMode::MODE_MIT;
            default: return xyber::ActautorMode::MODE_MIT;
        }
    }

    // =========================================================================
    // 电机控制指令回调函数
    // =========================================================================
    // 订阅 /motor/command 话题,处理四种指令:
    //   cmd=1: 使能电机
    //   cmd=2: 禁能电机
    //   cmd=3: 设置控制模式
    //   cmd=4: MIT控制 (pos+vel+torque+kp+kd)
    // =========================================================================
    void motorCmdCB(const dcu_driver_pkg::MotorCommand::ConstPtr& msg)
    {
        // 根据motor_id查找电机名称
        std::string name = getMotorNameById(msg->motor_id);
        if (name.empty()) {
            ROS_WARN("Unknown motor_id: %d", msg->motor_id);
            return;
        }

        switch (msg->cmd) {
            // =================================================================
            // cmd=1: 使能电机 (仅使能,不包含控制)
            // =================================================================
            case 1: {
                if (!xyber_ctrl_->EnableActuator(name)) {
                    ROS_ERROR("Failed to enable motor_id: %d", msg->motor_id);
                    return;
                }
                ROS_INFO("Motor ID %d enabled", msg->motor_id);
                break;
            }

            // =================================================================
            // cmd=2: 禁能电机
            // =================================================================
            case 2: {
                if (!xyber_ctrl_->DisableActuator(name)) {
                    ROS_ERROR("Failed to disable motor_id: %d", msg->motor_id);
                    return;
                }
                ROS_INFO("Motor ID %d disabled", msg->motor_id);
                break;
            }

            // =================================================================
            // cmd=3: 设置控制模式
            // =================================================================
            case 3: {
                xyber::ActautorMode xyber_mode = modeToXyberMode(msg->mode);
                if (!xyber_ctrl_->SetMode(name, xyber_mode)) {
                    ROS_ERROR("Failed to set mode %d for motor_id: %d", msg->mode, msg->motor_id);
                    return;
                }
                ROS_INFO("Motor ID %d mode set to %d", msg->motor_id, msg->mode);
                break;
            }

            // =================================================================
            // cmd=4: MIT控制 (位置+速度+力矩+刚度+阻尼)
            // =================================================================
            case 4: {
                // SetMitCmd参数: pos, vel, effort, kp, kd
                xyber_ctrl_->SetMitCmd(name, msg->q, msg->dq, msg->tau, msg->kp, msg->kd);
                ROS_INFO("MIT cmd: ID=%d q=%.3f dq=%.3f tau=%.3f kp=%.1f kd=%.1f",
                         msg->motor_id, msg->q, msg->dq, msg->tau, msg->kp, msg->kd);
                break;
            }

            default:
                ROS_WARN("Unknown cmd: %d for motor ID %d", msg->cmd, msg->motor_id);
                break;
        }
    }

    // =========================================================================
    // ROS Action回调函数 (executeCB)
    // =========================================================================
    // 用于多电机同时控制,通过Action接口
    // Action名称: dcu_control
    // Goal: joint_names + positions + stiffness + damping
    // Result: success + message
    // Feedback: current_positions/velocities/efforts
    // =========================================================================
    void executeCB(const dcu_driver_pkg::DCUControlGoalConstPtr& goal)
    {
        dcu_driver_pkg::DCUControlResult result;
        dcu_driver_pkg::DCUControlFeedback feedback;

        ROS_INFO("Action goal received: %zu joints", goal->joint_names.size());

        // 检查参数数量匹配
        if (goal->joint_names.size() != goal->positions.size()) {
            result.success = false;
            result.message = "Size mismatch";
            action_server_.setAborted(result);
            return;
        }

        // 对每个电机发送MIT控制命令
        for (size_t i = 0; i < goal->joint_names.size(); ++i) {
            const std::string& name = goal->joint_names[i];
            float pos = static_cast<float>(goal->positions[i]);
            float kp = (i < goal->stiffness.size()) ? static_cast<float>(goal->stiffness[i]) : 10.0f;
            float kd = (i < goal->damping.size()) ? static_cast<float>(goal->damping[i]) : 1.0f;

            // 检查电机是否存在
            if (std::find(motor_names_.begin(), motor_names_.end(), name) == motor_names_.end()) {
                ROS_WARN("Action: unknown motor %s", name.c_str());
                continue;
            }

            // 发送MIT控制命令 (pos, vel=0, effort=0, kp, kd)
            xyber_ctrl_->SetMitCmd(name, pos, 0.0f, 0.0f, kp, kd);
            ROS_INFO("Action: %s pos=%.3f kp=%.1f kd=%.1f", name.c_str(), pos, kp, kd);
            
            // 读取当前状态
            feedback.current_positions.push_back(xyber_ctrl_->GetPosition(name));
            feedback.current_velocities.push_back(xyber_ctrl_->GetVelocity(name));
            feedback.current_efforts.push_back(xyber_ctrl_->GetEffort(name));
        }

        // 返回结果
        action_server_.publishFeedback(feedback);
        result.success = true;
        result.message = "Command executed";
        action_server_.setSucceeded(result);
    }

    // =========================================================================
    // 发布电机状态
    // =========================================================================
    // 定时发布 /joint_states 话题
    // 频率: 100Hz (由spin函数控制)
    // 内容: 所有电机的 position/velocity/effort
    // =========================================================================
    void publishStates()
    {
        if (!is_running_) return;
        
        sensor_msgs::JointState joint_state;
        joint_state.header.stamp = ros::Time::now();

        // 遍历所有电机,读取状态
        for (const auto& name : motor_names_) {
            joint_state.name.push_back(name);
            joint_state.position.push_back(xyber_ctrl_->GetPosition(name));
            joint_state.velocity.push_back(xyber_ctrl_->GetVelocity(name));
            joint_state.effort.push_back(xyber_ctrl_->GetEffort(name));
        }
        joint_states_pub_.publish(joint_state);
    }

    // =========================================================================
    // 电机状态监控线程
    // =========================================================================
    // 独立线程,定期读取并显示所有电机的实时状态
    // 用于调试和监控,每秒输出一次状态信息
    // =========================================================================
    void startStateMonitor()
    {
        state_monitor_thread_ = std::thread([this]() {
            ROS_INFO("State monitor thread started");
            while (is_running_ && ros::ok()) {
                for (const auto& name : motor_names_) {
                    float pos = xyber_ctrl_->GetPosition(name);
                    float vel = xyber_ctrl_->GetVelocity(name);
                    float effort = xyber_ctrl_->GetEffort(name);
                    xyber::ActautorState state = xyber_ctrl_->GetPowerState(name);
                    xyber::ActautorMode mode = xyber_ctrl_->GetMode(name);
                    std::string error = xyber_ctrl_->GetErrorString(name);
                    ROS_INFO_THROTTLE(1.0, "[%s] pos=%.3f rad, vel=%.3f rad/s, effort=%.3f Nm, state=%d, mode=%d, error=%s",
                                      name.c_str(), pos, vel, effort, (int)state, (int)mode, error.c_str());
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        });
    }

    // =========================================================================
    // 主循环
    // =========================================================================
    // 处理ROS回调和发布状态
    // 频率: 100Hz
    // =========================================================================
    void spin()
    {
        ros::Rate rate(100);
        while (ros::ok()) {
            ros::spinOnce();  // 处理ROS回调
            if (is_running_) {
                publishStates();  // 发布状态
            }
            rate.sleep();
        }
    }

private:
    ros::NodeHandle nh_;                                          // ROS节点句柄
    actionlib::SimpleActionServer<dcu_driver_pkg::DCUControlAction> action_server_;  // Action服务
    ros::Subscriber motor_cmd_sub_;                                // 控制指令订阅者
    ros::Publisher joint_states_pub_;                             // 状态发布者
    
    xyber::XyberController* xyber_ctrl_;                          // XyberController单例指针
    std::vector<MotorConfig> motors_;                            // 电机配置列表
    std::vector<std::string> motor_names_;                        // 电机名称列表 (按顺序)
    std::unordered_map<uint8_t, std::string> motor_id_map_;       // motor_id → name 映射表
    std::thread state_monitor_thread_;                            // 状态监控线程
    bool is_running_;                                             // 运行状态标志
};

// =============================================================================
// 主函数
// =============================================================================
int main(int argc, char** argv)
{
    // 初始化ROS节点
    ros::init(argc, argv, "dcu_driver_server");
    ros::NodeHandle nh;

    // 从参数服务器读取配置 (带默认值)
    std::string ifname = "eth0";       // 网卡名称
    bool enable_dc = true;             // 启用分布式时钟
    int cycle_ns = 1000000;           // 循环周期 (1ms = 1000Hz)

    nh.getParam("ethercat_if", ifname);
    nh.getParam("enable_dc", enable_dc);
    nh.getParam("cycle_ns", cycle_ns);

    // 创建服务对象
    DCUDriverServer server;

    // 初始化XyberController
    if (!server.init()) {
        ROS_ERROR("Failed to initialize");
        return 1;
    }

    // 启动EtherCAT通信
    if (!server.start(ifname, enable_dc, cycle_ns)) {
        ROS_ERROR("Failed to start EtherCAT");
        return 1;
    }

    // 进入主循环
    server.spin();
    return 0;
}
