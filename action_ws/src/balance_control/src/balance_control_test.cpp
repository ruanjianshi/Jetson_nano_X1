/*
 * Balance Control Test Node
 * ==========================
 *
 * 功能说明:
 *   - 模拟IMU数据发送
 *   - 接收平衡控制算法的输出
 *   - 打印电机角度解算结果
 *
 * 测试流程:
 *   1. 模拟IMU发送静止状态 (roll=0, pitch=0, yaw=0)
 *   2. 模拟IMU发送倾斜状态 (roll=0.1, pitch=0.2, yaw=0)
 *   3. 查看算法输出的电机角度
 *
 * 使用方法:
 *   rosrun balance_control balance_control_test
 *
 * Author: Qi Xiao
Email: 2408128687@qq.com
 * 日期: 2026-05-06
 */

#include <ros/ros.h>
#include <sensor_msgs/Imu.h>
#include <std_msgs/Float64MultiArray.h>
#include <Eigen/Dense>
#include <vector>
#include <string>
#include <cmath>

/**
 * @brief 电机角度解算结果
 */
struct MotorAngleResult {
    std::string name;
    double target_angle;  // 目标角度 (rad)
    double torque;        // 力矩 (Nm)
    double kp;            // 刚度
    double kd;            // 阻尼
};

/**
 * @brief 平衡控制测试类
 */
class BalanceControlTest {
public:
    BalanceControlTest()
        : test_count_(0)
    {
        // 创建IMU模拟发布者
        imu_pub_ = nh_.advertise<sensor_msgs::Imu>("/imu_serial/data", 10);

        // 创建电机角度结果订阅者
        // 注: 需要平衡控制器发布解算结果
        motor_angle_sub_ = nh_.subscribe("/balance_control/motor_angles", 10,
                                         &BalanceControlTest::motorAngleCallback, this);

        // 电机配置
        motor_configs_.push_back({"left_joint_1", 0, 3, 1});   // 左髋横滚
        motor_configs_.push_back({"left_joint_2", 0, 3, 1});   // 左髋俯仰
        motor_configs_.push_back({"left_joint_3", 0, 3, 2});   // 左膝俯仰
        motor_configs_.push_back({"left_joint_wheel", 0, 3, 2});  // 左轮
        motor_configs_.push_back({"right_joint_1", 1, 2, 1});  // 右髋横滚
        motor_configs_.push_back({"right_joint_2", 1, 2, 1});  // 右髋俯仰
        motor_configs_.push_back({"right_joint_3", 1, 5, 2});  // 右膝俯仰
        motor_configs_.push_back({"right_joint_wheel", 1, 5, 2});  // 右轮

        ROS_INFO("==========================================");
        ROS_INFO("Balance Control Test Node Started");
        ROS_INFO("==========================================");
    }

    /**
     * @brief 运行测试
     */
    void run() {
        ROS_INFO("Starting test sequence...");

        // 测试1: 静止状态
        testStaticState();

        // 等待2秒
        ros::Duration(2.0).sleep();

        // 测试2: 轻微前倾
        testForwardTilt();

        // 等待2秒
        ros::Duration(2.0).sleep();

        // 测试3: 轻微左倾
        testLeftRoll();

        // 等待2秒
        ros::Duration(2.0).sleep();

        // 测试4: 组合倾斜
        testCombinedTilt();

        ROS_INFO("==========================================");
        ROS_INFO("Test Complete");
        ROS_INFO("==========================================");
    }

private:
    /**
     * @brief 模拟IMU数据
     */
    void publishIMU(double roll, double pitch, double yaw) {
        sensor_msgs::Imu msg;

        // 设置时间戳
        msg.header.stamp = ros::Time::now();
        msg.header.frame_id = "imu_link";

        // 四元数转换 (从欧拉角)
        Eigen::Quaterniond q = eulerToQuaternion(roll, pitch, yaw);

        msg.orientation.w = q.w();
        msg.orientation.x = q.x();
        msg.orientation.y = q.y();
        msg.orientation.z = q.z();

        // 模拟角速度 (基于姿态变化率)
        msg.angular_velocity.x = 0.0;
        msg.angular_velocity.y = 0.0;
        msg.angular_velocity.z = 0.0;

        // 模拟线加速度 (静止时约为重力)
        msg.linear_acceleration.x = -9.81 * sin(pitch);
        msg.linear_acceleration.y = 9.81 * sin(roll);
        msg.linear_acceleration.z = 9.81 * cos(roll) * cos(pitch);

        // 协方差矩阵 (设为单位矩阵表示不确定度)
        msg.orientation_covariance[0] = 0.1;
        msg.orientation_covariance[4] = 0.1;
        msg.orientation_covariance[8] = 0.1;

        imu_pub_.publish(msg);

        ROS_INFO("Publishing IMU data: roll=%.3f, pitch=%.3f, yaw=%.3f", roll, pitch, yaw);
    }

