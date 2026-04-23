/*
 * DCU Driver Server Node - 智元X1机器人直流电机驱动服务节点
 * 
 * 功能: 通过 EtherCAT 总线控制智元科技 PowerFlow R/R52 系列执行器
 * 
 * =============================================================================
 * 硬件架构:
 *   Jetson Nano (EtherCAT) → DCU (域控制器) → CANFD → PowerFlow 执行器
 * 
 * 硬件配置:
 *   - DCU CTRL1 通道: 串联 R86-2 #1 (CAN ID=3) + R86-2 #2 (CAN ID=2)
 *   - DCU CTRL2 通道: 串联 R52 #1 (CAN ID=3) + R52 #2 (CAN ID=5)
 * 
 * 电机参数:
 *   - R86-2: 减速比16, 额定转矩20Nm, 峰值80Nm, 电流限幅20A
 *   - R52:   减速比36, 额定转矩6Nm, 峰值19Nm, 电流限幅8A
 * =============================================================================
 * 
 * 控制命令格式 (发布到 /motor/command 话题):
 * 
 *   # 1. 使能电机 (cmd=1, channel=1/2/3, motor_id=1-8, motor_type=可选)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 1, motor_id: 3, channel: 1, motor_type: 'POWER_FLOW_R86'}"
 *   
 *   # 2. 设置控制模式 (cmd=3, mode=6=MIT)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 3, motor_id: 3, channel: 1, mode: 6}"
 *   
 *   # 3. MIT控制 (cmd=4, 位置+速度+力矩+刚度+阻尼)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 4, motor_id: 3, channel: 1, q: 0.0, dq: 0.0, tau: 0.0, kp: 10.0, kd: 1.0}"
 *   
 *   # 4. 禁能电机 (cmd=2)
 *   rostopic pub /motor/command dcu_driver_pkg/MotorCommand "{cmd: 2, motor_id: 3, channel: 1}"
 * 
 * =============================================================================
 * 消息字段说明:
 *   cmd         - 命令: 1=使能, 2=禁能, 3=设置模式, 4=MIT控制
 *   motor_id    - 电机 CAN ID (1-8)
 *   channel     - CAN通道: 1=CTRL1, 2=CTRL2, 3=CTRL3
 *   motor_type  - 电机型号: POWER_FLOW_R86/R52/R28 (可选,用于校验)
 *   mode        - 控制模式 (仅cmd=3时): 0-6
 *   q           - 目标位置 (rad), MIT控制时必填
 *   dq          - 目标速度 (rad/s)
 *   tau         - 目标力矩 (Nm), MIT控制时必填
 *   kp          - 刚度 (0-500), MIT控制时必填
 *   kd          - 阻尼 (0-8), MIT控制时必填
 * 
 * =============================================================================
 * SDK API (xyber_controller.h):
 *   - EnableActuator(name) / DisableActuator(name)  // 使能/禁能执行器
 *   - SetMode(name, mode)                         // 设置控制模式
 *   - SetMitCmd(name, pos, vel, effort, kp, kd)   // MIT模式控制 (唯一控制指令)
 *   - GetPosition/Velocity/Effort(name)           // 读取位置/速度/力矩
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
// 
// ROS 参数格式 (launch 文件或 yaml):
//   motors:
//     - name: "joint1"
//       ethercat_id: 1           # EtherCAT 从站ID (DCU的ID)
//       can_node_id: 3           # CAN 节点ID (电机ID, 范围1-8)
//       can_channel: "CTRL1"     # CANFD 通道 (CTRL1/CTRL2/CTRL3)
//       actuator_type: "POWER_FLOW_R86"  # 电机类型
//       torque_limit: 100.0      # 力矩限幅 (Nm)
//       velocity_limit: 37.7     # 速度限幅 (rad/s)
// =============================================================================
struct MotorConfig {
    std::string name;                  // 电机名称,用于SDK调用 (如 "joint1")
    uint8_t ethercat_id;              // EtherCAT 从站ID (通常是1)
    uint8_t can_node_id;              // CAN 节点ID (电机ID, 范围1-8)
    xyber::CtrlChannel can_channel;   // CANFD 通道 (CTRL_CH1/2/3)
    xyber::ActuatorType actuator_type; // 电机类型 (POWER_FLOW_R86/R52/L28)
};

// =============================================================================
// DCU驱动服务类
// =============================================================================
// 核心类,管理EtherCAT通信和电机控制
// 
// 主要功能:
//   1. 加载电机配置并创建DCU和执行器
//   2. 启动EtherCAT通信
//   3. 订阅 /motor/command 话题,解析控制指令 (cmd/channel/motor_id/motor_type)
//   4. 发布 /joint_states 话题,发布电机状态 (多圈累加位置)
//   5. 启动状态监控线程,每秒输出所有电机状态
//   6. 提供 ROS Action 接口 (dcu_control) 用于多电机同时控制
// =============================================================================
class DCUDriverServer
{
public:
    // =========================================================================
    // 构造函数
    // =========================================================================
    // 初始化ROS节点,创建订阅者/发布者,加载配置,启动Action服务
    DCUDriverServer()
        : action_server_(nh_, "dcu_control",       // Action服务名称
            boost::bind(&DCUDriverServer::executeCB, this, _1), false)
        , xyber_ctrl_(nullptr)                    // XyberController单例指针
        , is_running_(false)                       // 运行状态标志
    {
        // 订阅电机控制指令话题
        // 消息类型: MotorCommand (cmd/channel/motor_id/motor_type/q/dq/tau/kp/kd)
        motor_cmd_sub_ = nh_.subscribe("/motor/command", 100, &DCUDriverServer::motorCmdCB, this);
        
        // 发布电机状态话题
        // 消息类型: sensor_msgs/JointState (name/position/velocity/effort)
        joint_states_pub_ = nh_.advertise<sensor_msgs::JointState>("/joint_states", 100);
        
        // 从参数服务器加载电机配置
        loadMotorConfig();
        
        // 构建电机映射表 (channel+motor_id → name, motor_id → name, name → type)
        buildMotorIdMap();
        
        // 启动ROS Action服务 (用于多电机控制)
        action_server_.start();
        
        // 初始化圈数计数器和上一位置 (用于多圈位置累加)
        for (const auto& name : motor_names_) {
            revolution_counts_[name] = 0;
            last_positions_[name] = 0.0f;
        }
        
        ROS_INFO("DCU Driver Server started (Zhiyuan Protocol)");
    }

    ~DCUDriverServer()
    {
        stop();
    }

    // =========================================================================
    // 加载电机配置
    // =========================================================================
    // 从ROS参数服务器读取motors参数,解析并存储到motors_向量中
    // 
    // 参数格式:
    //   motors:
    //     - name: "joint1"
    //       ethercat_id: 1
    //       can_node_id: 3
    //       can_channel: "CTRL1"
    //       actuator_type: "POWER_FLOW_R86"
    //       torque_limit: 100.0
    //       velocity_limit: 37.7
    // 
    // 默认配置 (当ROS参数不存在时):
    //   joint1: R86-2, CAN ID=3, CTRL1
    //   joint2: R86-2, CAN ID=2, CTRL1
    //   joint3: R52,   CAN ID=3, CTRL2
    //   joint4: R52,   CAN ID=5, CTRL2
    // =========================================================================
    void loadMotorConfig()
    {
        XmlRpc::XmlRpcValue motor_list;
        
        // 尝试获取motors参数
        if (!nh_.getParam("motors", motor_list)) {
            // 参数不存在时使用默认X1机器人配置
            ROS_WARN("No motors configured, using default X1 robot config");
            motors_.push_back({"joint1", 1, 3, xyber::CtrlChannel::CTRL_CH1, 
                              xyber::ActuatorType::POWER_FLOW_R86});
            motors_.push_back({"joint2", 1, 2, xyber::CtrlChannel::CTRL_CH1, 
                              xyber::ActuatorType::POWER_FLOW_R86});
            motors_.push_back({"joint3", 1, 3, xyber::CtrlChannel::CTRL_CH2, 
                              xyber::ActuatorType::POWER_FLOW_R52});
            motors_.push_back({"joint4", 1, 5, xyber::CtrlChannel::CTRL_CH2, 
                              xyber::ActuatorType::POWER_FLOW_R52});
            for (const auto& m : motors_) {
                motor_names_.push_back(m.name);
            }
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
    // 构建电机映射表
    // =========================================================================
    // 构建三个映射表用于电机定位:
    //   1. motor_id_map_: motor_id → name (仅通过ID查找)
    //   2. motor_channel_id_map_: (channel, motor_id) → name (通过通道+ID精确定位)
    //   3. motor_type_map_: name → type_string (获取电机型号)
    // 
    // 注意: 由于同一通道上可能存在相同CAN ID的电机(如joint1和joint3都ID=3但不同通道)
    //       因此必须使用 channel+motor_id 组合来精确定位电机
    // =========================================================================
    void buildMotorIdMap()
    {
        motor_id_map_.clear();
        motor_channel_id_map_.clear();
        motor_type_map_.clear();
        
        for (const auto& m : motors_) {
            motor_id_map_[m.can_node_id] = m.name;
            motor_channel_id_map_[{m.can_channel, m.can_node_id}] = m.name;
            motor_type_map_[m.name] = actuatorTypeToString(m.actuator_type);
        }
        
        ROS_INFO("Motor ID map: %zu motors", motor_id_map_.size());
        for (const auto& [id, name] : motor_id_map_) {
            ROS_INFO("  ID %d -> %s (type: %s)", id, name.c_str(), motor_type_map_[name].c_str());
        }
    }

    // =========================================================================
    // 通过通道+ID查找电机名称
    // =========================================================================
    // 参数:
    //   channel - CAN通道 (1=CTRL1, 2=CTRL2, 3=CTRL3)
    //   motor_id - CAN节点ID (1-8)
    // 返回: 电机名称 (如 "joint1"), 找不到返回空字符串
    // =========================================================================
    std::string getMotorNameByChannelAndId(uint8_t channel, uint8_t motor_id)
    {
        xyber::CtrlChannel ch = (channel == 2) ? xyber::CtrlChannel::CTRL_CH2 : 
                                (channel == 3) ? xyber::CtrlChannel::CTRL_CH3 : 
                                xyber::CtrlChannel::CTRL_CH1;
        auto key = std::make_pair(ch, motor_id);
        auto it = motor_channel_id_map_.find(key);
        if (it != motor_channel_id_map_.end()) {
            return it->second;
        }
        return "";
    }

    // =========================================================================
    // 通过电机名称获取型号
    // =========================================================================
    std::string getMotorTypeByName(const std::string& name)
    {
        auto it = motor_type_map_.find(name);
        if (it != motor_type_map_.end()) {
            return it->second;
        }
        return "";
    }

    // =========================================================================
    // ActuatorType 枚举转字符串
    // =========================================================================
    std::string actuatorTypeToString(xyber::ActuatorType type)
    {
        switch (type) {
            case xyber::ActuatorType::POWER_FLOW_R86: return "POWER_FLOW_R86";
            case xyber::ActuatorType::POWER_FLOW_R52: return "POWER_FLOW_R52";
            case xyber::ActuatorType::POWER_FLOW_L28: return "POWER_FLOW_L28";
            case xyber::ActuatorType::OMNI_PICKER: return "OMNI_PICKER";
            default: return "UNKNOWN";
        }
    }

    // =========================================================================
    // 计算多圈累加位置
    // =========================================================================
    // 通过检测过零点来累加圈数
    // 电机原始位置范围是 ±6.283 rad (±360°), 跨越边界时累加圈数
    // 
    // 算法:
    //   当位置从正转负 (diff > π) → 圈数减1
    //   当位置从负转正 (diff < -π) → 圈数加1
    // 
    // 返回: 累加后的多圈位置 = revolutions * 2π + raw_pos
    // =========================================================================
    float getCumulativePosition(const std::string& name, float raw_pos)
    {
        float last_pos = last_positions_[name];
        float diff = raw_pos - last_pos;
        
        // 检测过零点 (跳变超过 π)
        if (diff > M_PI) {
            // 从正到负转，圈数减1
            revolution_counts_[name]--;
        } else if (diff < -M_PI) {
            // 从负到正转，圈数加1
            revolution_counts_[name]++;
        }
        
        last_positions_[name] = raw_pos;
        
        // 返回累加位置 = 圈数 * 2π + 当前位置
        return revolution_counts_[name] * 2.0f * M_PI + raw_pos;
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
    //   1. 按 ethercat_id 分组创建 DCU 实例
    //   2. 挂载执行器到对应 DCU 的指定通道
    //   3. 设置实时优先级 (RT thread priority 99, bind to CPU 1)
    //   4. 启动 EtherCAT 通信
    //   5. 启动状态监控线程 (每秒输出所有电机状态)
    // 
    // 参数:
    //   ifname   - 网卡名称 (如 "eth0")
    //   enable_dc - 是否启用分布式时钟
    //   cycle_ns - 通信周期 (纳秒), 默认1ms (1000000ns)
    // =========================================================================
    bool start(const std::string& ifname, bool enable_dc, uint64_t cycle_ns)
    {
        if (xyber_ctrl_ == nullptr) {
            ROS_ERROR("Controller not initialized");
            return false;
        }

        // 创建DCU实例 (按ethercat_id分组,相同ethercat_id的电机共用一个DCU)
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

        // 设置实时优先级并启动EtherCAT
        xyber_ctrl_->SetRealtime(99, 1);
        if (!xyber_ctrl_->Start(ifname, cycle_ns, enable_dc)) {
            ROS_ERROR("Failed to start EtherCAT");
            return false;
        }

        // 等待EtherCAT稳定
        ros::Duration(2.0).sleep();

        ROS_INFO("DCU Driver started. Use /motor/command to control motors.");
        is_running_ = true;
        
        ROS_INFO("Motor count: %zu, names: ", motor_names_.size());
        for (size_t i = 0; i < motor_names_.size(); ++i) {
            ROS_INFO("  [%zu] %s", i, motor_names_[i].c_str());
        }
        
        // 启动状态监控线程
        startStateMonitor();
        
        // 可选: 自动测试模式
        bool run_test = false;
        nh_.param<bool>("run_auto_test", run_test, false);
        if (run_test) {
            std::thread test_thread(&DCUDriverServer::testMotor, this);
            test_thread.detach();
        }

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
    // 控制模式转换 (用户mode → SDK mode)
    // =========================================================================
    // 用户发送的mode (MotorCommand.msg):
    //   0: MODE_CURRENT       - 电流环模式
    //   1: MODE_CURRENT_RAMP  - 电流环梯形加减速
    //   2: MODE_VELOCITY      - 速度环模式
    //   3: MODE_VELOCITY_RAMP - 速度环梯形加减速
    //   4: MODE_POSITION       - 位置环模式
    //   5: MODE_POSITION_RAMP  - 位置环梯形加减速
    //   6: MODE_MIT           - MIT混合控制模式 (默认)
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
    //   cmd=3: 设置控制模式 (mode=0-6)
    //   cmd=4: MIT控制 (pos+vel+torque+kp+kd)
    // 
    // 电机定位: 通过 channel + motor_id 组合查找电机名称
    // 型号校验: 可选检查 motor_type 是否匹配
    // =========================================================================
    void motorCmdCB(const dcu_driver_pkg::MotorCommand::ConstPtr& msg)
    {
        // 通过 channel + motor_id 查找电机
        std::string name = getMotorNameByChannelAndId(msg->channel, msg->motor_id);
        if (name.empty()) {
            ROS_WARN("Unknown motor: channel=%d, motor_id=%d", msg->channel, msg->motor_id);
            return;
        }

        // 可选: 校验电机型号
        if (!msg->motor_type.empty()) {
            std::string expected_type = getMotorTypeByName(name);
            if (!expected_type.empty() && msg->motor_type != expected_type) {
                ROS_WARN("Motor type mismatch: expected %s, got %s", 
                         expected_type.c_str(), msg->motor_type.c_str());
                return;
            }
        }

        switch (msg->cmd) {
            case 1: // 使能电机
                if (!xyber_ctrl_->EnableActuator(name)) {
                    ROS_ERROR("Failed to enable %s", name.c_str());
                    return;
                }
                break;

            case 2: // 禁能电机
                if (!xyber_ctrl_->DisableActuator(name)) {
                    ROS_ERROR("Failed to disable %s", name.c_str());
                    return;
                }
                break;

            case 3: // 设置控制模式
                xyber_ctrl_->SetMode(name, modeToXyberMode(msg->mode));
                break;

            case 4: // MIT控制
                xyber_ctrl_->SetMitCmd(name, msg->q, msg->dq, msg->tau, msg->kp, msg->kd);
                ROS_DEBUG("MIT cmd: %s q=%.3f kp=%.1f kd=%.1f",
                         name.c_str(), msg->q, msg->kp, msg->kd);
                break;

            default:
                ROS_WARN("Unknown cmd: %d", msg->cmd);
                break;
        }
    }

    // =========================================================================
    // ROS Action 回调函数 (executeCB)
    // =========================================================================
    // 用于多电机同时控制,通过 Action 接口
    // 
    // Action名称: dcu_control
    // Goal: joint_names + positions + velocities + efforts + stiffness + damping
    // Result: success + message
    // Feedback: current_positions + velocities + efforts
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
            
            // 读取当前状态 (使用累加位置)
            float raw_pos = xyber_ctrl_->GetPosition(name);
            feedback.current_positions.push_back(getCumulativePosition(name, raw_pos));
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
    // 定时发布 /joint_states 话题,频率100Hz
    // 内容: 所有电机的 name/position(多圈累加)/velocity/effort
    // =========================================================================
    void publishStates()
    {
        if (!is_running_) return;
        
        sensor_msgs::JointState joint_state;
        joint_state.header.stamp = ros::Time::now();

        for (const auto& name : motor_names_) {
            joint_state.name.push_back(name);
            float raw_pos = xyber_ctrl_->GetPosition(name);
            joint_state.position.push_back(getCumulativePosition(name, raw_pos));
            joint_state.velocity.push_back(xyber_ctrl_->GetVelocity(name));
            joint_state.effort.push_back(xyber_ctrl_->GetEffort(name));
        }
        joint_states_pub_.publish(joint_state);
    }

    // =========================================================================
    // 电机状态监控线程
    // =========================================================================
    // 独立线程,每秒读取并显示所有电机的实时状态
    // 输出格式:
    //   ========== Motor States ==========
    //   [joint1] pos=0.000 rad (raw=-6.283), vel=-12.566 rad/s, effort=-100.000 Nm, state=0, mode=6
    //   [joint2] pos=0.000 rad (raw=-6.283), vel=-12.566 rad/s, effort=-100.000 Nm, state=0, mode=6
    //   ...
    //   ===================================
    // =========================================================================
    void startStateMonitor()
    {
        state_monitor_thread_ = std::thread([this]() {
            while (is_running_ && ros::ok()) {
                ROS_INFO("========== Motor States ==========");
                for (const auto& name : motor_names_) {
                    float raw_pos = xyber_ctrl_->GetPosition(name);
                    float pos = getCumulativePosition(name, raw_pos);
                    float vel = xyber_ctrl_->GetVelocity(name);
                    float effort = xyber_ctrl_->GetEffort(name);
                    xyber::ActautorState state = xyber_ctrl_->GetPowerState(name);
                    xyber::ActautorMode mode = xyber_ctrl_->GetMode(name);
                    ROS_INFO("[%s] pos=%.3f rad (raw=%.3f), vel=%.3f rad/s, effort=%.3f Nm, state=%d, mode=%d",
                             name.c_str(), pos, raw_pos, vel, effort, (int)state, (int)mode);
                }
                ROS_INFO("===================================");
                std::this_thread::sleep_for(std::chrono::seconds(1));
            }
        });
    }

    // =========================================================================
    // 主循环 (spin)
    // =========================================================================
    // 处理ROS回调(定时100Hz)和发布状态
    // =========================================================================
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

    // =========================================================================
    // 电机自动测试
    // =========================================================================
    // 可选功能,通过设置 run_auto_test:=true 启用
    // 测试流程:
    //   1. 使能电机 → 检查state是否变为1
    //   2. 设置MIT模式 → 检查mode是否为6
    //   3. 禁能电机 → 检查state是否变为0
    // =========================================================================
    void testMotor()
    {
        ros::Duration(3.0).sleep();

        ROS_INFO("========== Motor Auto Test Started ==========");

        for (const auto& name : motor_names_) {
            ROS_INFO("Testing motor: %s", name.c_str());
            bool test_passed = true;

            // Step 1: 使能电机
            ROS_INFO("  -> Step 1: Enabling motor...");
            xyber::ActautorState state_before = xyber_ctrl_->GetPowerState(name);
            bool enable_ret = xyber_ctrl_->EnableActuator(name);
            ros::Duration(1.0).sleep();
            xyber::ActautorState state_after = xyber_ctrl_->GetPowerState(name);
            
            if (enable_ret && static_cast<int>(state_after) == 1) {
                ROS_INFO("  -> [PASS] Motor enabled successfully.");
            } else {
                ROS_ERROR("  -> [FAIL] Motor enable failed (state=%d).", static_cast<int>(state_after));
                test_passed = false;
            }

            if (!test_passed) {
                xyber_ctrl_->DisableActuator(name);
                continue;
            }

            // Step 2: 设置MIT模式
            ROS_INFO("  -> Step 2: Setting mode to MIT (6)...");
            xyber_ctrl_->SetMode(name, xyber::ActautorMode::MODE_MIT);
            ros::Duration(0.3).sleep();
            xyber::ActautorMode current_mode = xyber_ctrl_->GetMode(name);
            
            if (current_mode == xyber::ActautorMode::MODE_MIT) {
                ROS_INFO("  -> [PASS] Mode is MIT.");
            } else {
                ROS_WARN("  -> [WARN] Mode is NOT MIT (actual=%d).", static_cast<int>(current_mode));
            }

            // Step 3: 禁能电机
            ROS_INFO("  -> Step 3: Disabling motor...");
            xyber_ctrl_->DisableActuator(name);
            ros::Duration(0.5).sleep();
            xyber::ActautorState state_disabled = xyber_ctrl_->GetPowerState(name);
            
            if (static_cast<int>(state_disabled) != 1) {
                ROS_INFO("  -> [PASS] Motor disabled successfully.");
            } else {
                ROS_WARN("  -> [WARN] Motor still enabled after disable command.");
            }

            // 总结
            if (test_passed) {
                ROS_INFO("  -> [OVERALL RESULT] Test PASSED for %s", name.c_str());
            } else {
                ROS_ERROR("  -> [OVERALL RESULT] Test FAILED for %s", name.c_str());
            }
            ROS_INFO("----------------------------------------");
        }

        ROS_INFO("========== Motor Auto Test Finished ==========");
    }

private:
    ros::NodeHandle nh_;                                          // ROS节点句柄
    actionlib::SimpleActionServer<dcu_driver_pkg::DCUControlAction> action_server_;  // Action服务
    ros::Subscriber motor_cmd_sub_;                               // 控制指令订阅者
    ros::Publisher joint_states_pub_;                              // 状态发布者
    
    xyber::XyberController* xyber_ctrl_;                           // XyberController单例指针
    std::vector<MotorConfig> motors_;                             // 电机配置列表
    std::vector<std::string> motor_names_;                         // 电机名称列表 (按顺序)
    
    std::unordered_map<uint8_t, std::string> motor_id_map_;       // motor_id → name 映射表
    std::map<std::pair<xyber::CtrlChannel, uint8_t>, std::string> motor_channel_id_map_;  // (channel, motor_id) → name
    std::map<std::string, std::string> motor_type_map_;           // name → type string
    
    std::thread state_monitor_thread_;                            // 状态监控线程
    bool is_running_;                                             // 运行状态标志
    
    std::unordered_map<std::string, int> revolution_counts_;      // 圈数计数器 (用于多圈位置累加)
    std::unordered_map<std::string, float> last_positions_;       // 上一时刻位置 (用于过零点检测)
};

// =============================================================================
// 主函数
// =============================================================================
int main(int argc, char** argv)
{
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