/*
 * Robot Hardware Parameters
 * =========================
 *
 * 功能说明:
 *   - 定义轮腿机器人硬件参数结构
 *   - 支持从ROS参数服务器或YAML文件加载
 *   - 提供参数的getter/setter方法
 *   - 支持软限位和安全检查
 *
 * 使用方法:
 *   RobotHardwareParams params;
 *   params.loadFromYaml("/path/to/config.yaml");
 *   params.loadFromParamServer(nh);
 *
 *   // 使用参数
 *   auto limits = params.getMotorLimits("R86");
 *   params.applySoftLimits("hip_roll", angle);
 *
 * 作者: Jetson Nano
 * 日期: 2026-05-06
 */

#ifndef ROBOT_HARDWARE_PARAMS_H
#define ROBOT_HARDWARE_PARAMS_H

#include <string>
#include <vector>
#include <Eigen/Dense>
#include <ros/ros.h>

namespace balance_control {

/**
 * @brief 电机配置结构
 */
struct MotorConfig {
    std::string name;                // 关节名称
    uint8_t motor_id;                 // CAN节点ID (1-8)
    uint8_t channel;                  // CAN通道: 1=CTRL1, 2=CTRL2
    std::string motor_type;          // 电机型号: R86/R52/R28
    std::string joint_type;          // 关节类型: hip_roll/pitch, knee_pitch, wheel
    int8_t direction;                // 控制方向: 1=正向, -1=反向
};

/**
 * @brief 电机限幅参数
 */
struct MotorLimitParams {
    double max_torque;               // 最大力矩 (Nm)
    double max_velocity;             // 最大速度 (rad/s)
    double position_min;             // 最小位置 (rad)
    double position_max;             // 最大位置 (rad)
    double kp_default;               // 默认刚度
    double kd_default;               // 默认阻尼
};

/**
 * @brief IMU配置参数
 */
struct IMUConfig {
    double position_x;               // 安装位置X (m)
    double position_y;               // 安装位置Y (m)
    double position_z;               // 安装位置Z (m)

    double rotation_roll;           // 安装横滚角误差 (rad)
    double rotation_pitch;           // 安装俯仰角误差 (rad)
    double rotation_yaw;             // 安装偏航角误差 (rad)

    double neutral_roll;            // 中立横滚角 (rad)
    double neutral_pitch;           // 中立俯仰角 (rad)
    double neutral_yaw;             // 中立偏航角 (rad)

    double balance_roll_max;         // 最大横滚角 (rad)
    double balance_pitch_max;        // 最大俯仰角 (rad)
    double balance_yaw_max;          // 最大偏航角 (rad)
};

/**
 * @brief 腿部几何参数
 */
struct LegGeometry {
    double upper_leg_length;        // 大腿长度 (m)
    double lower_leg_length;         // 小腿长度 (m)
    double hip_offset_x;              // 髋关节X偏移 (m)
    double hip_offset_y;              // 髋关节Y偏移 (m)
    double hip_offset_z;             // 髋关节Z偏移 (m)
    double leg_length_min;           // 最小腿长 (m)
    double leg_length_max;           // 最大腿长 (m)
    double foot_height_min;          // 足端最小高度 (m)
    double foot_height_max;          // 足端最大高度 (m)
};

/**
 * @brief 轮子参数
 */
struct WheelConfig {
    double radius;                   // 轮子半径 (m)
    double width;                    // 轮子宽度 (m)
    double wheel_base;              // 两轮间距 (m)
    double max_wheel_speed;         // 最大轮速 (rad/s)
    double driver_kp;               // 驱动刚度
    double driver_kd;               // 驱动阻尼
};

/**
 * @brief PID参数
 */
struct PIDParams {
    double kp_roll;                 // 横滚P
    double kd_roll;                 // 横滚D
    double ki_roll;                 // 横滚I

    double kp_pitch;                // 俯仰P
    double kd_pitch;                // 俯仰D
    double ki_pitch;                // 俯仰I

    double kp_yaw;                  // 偏航P
    double kd_yaw;                  // 偏航D
    double ki_yaw;                  // 偏航I
};

/**
 * @brief 控制参数
 */
struct ControlParams {
    int control_frequency;          // 控制频率 (Hz)
    std::string ethercat_if;        // 网卡名称
    uint64_t cycle_ns;             // 通信周期 (ns)
    bool enable_dc;                // 是否启用DC
    std::string default_mode;      // 默认控制模式
    double emergency_stop_threshold;  // 紧急停止阈值 (Nm)
};

/**
 * @brief 关节软限位
 */
struct JointSoftLimits {
    double hip_roll_min;
    double hip_roll_max;
    double hip_pitch_min;
    double hip_pitch_max;
    double knee_pitch_min;
    double knee_pitch_max;
    double wheel_min;
    double wheel_max;
};

/**
 * @brief 关节标零位置
 */
struct JointHomeParams {
    double hip_roll;
    double hip_pitch;
    double knee_pitch;
    double wheel;

    double hip_roll_offset;
    double hip_pitch_offset;
    double knee_pitch_offset;
    double wheel_offset;
};

/**
 * @brief 目标姿态
 */
struct TargetPose {
    double roll;
    double pitch;
    double yaw;
};

/**
 * @brief 机器人硬件参数类
 */
class RobotHardwareParams {
public:
    /**
     * @brief 构造函数 - 初始化默认参数
     */
    RobotHardwareParams();

