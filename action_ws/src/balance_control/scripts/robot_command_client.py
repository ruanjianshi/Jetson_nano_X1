#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
Balance Control Command Client
========================================

功能说明:
  - 提供高层运动命令接口 (前进、后退、转向、跳跃等)
  - 将高层命令转换为底层平衡控制目标
  - 支持持续发送和一次性命令

命令类型:
  - STOP (0): 停止移动
  - FORWARD (1): 前进
  - BACKWARD (2): 后退
  - TURN_LEFT (3): 左转
  - TURN_RIGHT (4): 右转
  - STRAFE_LEFT (5): 左侧向移动
  - STRAFE_RIGHT (6): 右侧向移动
  - JUMP (7): 跳跃
  - BALANCE (8): 进入平衡模式

使用示例:
  rosrun balance_control robot_command_client.py _command:=1 _speed:=0.5
  rosrun balance_control robot_command_client.py _command:=3 _yaw_rate:=1.0

Author: Qi Xiao
Email: 2408128687@qq.com
日期: 2026-05-06
"""

import rospy
import actionlib
from balance_control.msg import RobotCommand
from balance_control.msg import BalanceControlAction, BalanceControlGoal
from geometry_msgs.msg import Twist

class RobotCommandClient:
    """
    机器人命令客户端类
    
    功能:
      - 订阅 /cmd_vel 话题获取运动命令
      - 将运动命令转换为平衡控制目标
      - 通过 Action 接口发送控制目标
    
    坐标系 (B frame):
      - X轴: 指向机器人右侧
      - Y轴: 指向机器人后方 (前进方向为-Y)
      - Z轴: 指向上方
    """

    def __init__(self):
        """初始化ROS节点和Action Client"""
        
        # ========== ROS初始化 ==========
        rospy.init_node('robot_command_client', anonymous=True)
        rospy.loginfo("==========================================")
        rospy.loginfo("Robot Command Client 已启动")
        rospy.loginfo("==========================================")
        
        # ========== 参数获取 ==========
        self.command = rospy.get_param('~command', 0)      # 默认停止
        self.speed = rospy.get_param('~speed', 0.0)        # 默认速度 0
        self.yaw_rate = rospy.get_param('~yaw_rate', 0.0)  # 默认转向 0
        self.jump_height = rospy.get_param('~jump_height', 0.0)
        self.duration = rospy.get_param('~duration', 0.0)
        
        # 持续发送模式 (用于cmd_vel)
        self.continuous_mode = rospy.get_param('~continuous', False)
        
        # ========== 关节映射 ==========
        # 左腿关节顺序: HIP_ROLL, HIP_PITCH, KNEE_PITCH, WHEEL
        # 右腿关节顺序: HIP_ROLL, HIP_PITCH, KNEE_PITCH, WHEEL
        self.joint_names = [
            'joint_left_leg_1', 'joint_left_leg_2', 'joint_left_leg_3', 'joint_left_leg_4',
            'joint_right_leg_1', 'joint_right_leg_2', 'joint_right_leg_3', 'joint_right_leg_4'
        ]
        
        # ========== 创建Action Client ==========
        self.action_client = actionlib.SimpleActionClient('balance_control', BalanceControlAction)
        rospy.loginfo("等待 Balance Control Action Server...")
        
        if not self.action_client.wait_for_server(rospy.Duration(10.0)):
            rospy.logerr("无法连接到 Action Server!")
            return
        
        rospy.loginfo("已连接到 Action Server")
        
        # ========== 订阅cmd_vel话题 ==========
        if self.continuous_mode:
            self.cmd_vel_sub = rospy.Subscriber('/cmd_vel', Twist, self.cmdVelCallback)
            rospy.loginfo("订阅 /cmd_vel 话题 (持续模式)")
        
        # ========== 发送初始命令 ==========
        self.sendCommand(self.command, self.speed, self.yaw_rate, self.jump_height, self.duration)
        
        # ========== 如果不是持续模式，则完成后退出 ==========
        if not self.continuous_mode:
            rospy.loginfo("命令已发送，客户端将退出")
            return
        
        # ========== 持续模式主循环 ==========
        rospy.loginfo("进入持续控制模式...")
        rate = rospy.Rate(10)  # 10Hz
        
        while not rospy.is_shutdown():
            rate.sleep()
            
            if rospy.is_shutdown():
                break
        
        # 退出前发送停止命令
        self.sendStop()
        rospy.loginfo("客户端退出")

    def cmdVelCallback(self, msg):
        """
        cmd_vel 回调函数
        
        将 Twist 消息转换为平衡控制命令:
          - linear.x -> 前进/后退 (Y方向)
          - linear.y -> 侧向移动 (X方向)
          - angular.z -> 转向 (Yaw)
        """
        # 从 cmd_vel 提取速度
        forward_speed = -msg.linear.x  # 转换为机器人坐标系
        lateral_speed = msg.linear.y
        yaw_rate = msg.angular.z
        
        # 判断命令类型
        command = RobotCommand.CMD_FORWARD  # 默认前进
        
        # 根据速度判断命令
        if abs(forward_speed) > 0.01:
            if forward_speed > 0:
                command = RobotCommand.CMD_FORWARD
            else:
                command = RobotCommand.CMD_BACKWARD
        elif abs(lateral_speed) > 0.01:
            if lateral_speed > 0:
                command = RobotCommand.CMD_STRAFE_RIGHT
            else:
                command = RobotCommand.CMD_STRAFE_LEFT
        elif abs(yaw_rate) > 0.01:
            if yaw_rate > 0:
                command = RobotCommand.CMD_TURN_LEFT
            else:
                command = RobotCommand.CMD_TURN_RIGHT
        else:
            command = RobotCommand.CMD_STOP
        
        speed = max(abs(forward_speed), abs(lateral_speed))
        self.sendCommand(command, speed, yaw_rate, 0.0, 0.0)

    def computeTargetOrientation(self, command, speed, yaw_rate):
        """
        根据命令计算目标姿态
        
        说明:
          - 前进/后退时，身体微微前倾/后仰
          - 转向时，身体微微侧倾
          - 保持平衡
        
        参数:
          command: 命令类型
          speed: 速度 m/s
          yaw_rate: 转向角速度 rad/s
        
        返回:
          (target_roll, target_pitch, target_yaw)
        """
        # 默认目标 (保持平衡)
        target_roll = 0.0
        target_pitch = 0.0
        target_yaw = 0.0
        
        if command == RobotCommand.CMD_FORWARD:
            # 前进: 身体微微前倾，角度与速度成正比
            target_pitch = -speed * 0.15  # 最大约 -0.3 rad (约17度)
        
        elif command == RobotCommand.CMD_BACKWARD:
            # 后退: 身体微微后仰
            target_pitch = speed * 0.15
        
        elif command == RobotCommand.CMD_TURN_LEFT:
            # 左转: 身体微微右倾，帮助转向
            target_roll = yaw_rate * 0.1
            target_yaw = yaw_rate * 0.5  # 直接控制偏航
        
        elif command == RobotCommand.CMD_TURN_RIGHT:
            # 右转: 身体微微左倾
            target_roll = -yaw_rate * 0.1
            target_yaw = -yaw_rate * 0.5
        
        elif command == RobotCommand.CMD_STRAFE_LEFT:
            # 左侧向: 身体微微右倾
            target_roll = 0.1
        
        elif command == RobotCommand.CMD_STRAFE_RIGHT:
            # 右侧向: 身体微微左倾
            target_roll = -0.1
        
        elif command == RobotCommand.CMD_STOP:
            # 停止: 回到中立姿态
            target_roll = 0.0
            target_pitch = 0.0
            target_yaw = 0.0
        
        elif command == RobotCommand.CMD_JUMP:
            # 跳跃: 身体微微下蹲准备
            target_pitch = -0.2
        
        elif command == RobotCommand.CMD_BALANCE:
            # 平衡模式: 保持当前姿态
            pass
        
        return target_roll, target_pitch, target_yaw

    def sendCommand(self, command, speed, yaw_rate, jump_height, duration):
        """
        发送命令到平衡控制器
        
        参数:
          command: 命令类型 (0-8)
          speed: 速度 m/s
          yaw_rate: 转向角速度 rad/s
          jump_height: 跳跃高度 m
          duration: 持续时间 s
        """
        # 计算目标姿态
        target_roll, target_pitch, target_yaw = self.computeTargetOrientation(command, speed, yaw_rate)
        
        # 创建 Action Goal
        goal = BalanceControlGoal()
        goal.command = 4  # CMD_SET_TARGET
        goal.algorithm = 0  # 0=LQR, 1=VMC, 2=MPC
        goal.target_roll = target_roll
        goal.target_pitch = target_pitch
        goal.target_yaw = target_yaw
        
        # 发送目标
        self.action_client.send_goal(goal)
        
        # 打印命令信息
        cmd_name = self.getCommandName(command)
        rospy.loginfo("==========================================")
        rospy.loginfo("发送命令: %s", cmd_name)
        rospy.loginfo("  速度: %.2f m/s", speed)
        rospy.loginfo("  转向: %.2f rad/s", yaw_rate)
        rospy.loginfo("  目标姿态: roll=%.3f, pitch=%.3f, yaw=%.3f", 
                      target_roll, target_pitch, target_yaw)
        rospy.loginfo("==========================================")
        
        # 如果不是持续命令，等待结果
        if duration > 0:
            rospy.sleep(duration)
            self.sendStop()

    def sendStop(self):
        """发送停止命令"""
        goal = BalanceControlGoal()
        goal.command = 2  # CMD_DISABLE
        self.action_client.send_goal(goal)
        rospy.loginfo("发送停止命令")

    def getCommandName(self, command):
        """获取命令名称"""
        names = {
            0: "STOP",
            1: "FORWARD",
            2: "BACKWARD",
            3: "TURN_LEFT",
            4: "TURN_RIGHT",
            5: "STRAFE_LEFT",
            6: "STRAFE_RIGHT",
            7: "JUMP",
            8: "BALANCE"
        }
        return names.get(command, "UNKNOWN")


if __name__ == '__main__':
    try:
        RobotCommandClient()
    except rospy.ROSInterruptException:
        pass