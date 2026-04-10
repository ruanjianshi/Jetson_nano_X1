#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
IMU I2C Action Client 示例
========================================
功能说明:
  - 演示如何使用IMU I2C Action Client
  - 支持单次读取、连续读取、校准、配置等操作

使用方法:
  source devel/setup.bash
  python3 imu_i2c_client.py

作者: Jetson Nano
日期: 2026-04-03
"""

import rospy
import actionlib
import sys
from yb_imu_driver.msg import IMUI2CAction, IMUI2CGoal


class IMUI2CClient:
    """
    IMU I2C Action Client 类
    
    职责:
      1. 连接到IMU I2C Action Server
      2. 发送各种操作请求
      3. 接收和显示结果
    """
    
    def __init__(self):
        """
        构造函数 - 初始化客户端
        """
        rospy.init_node('imu_i2c_client')
        
        self.client = actionlib.SimpleActionClient('imu_i2c', IMUI2CAction)
        
        rospy.loginfo("正在连接到 IMU I2C Action Server...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 已连接到 IMU I2C Action Server")
    
    def print_sensor_data(self, result):
        """
        打印传感器数据
        """
        print("\n" + "=" * 60)
        print("📊 传感器数据")
        print("=" * 60)
        print(f"加速度 [g]:          x={result.accel_x: .3f}, y={result.accel_y: .3f}, z={result.accel_z: .3f}")
        print(f"陀螺仪 [rad/s]:      x={result.gyro_x: .3f}, y={result.gyro_y: .3f}, z={result.gyro_z: .3f}")
        print(f"磁力计 [uT]:         x={result.mag_x: .3f}, y={result.mag_y: .3f}, z={result.mag_z: .3f}")
        print(f"四元数:              w={result.quat_w: .5f}, x={result.quat_x: .5f}, y={result.quat_y: .5f}, z={result.quat_z: .5f}")
        print(f"欧拉角 [rad]:        roll={result.roll: .3f}, pitch={result.pitch: .3f}, yaw={result.yaw: .3f}")
        print(f"气压计:")
        print(f"  高度:              {result.height: .2f} m")
        print(f"  温度:              {result.temperature: .2f} °C")
        print(f"  气压:              {result.pressure: .5f} Pa")
        print(f"  气压差:            {result.pressure_contrast: .5f} Pa")
        print("=" * 60)
    
    def single_read(self):
        """
        单次读取传感器数据
        """
        print("\n📖 单次读取模式")
        
        goal = IMUI2CGoal()
        goal.operation_type = 0
        
        self.client.send_goal(goal)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        if result.success:
            self.print_sensor_data(result)
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")
        
        return result.success
    
    def continuous_read(self, duration=5.0):
        """
        连续读取传感器数据
        
        参数:
            duration: 连续读取时长(秒)
        """
        print(f"\n📖 连续读取模式, 时长: {duration}秒")
        
        goal = IMUI2CGoal()
        goal.operation_type = 1
        goal.duration = duration
        
        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        
        finished = self.client.wait_for_result(rospy.Duration(duration + 2))
        
        if finished:
            result = self.client.get_result()
            if result.success:
                self.print_sensor_data(result)
                print(f"✅ {result.message}")
            else:
                print(f"❌ {result.message}")
            return result.success
        else:
            print("❌ 超时")
            return False
    
    def feedback_callback(self, feedback):
        """
        反馈回调函数
        
        参数:
            feedback: 服务器发送的反馈
        """
        print(f"\r📊 进度: {feedback.progress}% | {feedback.status}", end="", flush=True)
    
    def calibrate_imu(self, calib_type=0):
        """
        校准IMU
        
        参数:
            calib_type: 0=自动(陀螺仪+加速度计), 1=陀螺仪, 2=加速度计
        """
        calib_names = {0: "自动(陀螺仪+加速度计)", 1: "陀螺仪", 2: "加速度计"}
        print(f"\n🔧 IMU校准模式, 类型: {calib_names.get(calib_type, calib_type)}")
        
        goal = IMUI2CGoal()
        goal.operation_type = 2
        goal.calibration_type = calib_type
        
        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        if result.success:
            print(f"\n✅ {result.message}")
        else:
            print(f"\n❌ {result.message}")
        
        return result.success
    
    def calibrate_mag(self):
        """
        校准磁力计
        """
        print("\n🔧 磁力计校准模式")
        
        goal = IMUI2CGoal()
        goal.operation_type = 3
        
        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        if result.success:
            print(f"\n✅ {result.message}")
        else:
            print(f"\n❌ {result.message}")
        
        return result.success
    
    def calibrate_temperature(self, temperature=25.0):
        """
        校准温度
        
        参数:
            temperature: 校准温度值
        """
        print(f"\n🔧 温度校准模式, 温度: {temperature}°C")
        
        goal = IMUI2CGoal()
        goal.operation_type = 4
        goal.calibration_temperature = temperature
        
        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        if result.success:
            print(f"\n✅ {result.message}")
        else:
            print(f"\n❌ {result.message}")
        
        return result.success
    
    def set_algorithm(self, algo_type=9):
        """
        设置融合算法
        
        参数:
            algo_type: 6或9
        """
        algo_names = {6: "六轴", 9: "九轴"}
        print(f"\n⚙️  设置融合算法为{algo_names.get(algo_type, algo_type)}算法")
        
        goal = IMUI2CGoal()
        goal.operation_type = 5
        goal.algorithm_type = algo_type
        
        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        if result.success:
            print(f"\n✅ {result.message}")
        else:
            print(f"\n❌ {result.message}")
        
        return result.success
    
    def interactive_menu(self):
        """
        交互式菜单
        """
        while not rospy.is_shutdown():
            print("\n" + "=" * 60)
            print("IMU I2C Action Client - 交互式菜单")
            print("=" * 60)
            print("1. 单次读取")
            print("2. 连续读取 (5秒)")
            print("3. IMU校准 (自动)")
            print("4. 磁力计校准")
            print("5. 温度校准")
            print("6. 设置融合算法 (九轴)")
            print("7. 设置融合算法 (六轴)")
            print("0. 退出")
            print("=" * 60)
            
            choice = input("请选择操作 (0-7): ").strip()
            
            if choice == '1':
                self.single_read()
            elif choice == '2':
                self.continuous_read(5.0)
            elif choice == '3':
                self.calibrate_imu(0)
            elif choice == '4':
                self.calibrate_mag()
            elif choice == '5':
                temp = input("请输入当前温度 (°C): ").strip()
                try:
                    temperature = float(temp)
                    self.calibrate_temperature(temperature)
                except ValueError:
                    print("❌ 无效的温度值")
            elif choice == '6':
                self.set_algorithm(9)
            elif choice == '7':
                self.set_algorithm(6)
            elif choice == '0':
                print("👋 再见!")
                break
            else:
                print("❌ 无效的选择")


if __name__ == '__main__':
    try:
        client = IMUI2CClient()
        
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == 'single':
                client.single_read()
            elif command == 'continuous':
                duration = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
                client.continuous_read(duration)
            elif command == 'calibrate':
                client.calibrate_imu(0)
            elif command == 'calibrate_mag':
                client.calibrate_mag()
            elif command == 'calibrate_temp':
                temp = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0
                client.calibrate_temperature(temp)
            elif command == 'algo9':
                client.set_algorithm(9)
            elif command == 'algo6':
                client.set_algorithm(6)
            else:
                print(f"❌ 未知的命令: {command}")
                print("可用命令: single, continuous [duration], calibrate, calibrate_mag, calibrate_temp [temp], algo9, algo6")
        else:
            client.interactive_menu()
            
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        print(f"❌ 错误: {e}")