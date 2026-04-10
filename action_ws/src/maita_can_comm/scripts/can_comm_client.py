#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 通信 Action Client
========================================
功能说明:
  - 向 CAN 通信 Action Server 发送 CAN 帧
  - 支持标准帧和扩展帧
  - 支持可变数据长度
  
使用方法:
  python3 scripts/can_comm_client.py \
    _can_id:=0x123 \
    _data:="[0x01, 0x02, 0x03]" \
    _dlc:=3 \
    _extended:=false \
    _channel:=0
  
作者: Jetson Nano
日期: 2026-04-02
"""

import rospy
import actionlib
from maita_can_comm.msg import CANCommGoal, CANCommAction


class CANCommClient:
    """
    CAN 通信 Action Client 类
    """
    
    def __init__(self):
        """
        构造函数 - 初始化客户端
        """
        rospy.init_node('can_comm_client')
        
        # 从参数服务器读取配置
        self.can_id = rospy.get_param('~can_id', 0x123)
        self.data = rospy.get_param('~data', [0x01, 0x02, 0x03])
        self.dlc = rospy.get_param('~dlc', 3)
        self.extended = rospy.get_param('~extended', False)
        self.channel = rospy.get_param('~channel', 0)
        
        # 创建 Action Client
        self.client = actionlib.SimpleActionClient('can_comm', CANCommAction)
        
        rospy.loginfo("等待 CAN 通信 Action Server...")
        self.client.wait_for_server()
        
        rospy.loginfo("✅ Action Server 已连接")
    
    def send_can_frame(self):
        """
        发送 CAN 帧
        """
        # 创建 Goal
        goal = CANCommGoal()
        goal.can_id = self.can_id
        goal.data = self.data
        goal.dlc = self.dlc
        goal.extended = self.extended
        goal.channel = self.channel
        
        rospy.loginfo(f"📤 发送 CAN 帧:")
        rospy.loginfo(f"   CAN ID: {hex(self.can_id)}")
        rospy.loginfo(f"   数据长度: {self.dlc}")
        rospy.loginfo(f"   数据: {[hex(b) for b in self.data]}")
        rospy.loginfo(f"   扩展帧: {self.extended}")
        rospy.loginfo(f"   通道: {self.channel}")
        
        # 发送 Goal
        self.client.send_goal(goal)
        
        # 等待结果
        self.client.wait_for_result()
        
        # 获取结果
        result = self.client.get_result()
        
        if result.success:
            rospy.loginfo(f"✅ {result.message}")
        else:
            rospy.logerr(f"❌ {result.message}")


if __name__ == '__main__':
    try:
        client = CANCommClient()
        client.send_can_frame()
        
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号')