    /**
     * @brief 计算电机角度 (简化模型)
     *
     * 根据目标姿态计算各关节的目标角度:
     *   - roll > 0: 身体右倾 -> 左腿外展, 右腿内收
     *   - pitch > 0: 身体前倾 -> 髋关节前屈, 膝关节伸展
     */
    void computeMotorAngles(double roll, double pitch, double yaw,
                            std::vector<MotorAngleResult>& results) {
        // 腿部几何参数
        const double UPPER_LEG_LENGTH = 0.2;  // 大腿长度 (m)
        const double LOWER_LEG_LENGTH = 0.2; // 小腿长度 (m)
        const double HIP_OFFSET = 0.1;        // 髋关节偏移 (m)

        // 增益参数
        const double ROLL_GAIN = 0.5;   // roll转髋关节角度增益
        const double PITCH_GAIN = 0.3; // pitch转髋/膝关节角度增益

        // 计算髋关节角度
        double hip_roll = -roll * ROLL_GAIN;  // 右倾时左髋外展
        double hip_pitch = pitch * PITCH_GAIN;  // 前倾时髋屈曲

        // 计算膝关节角度 (保持支撑平衡)
        double knee_pitch = -pitch * PITCH_GAIN * 1.2;  // 前倾时膝伸展

        // 轮子角度 (用于移动控制, 暂设为0)
        double wheel_angle = 0.0;

        ROS_INFO("----------------------------------------");
        ROS_INFO("Pose Computation:");
        ROS_INFO("  Roll: %.3f rad -> Hip Roll: %.3f rad", roll, hip_roll);
        ROS_INFO("  Pitch: %.3f rad -> Hip Pitch: %.3f rad, Knee Pitch: %.3f rad",
                 pitch, hip_pitch, knee_pitch);
        ROS_INFO("----------------------------------------");
        ROS_INFO("%-20s %10s %10s %6s %6s", "Motor", "Angle(rad)", "Torque(Nm)", "Kp", "Kd");
        ROS_INFO("----------------------------------------");

        // 左腿电机 (4个)
        results.push_back({"left_joint_1", hip_roll, 0.0, 20.0, 2.0});
        results.push_back({"left_joint_2", hip_pitch, 0.0, 20.0, 2.0});
        results.push_back({"left_joint_3", knee_pitch, 0.0, 15.0, 1.5});
        results.push_back({"left_joint_wheel", wheel_angle, 0.0, 10.0, 1.0});

        // 右腿电机 (4个) - roll方向相反
        results.push_back({"right_joint_1", -hip_roll, 0.0, 20.0, 2.0});
        results.push_back({"right_joint_2", hip_pitch, 0.0, 20.0, 2.0});
        results.push_back({"right_joint_3", knee_pitch, 0.0, 15.0, 1.5});
        results.push_back({"right_joint_wheel", wheel_angle, 0.0, 10.0, 1.0});

        // 打印结果
        for (const auto& r : results) {
            ROS_INFO("%-20s %10.3f %10.3f %6.1f %6.1f",
                     r.name.c_str(), r.target_angle, r.torque, r.kp, r.kd);
        }

        ROS_INFO("----------------------------------------");
    }

