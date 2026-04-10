#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IMU 数据显示节点 - 解码显示IMU数据
"""

import rospy
from sensor_msgs.msg import Imu
import numpy as np


class IMUDisplayNode:
    def __init__(self):
        rospy.init_node('imu_display_node')
        
        self.imu_topic = rospy.get_param('~imu_topic', '/imu_serial/data')
        self.display_rate = rospy.get_param('~display_rate', 10.0)
        self.use_color = rospy.get_param('~use_color', True)
        
        self.sub = rospy.Subscriber(self.imu_topic, Imu, self.imu_callback)
        self.rate = rospy.Rate(self.display_rate)
        self.data_count = 0
        
        rospy.loginfo("✅ IMU 数据显示节点已启动")
        rospy.loginfo(f"   订阅: {self.imu_topic}")
        rospy.loginfo(f"   刷新率: {self.display_rate} Hz")
    
    def show_header(self):
        print("\n" + "=" * 80)
        if self.use_color:
            print("📊 IMU 传感器数据实时显示 - [按 Ctrl+C 退出]")
        else:
            print("IMU 传感器数据实时显示 - [按 Ctrl+C 退出]")
        print("=" * 80)
    
    def quaternion_to_euler(self, x, y, z, w):
        roll = np.arctan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
        
        sin_pitch = 2*(w*y - z*x)
        sin_pitch = sin_pitch if sin_pitch > 1.0 else sin_pitch if sin_pitch < -1.0 else sin_pitch
        pitch = np.arcsin(sin_pitch)
        
        yaw = np.arctan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
        
        return roll, pitch, yaw
    
    def format_color(self, text, color='white'):
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'reset': '\033[0m'
        }
        
        if not self.use_color:
            return text
        
        color_code = colors.get(color, colors['white'])
        return f"{color_code}{text}{colors['reset']}"
    
    def imu_callback(self, msg):
        self.data_count += 1
        
        qw = msg.orientation.w
        qx = msg.orientation.x
        qy = msg.orientation.y
        qz = msg.orientation.z
        
        roll, pitch, yaw = self.quaternion_to_euler(qx, qy, qz, qw)
        
        roll_deg = roll * 180.0 / np.pi
        pitch_deg = pitch * 180.0 / np.pi
        yaw_deg = yaw * 180.0 / np.pi
        
        time_str = rospy.Time.now()
        
        print("\n" + self.format_color(f"📊 IMU数据 #{self.data_count} - {time_str}", 'cyan'))
        print("-" * 80)
        
        if self.use_color:
            print(self.format_color("加速度计 (Accelerometer)", 'yellow'))
        else:
            print("加速度计 (Accelerometer)")
        print(f"  X轴: {msg.linear_acceleration.x:+8.3f} g   Y轴: {msg.linear_acceleration.y:+8.3f} g   Z轴: {msg.linear_acceleration.z:+8.3f} g")
        print(f"  合成: {np.sqrt(msg.linear_acceleration.x**2 + msg.linear_acceleration.y**2 + msg.linear_acceleration.z**2):.3f} g")
        
        if self.use_color:
            print(f"\n{self.format_color('陀螺仪 (Gyroscope)', 'yellow')}")
        else:
            print("\n陀螺仪 (Gyroscope)")
        print(f"  X轴: {msg.angular_velocity.x:+8.3f}   Y轴: {msg.angular_velocity.y:+8.3f}   Z轴: {msg.angular_velocity.z:+8.3f} rad/s")
        print(f"  合成: {np.sqrt(msg.angular_velocity.x**2 + msg.angular_velocity.y**2 + msg.angular_velocity.z**2):.3f} rad/s")
        
        if self.use_color:
            print(f"\n{self.format_color('姿态 (Orientation)', 'green')}")
        else:
            print("\n姿态 (Orientation)")
        print(f"  四元数: w={qw:+7.4f}, x={qx:+7.4f}, y={qy:+7.4f}, z={qz:+7.4f}")
        print(f"  欧拉角 (ZYX顺序):  Roll={roll_deg:+7.2f}°, Pitch={pitch_deg:+7.2f}°, Yaw={yaw_deg:+7.2f}°")
        
        print("\n" + "=" * 80)
    
    def run(self):
        try:
            while not rospy.is_shutdown():
                self.rate.sleep()
        except KeyboardInterrupt:
            print("\n\n👋 显示节点已退出")
        except rospy.ROSInterruptException:
            print("\n\n📛 收到ROS中断信号")


if __name__ == '__main__':
    try:
        node = IMUDisplayNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
