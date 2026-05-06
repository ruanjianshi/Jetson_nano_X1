#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
Keyboard Teleop for Wheeled Legged Robot
========================================

功能说明:
  - 通过键盘控制机器人移动
  - 支持 WASD 移动，QE 转向，空格 跳跃

键盘布局:
    [W]        前进
    [A]        左转
    [S]        后退
    [D]        右转
    [Q]        左转向
    [E]        右转向
    [Space]    跳跃
    [X]        停止
    [C]        进入平衡模式

速度控制:
    [1-9]      设置速度等级 (1=慢, 9=快)
    方向键      侧向移动

使用示例:
  rosrun balance_control robot_keyboard_teleop.py

作者: Jetson Nano
日期: 2026-05-06
"""

import sys
import tty
import termios
from geometry_msgs.msg import Twist

class KeyboardTeleop:
    """
    键盘遥控类
    
    使用标准输入实现类似 cmd_vel 的控制
    """

    # 键盘按键码
    KEY_W = 'w'
    KEY_A = 'a'
    KEY_S = 's'
    KEY_D = 'd'
    KEY_Q = 'q'
    KEY_E = 'e'
    KEY_SPACE = ' '
    KEY_X = 'x'
    KEY_C = 'c'

    def __init__(self):
        rospy.init_node('robot_keyboard_teleop', anonymous=True)
        
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        
        self.speed = 0.5
        self.yaw_rate = 1.0
        
        self.running = True
        
        rospy.loginfo("==========================================")
        rospy.loginfo("Keyboard Teleop for Wheeled Legged Robot")
        rospy.loginfo("==========================================")
        rospy.loginfo("W/S: 前进/后退")
        rospy.loginfo("A/D: 左/右转向")
        rospy.loginfo("Q/E: 原地左/右转")
        rospy.loginfo("空格: 跳跃")
        rospy.loginfo("X: 停止")
        rospy.loginfo("C: 平衡模式")
        rospy.loginfo("1-9: 速度等级")
        rospy.loginfo("==========================================")
        rospy.loginfo("按 Ctrl+C 退出")
        
        self.run()

    def run(self):
        """主循环"""
        rate = rospy.Rate(10)
        
        while not rospy.is_shutdown() and self.running:
            key = self.getKey()
            
            if key:
                self.processKey(key)
            
            rate.sleep()

    def getKey(self):
        """获取键盘按键 (非阻塞)"""
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
        except:
            key = ''
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, termios.tcgetattr(sys.stdin))
        
        return key

    def processKey(self, key):
        """处理按键"""
        twist = Twist()
        
        if key == self.KEY_W:
            twist.linear.x = self.speed
            rospy.loginfo("前进: speed=%.2f", self.speed)
        
        elif key == self.KEY_S:
            twist.linear.x = -self.speed
            rospy.loginfo("后退: speed=%.2f", self.speed)
        
        elif key == self.KEY_A:
            twist.angular.z = self.yaw_rate
            rospy.loginfo("左转: yaw_rate=%.2f", self.yaw_rate)
        
        elif key == self.KEY_D:
            twist.angular.z = -self.yaw_rate
            rospy.loginfo("右转: yaw_rate=%.2f", self.yaw_rate)
        
        elif key == self.KEY_Q:
            twist.angular.z = self.yaw_rate * 1.5
            rospy.loginfo("原地左转")
        
        elif key == self.KEY_E:
            twist.angular.z = -self.yaw_rate * 1.5
            rospy.loginfo("原地右转")
        
        elif key == self.KEY_SPACE:
            twist.linear.z = 0.5  # 跳跃标志
            rospy.loginfo("跳跃!")
        
        elif key == self.KEY_X:
            rospy.loginfo("停止")
        
        elif key == self.KEY_C:
            rospy.loginfo("进入平衡模式")
        
        elif key in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            self.speed = (int(key) / 9.0) * 2.0
            rospy.loginfo("速度等级: %s (speed=%.2f)", key, self.speed)
        
        elif key == '\x03':
            rospy.loginfo("退出")
            self.running = False
        
        self.pub.publish(twist)

if __name__ == '__main__':
    try:
        KeyboardTeleop()
    except rospy.ROSInterruptException:
        pass