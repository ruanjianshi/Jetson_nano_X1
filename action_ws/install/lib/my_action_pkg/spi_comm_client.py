#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
SPI 通信 Action Client
========================================
功能说明:
  - 作为 ROS Action 客户端，向服务器发送 SPI 通信请求
  - 接收服务器的反馈信息（Feedback）
  - 接收服务器的最终结果（Result）
  - 显示写入和读取的数据对比
  
使用方法:
  source install/setup.bash
  python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/spi_comm_client.py \
      _spi_bus:=0 \
      _device_address:=0 \
      _write_data:=0xAA \
      _read_after_write:=true
  
作者: Jetson Nano
日期: 2026-03-31
"""

import rospy
import actionlib
from my_action_pkg.msg import SPICommAction, SPICommGoal
from std_msgs.msg import String


class SPICommClient:
    """
    SPI 通信 Action Client 类
    
    职责:
      1. 创建 Action Client 并连接到服务器
      2. 发送 Goal（SPI 通信参数）到服务器
      3. 接收并处理服务器的 Feedback（反馈信息）
      4. 等待并处理服务器的 Result（最终结果）
    """
    
    def __init__(self, spi_bus, device_address, write_data, read_after_write):
        """
        构造函数 - 初始化客户端
        
        参数:
          spi_bus: SPI 总线编号
          device_address: 设备地址/片选编号
          write_data: 要写入的数据
          read_after_write: 写入后是否读取
        """
        self.client = actionlib.SimpleActionClient('spi_comm', SPICommAction)
        
        rospy.loginfo('⏳ 等待 Action Server 上线...')
        self.client.wait_for_server()
        rospy.loginfo('✅ Action Server 已连接')
        
        goal = SPICommGoal()
        goal.spi_bus = spi_bus
        goal.device_address = device_address
        goal.write_data = write_data
        goal.read_after_write = read_after_write
        
        rospy.loginfo(f"📤 发送 Goal:")
        rospy.loginfo(f"   SPI 总线: {spi_bus}")
        rospy.loginfo(f"   设备地址: {device_address}")
        rospy.loginfo(f"   写入数据: 0x{write_data:02X} ({write_data})")
        rospy.loginfo(f"   写后读取: {read_after_write}")
        
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        rospy.loginfo('⏳ 等待服务器返回结果...')
        
        if self.client.wait_for_result(rospy.Duration(5.0)):
            result = self.client.get_result()
            
            if result.success:
                rospy.loginfo("=" * 50)
                rospy.loginfo("✅ SPI 通信成功！")
                rospy.loginfo(f"   写入数据: 0x{write_data:02X} ({write_data})")
                if read_after_write:
                    rospy.loginfo(f"   读取数据: 0x{result.received_data:02X} ({result.received_data})")
                rospy.loginfo("=" * 50)
            else:
                rospy.logwarn("=" * 50)
                rospy.logwarn("❌ SPI 通信失败！")
                rospy.logwarn("=" * 50)
        else:
            rospy.logerr("❌ 等待结果超时（5秒）")
    
    def feedback_cb(self, feedback):
        """
        反馈回调函数
        
        参数:
          feedback: 服务器发送的反馈信息
        """
        rospy.loginfo(f"📢 Feedback: {feedback.status.data} (数据: 0x{feedback.current_data:02X})")


if __name__ == '__main__':
    try:
        rospy.init_node('spi_comm_client')
        rospy.loginfo("正在初始化 SPI 通信 Action Client...")
        
        spi_bus = rospy.get_param('~spi_bus', 0)
        device_address = rospy.get_param('~device_address', 0)
        write_data = rospy.get_param('~write_data', 0xAA)
        read_after_write = rospy.get_param('~read_after_write', True)
        
        rospy.loginfo(f"========================================")
        rospy.loginfo(f"SPI 通信 Action Client")
        rospy.loginfo(f"========================================")
        
        client = SPICommClient(spi_bus, device_address, write_data, read_after_write)
        
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        rospy.logerr(f'❌ 客户端运行错误: {e}')