    /**
     * @brief 测试1: 静止状态
     */
    void testStaticState() {
        test_count_++;
        ROS_INFO("\n[Test %d] Static (roll=0, pitch=0, yaw=0)", test_count_);

        publishIMU(0.0, 0.0, 0.0);

        std::vector<MotorAngleResult> results;
        computeMotorAngles(0.0, 0.0, 0.0, results);
    }

    /**
     * @brief Test 2: Forward tilt
     */
    void testForwardTilt() {
        test_count_++;
        ROS_INFO("\n[Test %d] Forward tilt (roll=0, pitch=0.2, yaw=0)", test_count_);

        publishIMU(0.0, 0.2, 0.0);

        std::vector<MotorAngleResult> results;
        computeMotorAngles(0.0, 0.2, 0.0, results);
    }

    /**
     * @brief Test 3: Left roll
     */
    void testLeftRoll() {
        test_count_++;
        ROS_INFO("\n[Test %d] Left roll (roll=0.1, pitch=0, yaw=0)", test_count_);

        publishIMU(0.1, 0.0, 0.0);

        std::vector<MotorAngleResult> results;
        computeMotorAngles(0.1, 0.0, 0.0, results);
    }

    /**
     * @brief Test 4: Combined tilt
     */
    void testCombinedTilt() {
        test_count_++;
        ROS_INFO("\n[Test %d] Combined tilt (roll=0.1, pitch=0.15, yaw=0.05)", test_count_);

        publishIMU(0.1, 0.15, 0.05);

        std::vector<MotorAngleResult> results;
        computeMotorAngles(0.1, 0.15, 0.05, results);
    }

    /**
     * @brief 欧拉角转四元数
     */
    Eigen::Quaterniond eulerToQuaternion(double roll, double pitch, double yaw) {
        Eigen::Quaterniond q;

        // ZYX顺序 (先绕Z, 再Y, 最后X)
        double cy = cos(yaw * 0.5);
        double sy = sin(yaw * 0.5);
        double cp = cos(pitch * 0.5);
        double sp = sin(pitch * 0.5);
        double cr = cos(roll * 0.5);
        double sr = sin(roll * 0.5);

        q.w() = cr * cp * cy + sr * sp * sy;
        q.x() = sr * cp * cy - cr * sp * sy;
        q.y() = cr * sp * cy + sr * cp * sy;
        q.z() = cr * cp * sy - sr * sp * cy;

        return q;
    }

    /**
     * @brief 电机角度回调
     */
    void motorAngleCallback(const std_msgs::Float64MultiArray::ConstPtr& msg) {
        ROS_INFO("Received motor angles: %zu values", msg->data.size());
        for (size_t i = 0; i < msg->data.size() && i < 8; ++i) {
            ROS_INFO("  motor[%zu]: %.3f rad", i, msg->data[i]);
        }
    }

private:
    ros::NodeHandle nh_;
    ros::Publisher imu_pub_;
    ros::Subscriber motor_angle_sub_;

    struct MotorConfig {
        std::string name;
        uint8_t leg;
        uint8_t motor_id;
        uint8_t channel;
    };

    std::vector<MotorConfig> motor_configs_;
    int test_count_;
};

/*
 * Main Entry Point
 * ================
 */
int main(int argc, char** argv) {
    ros::init(argc, argv, "balance_control_test");

    try {
        BalanceControlTest test;
        ros::Duration(1.0).sleep();  // 等待初始化
        test.run();

        // Keep node running to view results
        ros::spin();
    } catch (const std::exception& e) {
        ROS_ERROR("Exception: %s", e.what());
        return 1;
    }

    return 0;
}