    // ========== 加载方法 ==========

    /**
     * @brief 从ROS参数服务器加载参数
     * @param nh 节点句柄
     * @param namespace_prefix 参数命名空间前缀
     */
    void loadFromParamServer(ros::NodeHandle& nh,
                              const std::string& namespace_prefix = "");

    /**
     * @brief 从YAML文件加载参数
     * @param file_path YAML文件路径
     */
    void loadFromYaml(const std::string& file_path);

    /**
     * @brief 打印参数概要
     */
    void printSummary() const;

    // ========== 获取参数 ==========

    // 机器人基本信息
    std::string getRobotName() const { return robot_name_; }
    std::string getRobotType() const { return robot_type_; }
    double getMass() const { return mass_; }
    double getGravity() const { return gravity_; }

    // 腿部几何
    const LegGeometry& getLegGeometry() const { return leg_geometry_; }

    // 轮子配置
    const WheelConfig& getWheelConfig() const { return wheel_config_; }

    // IMU配置
    const IMUConfig& getIMUConfig() const { return imu_config_; }

    // 电机配置
    const std::vector<MotorConfig>& getMotorConfigs() const { return motor_configs_; }
    const MotorLimitParams& getR86LimitParams() const { return r86_limits_; }
    const MotorLimitParams& getR52LimitParams() const { return r52_limits_; }

    // 控制参数
    const ControlParams& getControlParams() const { return control_params_; }

    // PID参数
    const PIDParams& getPIDParams() const { return pid_params_; }

    // 关节限位
    const JointSoftLimits& getJointSoftLimits() const { return joint_limits_; }

    // 标零位置
    const JointHomeParams& getJointHomeParams() const { return joint_home_; }

    // 目标姿态
    const TargetPose& getTargetPose() const { return target_pose_; }

    // 算法配置
    std::string getAlgorithm() const { return algorithm_; }
    double getMaxTorque() const { return max_torque_; }
    double getMaxVelocity() const { return max_velocity_; }

    // ========== 设置参数 ==========

    void setTargetPose(double roll, double pitch, double yaw);
    void setPIDParams(const PIDParams& params);
    void setControlFrequency(int freq);
    void setAlgorithm(const std::string& algo) { algorithm_ = algo; }

    // ========== 查询方法 ==========

    /**
     * @brief 根据关节名称查找电机配置
     */
    const MotorConfig* findMotorConfig(const std::string& joint_name) const;

    /**
     * @brief 根据电机ID和通道查找电机配置
     */
    const MotorConfig* findMotorConfigById(uint8_t motor_id, uint8_t channel) const;

    /**
     * @brief 获取电机限幅参数
     */
    MotorLimitParams getMotorLimits(const std::string& motor_type) const;

    /**
     * @brief 计算IMU中性姿态补偿
     */
    Eigen::Vector3d getIMUNeutralOffset() const;

    /**
     * @brief 验证姿态是否在安全范围内
     */
    bool isPoseSafe(double roll, double pitch) const;

    // ========== 安全限制方法 ==========

    /**
     * @brief 应用软限位
     * @param joint_type 关节类型
     * @param value 输入输出值 (会被限制)
     * @return 是否在限制内 (false表示被限制过)
     */
    bool applySoftLimits(const std::string& joint_type, double& value) const;

    /**
     * @brief 施力矩限制
     * @param motor_type 电机型号
     * @param torque 输入力矩
     * @return 限制后的力矩
     */
    double applyTorqueLimit(const std::string& motor_type, double torque) const;

    // ========== 运动学方法 ==========

    /**
     * @brief 获取髋关节变换矩阵
     * @param leg 腿编号 (0=左, 1=右)
     */
    Eigen::Matrix4d getHipTransform(uint8_t leg) const;

    /**
     * @brief 计算当前腿长
     * @param hip_pitch 髋俯仰角 (rad)
     * @param knee_pitch 膝俯仰角 (rad)
     */
    double computeLegLength(double hip_pitch, double knee_pitch) const;

private:
    /**
     * @brief 初始化默认参数
     */
    void initDefaultParams();

    // ========== 机器人基本信息 ==========
    std::string robot_name_;
    std::string robot_type_;
    double mass_;
    double gravity_;

    // ========== 几何参数 ==========
    LegGeometry leg_geometry_;
    WheelConfig wheel_config_;

    // ========== IMU配置 ==========
    IMUConfig imu_config_;

    // ========== 电机配置 ==========
    std::vector<MotorConfig> motor_configs_;
    MotorLimitParams r86_limits_;
    MotorLimitParams r52_limits_;

    // ========== 控制参数 ==========
    ControlParams control_params_;
    PIDParams pid_params_;
    JointSoftLimits joint_limits_;
    JointHomeParams joint_home_;
    TargetPose target_pose_;

    // ========== 算法选择 ==========
    std::string algorithm_;
    double max_torque_;
    double max_velocity_;
};

} // namespace balance_control

#endif // ROBOT_HARDWARE_PARAMS_H