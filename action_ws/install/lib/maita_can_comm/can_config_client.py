#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 配置 Action Client
========================================
使用方法:
  python3 scripts/can_config_client.py \
    _channel:=0 \
    _baudrate:=500000 \
    _enable_loopback:=false
"""

import rospy
import actionlib
from maita_can_comm.msg import CANConfigAction


class CANConfigClient:
    """CAN 配置 Action Client"""
    
    def __init__(self):
        rospy.init_node('can_config_client')
        
        self.channel = rospy.get_param('~channel', 0)
        self.baudrate = rospy.get_param('~baudrate', 500000)
        self.enable_loopback = rospy.get_param('~enable_loopback', False)
        self.enable_timestamp = rospy.get_param('~enable_timestamp', True)
        
        self.client = actionlib.SimpleActionClient('can_config', CANConfigAction)
        
        rospy.loginfo("等待 CAN 配置 Action Server...")
        self.client.wait_for_server()
        rospy.loginfo("✅ Action Server 已连接")
    
    def config_can(self):
        goal = CANConfigGoal()
        goal.channel = self.channel
        goal.baudrate = self.baudrate
        goal.enable_loopback = self.enable_loopback
        goal.enable_timestamp = self.enable_timestamp
        
        rospy.loginfo(f"📤 配置 CAN {self.channel}: {self.baudrate} bps")
        
        self.client.send_goal(goal)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        if result.success:
            rospy.loginfo(f"✅ {result.message}")
        else:
            rospy.logerr(f"❌ {result.message}")


if __name__ == '__main__':
    try:
        client = CANConfigClient()
        client.config_can()
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号')