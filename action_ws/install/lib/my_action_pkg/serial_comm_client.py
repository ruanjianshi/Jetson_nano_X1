#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
串口通信 Action Client
========================================
功能说明:
  - 作为 ROS Action 客户端，向服务器发送串口通信请求
  - 接收服务器的反馈信息（Feedback）
  - 接收服务器的最终结果（Result）
  - 显示发送和接收的数据对比
  
使用方法:
  source install/setup.bash
  rosrun my_action_pkg serial_comm_client.py _data:="Hello"
  rosrun my_action_pkg serial_comm_client.py _data:="Test Message"
  
作者: Jetson Nano
日期: 2026-03-30
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from my_action_pkg.msg import SerialCommAction, SerialCommGoal  # 自定义 Action 消息类型
from std_msgs.msg import String   # ROS 标准字符串消息类型


# ==================== SerialCommClient 类定义 ====================
class SerialCommClient:
    """
    串口通信 Action Client 类
    
    职责:
      1. 创建 Action Client 并连接到服务器
      2. 发送 Goal（要发送的数据）到服务器
      3. 接收并处理服务器的 Feedback（反馈信息）
      4. 等待并处理服务器的 Result（最终结果）
    """
    
    def __init__(self, data):
        """
        构造函数 - 初始化客户端
        
        参数:
          data: 要通过串口发送的字符串数据
        
        执行流程:
          1. 创建 Action Client
          2. 等待服务器上线
          3. 创建并发送 Goal
          4. 等待服务器返回结果
          5. 显示结果信息
        """

        # ==================== 1. 创建 Action Client ====================
        # SimpleActionClient 是 ROS 提供的简化 Action Client 实现
        # 参数说明:
        #   - 'serial_comm': Action 名称，必须与服务器端的 Action 名称一致
        #   - SerialCommAction: Action 类型（由 .action 文件生成）
        self.client = actionlib.SimpleActionClient('serial_comm', SerialCommAction)
        
        # ==================== 2. 等待服务器上线 ====================
        # wait_for_server() 阻塞等待服务器启动
        # 如果服务器未启动，此函数会一直等待
        rospy.loginfo('⏳ 等待 Action Server 上线...')
        self.client.wait_for_server()
        rospy.loginfo('✅ Action Server 已连接')
        
        # ==================== 3. 创建并发送 Goal ====================
        # 创建 Goal 对象
        goal = SerialCommGoal()
        
        # 设置 Goal 的数据
        # goal.data 是 String 类型
        # goal.data.data 是实际的字符串数据
        goal.data = String(data=data)
        
        # 发送 Goal
        # send_goal() 参数说明:
        #   - goal: 要发送的目标
        #   - feedback_cb: 反馈回调函数，当服务器发送 feedback 时调用
        rospy.loginfo(f"📤 发送 Goal: '{data}'")
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        # ==================== 4. 等待服务器返回结果 ====================
        # wait_for_result() 等待服务器返回结果
        # Duration(5.0) 设置最大等待时间为 5 秒
        rospy.loginfo('⏳ 等待服务器返回结果...')
        
        if self.client.wait_for_result(rospy.Duration(5.0)):
            # ==================== 6. 处理并显示结果 ====================
            # get_result() 获取服务器返回的结果
            result = self.client.get_result()
            
            # 检查操作是否成功
            if result.success:
                rospy.loginfo("=" * 50)
                rospy.loginfo("✅ 串口通信成功！")
                rospy.loginfo(f"   发送数据: '{data}'")
                rospy.loginfo(f"   接收数据: '{result.received_data.data}'")
                rospy.loginfo("=" * 50)
            else:
                rospy.logwarn("=" * 50)
                rospy.logwarn("❌ 串口通信失败！")
                rospy.logwarn(f"   发送数据: '{data}'")
                rospy.logwarn(f"   接收数据: '{result.received_data.data}'")
                rospy.logwarn("   可能原因: 串口回环未正确连接")
                rospy.logwarn("=" * 50)
        else:
            # 超时未收到结果
            rospy.logerr("❌ 等待结果超时（5秒）")
    
    # ==================== 反馈回调函数 ====================
    def feedback_cb(self, feedback):
        """
        反馈回调函数
        
        当服务器发送 feedback 时，Action Client 会自动调用此函数
        
        参数:
          feedback: 服务器发送的反馈信息
                    feedback.partial_data.data 是反馈的数据
        
        说明:
          Feedback 用于服务器向客户端报告任务执行进度
          在串口通信场景中，Feedback 告知客户端正在发送的数据
        """
        rospy.loginfo(f"📢 Feedback: '{feedback.partial_data.data}'")


# ==================== 主函数 ====================
if __name__ == '__main__':
    """
    主函数 - 程序入口
    
    功能:
      1. 初始化 ROS 节点
      2. 从命令行参数或参数服务器读取要发送的数据
      3. 创建 SerialCommClient 实例
      4. 处理异常并优雅退出
      
    参数说明:
      _data: 命令行参数，指定要发送的数据
             例如: rosrun my_action_pkg serial_comm_client.py _data:="Hello"
             rosparam set /serial_comm_client/data "xiaoqi"
    """
    try:
        # ==================== 1. 初始化 ROS 节点 ====================
        # init_node() 创建一个 ROS 节点
        # 必须在参数读取之前初始化节点
        rospy.init_node('serial_comm_client')
        rospy.loginfo("正在初始化串口通信 Action Client...")
        
        # ==================== 2. 从参数服务器读取要发送的数据 ====================
        # rospy.get_param('~data', default_value)
        # '~' 表示私有命名空间，可以通过命令行参数 _data 设置
        # 例如: rosrun my_action_pkg serial_comm_client.py _data:="modbus"
        data = rospy.get_param('~data', 'Hello Serial')
        
        rospy.loginfo(f"========================================")
        rospy.loginfo(f"串口通信 Action Client")
        rospy.loginfo(f"发送数据: '{data}'")
        rospy.loginfo(f"========================================")
        
        # ==================== 3. 创建客户端实例 ====================
        # 构造函数中会执行完整的通信流程
        client = SerialCommClient(data)
        
    except rospy.ROSInterruptException:
        # 捕获 ROS 中断异常（Ctrl+C）
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        # 捕获其他异常
        rospy.logerr(f'❌ 客户端运行错误: {e}')