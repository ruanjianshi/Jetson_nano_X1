#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 过滤 Action Client
========================================
使用方法:
  python3 scripts/can_filter_client.py \
    _channel:=0 \
    _can_id:=0x123 \
    _can_id_mask:=0x7FF \
    _enable:=true
"""

import rospy
import actionlib
from maita_can_comm.msg import CANFilterAction


class CANFilterClient:
    """CAN 过滤 Action Client"""
    
    def __init__(self):
        rospy.init_node('can_filter_client')
        
        self.channel = rospy.get_param('~channel', 0)
        self.can_id = rospy.get_param('~can_id', 0x123)
        self.can_id_mask = rospy.get_param('~can_id_mask', 0x7FF)
        self.enable = rospy.get_param('~enable', True)
        self.extended = rospy.get_param('~extended', False)
        
        self.client = actionlib.SimpleActionClient('can_filter', CANFilterAction)
        
        rospy.loginfo("等待 CAN 过滤 Action Server...")
        self.client.wait_for_server()
        rospy.loginfo("✅ Action Server 已连接")
    
    def config_filter(self):
        goal = CANFilterGoal()
        goal.channel = self.channel
        goal.can_id = self.can_id
        goal.can_id_mask = self.can_id_mask
        goal.enable = self.enable
        goal.extended = self.extended
        
        rospy.loginfo(f"📤 配置过滤器: ID=0x{self.can_id:03X}")
        
        self.client.send_goal(goal)
        self.client.wait_for_result()
        
        result = self.client.get_result()
        if result.success:
            rospy.loginfo(f"✅ {result.message}")
        else:
            rospy.logerr(f"❌ {result.message}")


if __name__ == '__main__':
    try:
        client = CANFilterClient()
        client.config_filter()
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号')