#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=======================================
MP2515 SPI转CAN 客户端
=======================================
功能说明:
  - 向 MP2515 CAN Action Server 发送 CAN 帧
  - 支持标准帧和扩展帧
  - 支持数据帧和远程帧
  
使用方法:
  source devel/setup.bash
  rosrun mcp2515_can_driver mp2515_can_client.py
  
作者: Jetson Nano
日期: 2026-04-08
"""

import rospy
import actionlib
from mcp2515_can_driver.msg import MCP2515CANCommAction, MCP2515CANCommGoal, MCP2515CANCommResult


class MP2515CANClient:
    """MP2515 CAN 通信客户端"""
    
    def __init__(self):
        self.server_name = 'mp2515_can_comm'
        rospy.loginfo(f"正在连接到 {self.server_name}...")
        
        self.client = actionlib.SimpleActionClient(self.server_name, MCP2515CANCommAction)
        self.client.wait_for_server()
        
        rospy.loginfo(f"✅ 已连接到 {self.server_name}")
    
    def send_can_frame(self, can_id, data, dlc, extended=False, remote=False, timeout=5.0):
        """
        发送 CAN 帧
        
        参数:
          can_id: CAN ID (11-bit 标准 或 29-bit 扩展)
          data: CAN 数据 (列表)
          dlc: 数据长度 (0-8)
          extended: 是否为扩展帧
          remote: 是否为远程帧
          timeout: 超时时间(秒)
        
        返回:
          success: 是否成功
          message: 状态消息
          result: 完整结果对象
        """
        goal = MCP2515CANCommGoal()
        goal.can_id = can_id
        goal.dlc = dlc
        goal.data = data
        goal.extended = extended
        goal.remote = remote
        
        id_type = "EXT" if extended else "STD"
        frame_type = "RTR" if remote else "DATA"
        rospy.loginfo(f"📤 发送 CAN 帧: {id_type} ID=0x{can_id:X} {frame_type} DLC={dlc}")
        
        self.client.send_goal(goal)
        
        self.client.wait_for_result(rospy.Duration(timeout))
        result = self.client.get_result()
        
        if result:
            rospy.loginfo(f"✅ 结果: success={result.success}, message={result.message}")
        else:
            rospy.logerr("❌ 未收到结果 (超时)")
        
        return result.success if result else False, result.message if result else "超时", result
    
    def feedback_cb(self, feedback):
        """反馈回调"""
        rospy.loginfo(f"📋 反馈: {feedback.status}")


def main():
    rospy.init_node('mp2515_can_client')
    
    client = MP2515CANClient()
    
    rospy.loginfo("发送测试 CAN 帧...")
    
    success, msg, result = client.send_can_frame(
        can_id=0x123,
        data=[0x11, 0x22, 0x33, 0x44, 0, 0, 0, 0],
        dlc=4,
        extended=False,
        remote=False
    )
    
    if success:
        rospy.loginfo("✅ 测试帧发送成功")
    else:
        rospy.logerr(f"❌ 测试帧发送失败: {msg}")
    
    rospy.loginfo("客户端测试完成")


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 收到中断信号")
    except Exception as e:
        rospy.logerr(f"❌ 客户端错误: {e}")
