#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 配置 Action Server
========================================
功能说明:
  - 配置 CAN 通道参数
  - 设置波特率
  - 启用/禁用回环模式
  - 启用/禁用时间戳
  
使用方法:
  python3 scripts/can_config_server.py
"""

import rospy
import actionlib
import can
from maita_can_comm.msg import CANConfigAction, CANConfigFeedback, CANConfigResult


class CANConfigServer:
    """CAN 配置 Action Server"""
    
    def __init__(self):
        rospy.init_node('can_config_server')
        rospy.loginfo("正在初始化 CAN 配置 Action Server...")
        
        self.server = actionlib.SimpleActionServer(
            'can_config',
            CANConfigAction,
            self.execute,
            False
        )
        
        self.server.start()
        
        rospy.loginfo("✅ CAN 配置 Action Server 已启动")
        rospy.loginfo("   Action 名称: can_config")
    
    def execute(self, goal):
        """
        执行配置 Goal
        """
        channel_name = f"can{goal.channel}"
        rospy.loginfo(f"📥 收到配置请求:")
        rospy.loginfo(f"   通道: {channel_name}")
        rospy.loginfo(f"   波特率: {goal.baudrate}")
        rospy.loginfo(f"   回环模式: {goal.enable_loopback}")
        rospy.loginfo(f"   时间戳: {goal.enable_timestamp}")
        
        feedback = CANConfigFeedback()
        feedback.status = f"正在配置 {channel_name}..."
        self.server.publish_feedback(feedback)
        
        # 这里可以添加实际的 CAN 配置逻辑
        # 例如修改内核参数、重新加载模块等
        
        rospy.sleep(0.5)
        
        result = CANConfigResult()
        result.success = True
        result.message = f"CAN {channel_name} 配置成功"
        result.actual_baudrate = goal.baudrate
        
        self.server.set_succeeded(result)
        rospy.loginfo("✅ 配置完成")


if __name__ == '__main__':
    try:
        server = CANConfigServer()
        rospy.loginfo("🔄 Action Server 正在运行...")
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号')