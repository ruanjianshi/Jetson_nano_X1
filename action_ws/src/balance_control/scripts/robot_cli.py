#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
Robot Command Line Interface (CLI)
========================================

功能说明:
  - 命令行方式发送控制命令
  - 支持前进、后退、转向、跳跃等命令
  - 实时显示机器人状态

使用示例:
  # 前进 0.5m/s
  rosrun balance_control robot_cli.py move forward 0.5
  
  # 左转 1.0 rad/s
  rosrun balance_control robot_cli.py turn left 1.0
  
  # 跳跃 0.3m
  rosrun balance_control robot_cli.py jump 0.3
  
  # 停止
  rosrun balance_control robot_cli.py stop

命令格式:
  rosrun balance_control robot_cli.py <command> [args]
  
Commands:
  move forward <speed>     前进 (speed: 0.0 ~ 2.0 m/s)
  move backward <speed>    后退
  turn left <rate>          左转 (rate: rad/s)
  turn right <rate>        右转
  strafe left <speed>      左侧向移动
  strafe right <speed>     右侧向移动
  stop                     停止
  jump <height>             跳跃 (height: 0.0 ~ 0.5 m)
  balance                   进入平衡模式
  status                    查询状态

作者: Jetson Nano
日期: 2026-05-06
"""

import rospy
import actionlib
from balance_control.msg import BalanceControlAction, BalanceControlGoal

class RobotCLI:
    """
    机器人命令行接口
    
    功能:
      - 解析命令行参数
      - 发送控制命令到 Action Server
      - 显示执行结果
    """

    def __init__(self):
        rospy.init_node('robot_cli', anonymous=False)
        
        self.action_client = actionlib.SimpleActionClient('balance_control', BalanceControlAction)
        rospy.loginfo("等待 Balance Control Action Server...")
        
        if not self.action_client.wait_for_server(rospy.Duration(10.0)):
            rospy.logerr("无法连接到 Action Server!")
            return
        
        rospy.loginfo("已连接")
        
        self.last_cmd = None

    def send_stop(self):
        """发送停止命令"""
        goal = BalanceControlGoal()
        goal.command = 2  # CMD_DISABLE
        self.action_client.send_goal(goal)
        self.last_cmd = "stop"

    def send_target(self, roll=0.0, pitch=0.0, yaw=0.0):
        """发送目标姿态"""
        goal = BalanceControlGoal()
        goal.command = 4  # CMD_SET_TARGET
        goal.target_roll = roll
        goal.target_pitch = pitch
        goal.target_yaw = yaw
        self.action_client.send_goal(goal)
        rospy.loginfo("目标姿态: roll=%.3f, pitch=%.3f, yaw=%.3f", roll, pitch, yaw)
        self.last_cmd = f"target({roll:.2f},{pitch:.2f},{yaw:.2f})"

    def send_enable(self):
        """发送启用命令"""
        goal = BalanceControlGoal()
        goal.command = 1  # CMD_ENABLE
        self.action_client.send_goal(goal)
        self.last_cmd = "enable"

    def run_command(self, command, *args):
        """
        执行命令
        
        参数:
          command: 命令类型
          args: 命令参数
        """
        rospy.loginfo("执行命令: %s %s", command, args)
        
        if command == "move":
            if len(args) < 2:
                rospy.logerr("用法: move <forward|backward> <speed>")
                return
            
            direction = args[0]
            speed = float(args[1]) if len(args) > 1 else 0.5
            
            if direction == "forward":
                self.send_target(pitch=-speed * 0.15)
            elif direction == "backward":
                self.send_target(pitch=speed * 0.15)
            else:
                rospy.logerr("未知方向: %s", direction)
                return
        
        elif command == "turn":
            if len(args) < 2:
                rospy.logerr("用法: turn <left|right> <rate>")
                return
            
            direction = args[0]
            rate = float(args[1]) if len(args) > 1 else 1.0
            
            if direction == "left":
                self.send_target(roll=rate * 0.1, yaw=rate * 0.5)
            elif direction == "right":
                self.send_target(roll=-rate * 0.1, yaw=-rate * 0.5)
            else:
                rospy.logerr("未知方向: %s", direction)
                return
        
        elif command == "strafe":
            if len(args) < 2:
                rospy.logerr("用法: strafe <left|right> <speed>")
                return
            
            direction = args[0]
            speed = float(args[1]) if len(args) > 1 else 0.5
            
            if direction == "left":
                self.send_target(roll=0.1)
            elif direction == "right":
                self.send_target(roll=-0.1)
            else:
                rospy.logerr("未知方向: %s", direction)
                return
        
        elif command == "stop":
            self.send_stop()
        
        elif command == "jump":
            height = float(args[0]) if len(args) > 0 else 0.3
            self.send_target(pitch=-0.2)
            rospy.loginfo("跳跃高度: %.2f m", height)
        
        elif command == "balance":
            self.send_enable()
            self.send_target(0.0, 0.0, 0.0)
        
        elif command == "status":
            rospy.loginfo("最后命令: %s", self.last_cmd)
        
        else:
            rospy.logerr("未知命令: %s", command)
            rospy.loginfo("可用命令: move, turn, strafe, stop, jump, balance, status")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cli = RobotCLI()
    
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    try:
        cli.run_command(command, *args)
    except Exception as e:
        rospy.logerr("执行失败: %s", str(e))

if __name__ == '__main__':
    import sys
    main()