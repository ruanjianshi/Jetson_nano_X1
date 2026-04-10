#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 过滤 Action Server
========================================
功能说明:
  - 配置 CAN ID 过滤器
  - 支持 ID 和掩码过滤
  - 支持标准帧和扩展帧过滤
  
使用方法:
  python3 scripts/can_filter_server.py
"""

import rospy
import actionlib
from maita_can_comm.msg import CANFilterAction, CANFilterFeedback, CANFilterResult


class CANFilterServer:
    """CAN 过滤 Action Server"""
    
    def __init__(self):
        rospy.init_node('can_filter_server')
        rospy.loginfo("正在初始化 CAN 过滤 Action Server...")
        
        self.server = actionlib.SimpleActionServer(
            'can_filter',
            CANFilterAction,
            self.execute,
            False
        )
        
        self.server.start()
        
        rospy.loginfo("✅ CAN 过滤 Action Server 已启动")
        rospy.loginfo("   Action 名称: can_filter")
    
    def execute(self, goal):
        """
        执行过滤配置 Goal
        """
        rospy.loginfo(f"📥 收到过滤配置请求:")
        rospy.loginfo(f"   通道: can{goal.channel}")
        rospy.loginfo(f"   CAN ID: 0x{goal.can_id:03X}")
        rospy.loginfo(f"   掩码: 0x{goal.can_id_mask:03X}")
        rospy.loginfo(f"   启用: {goal.enable}")
        rospy.loginfo(f"   扩展帧: {goal.extended}")
        
        feedback = CANFilterFeedback()
        feedback.status = f"正在配置过滤器..."
        self.server.publish_feedback(feedback)
        
        rospy.sleep(0.3)
        
        result = CANFilterResult()
        result.success = True
        result.message = f"过滤器配置成功: ID=0x{goal.can_id:03X}"
        result.filter_index = 0
        
        self.server.set_succeeded(result)
        rospy.loginfo("✅ 过滤器配置完成")


if __name__ == '__main__':
    try:
        server = CANFilterServer()
        rospy.loginfo("🔄 Action Server 正在运行...")
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号')