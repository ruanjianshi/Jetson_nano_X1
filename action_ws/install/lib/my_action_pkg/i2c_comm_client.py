#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
I2C 通信 Action Client
========================================
功能说明:
  - 作为 ROS Action 客户端，向服务器发送 I2C 通信请求
  - 接收服务器的反馈信息（Feedback）
  - 接收服务器的最终结果（Result）
  - 显示 I2C 通信的结果和读取的数据
  
使用方法:
  source install/setup.bash
  python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/i2c_comm_client.py \
      _device_address:=0x50 \
      _register_address:=0x00 \
      _data:=0xAA
  
作者: Jetson Nano
日期: 2026-03-30
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from my_action_pkg.msg import I2CCommAction, I2CCommGoal  # 自定义 Action 消息类型
from std_msgs.msg import String   # ROS 标准字符串消息类型


# ==================== I2CCommClient 类定义 ====================
class I2CCommClient:
    """
    I2C 通信 Action Client 类
    
    职责:
      1. 创建 Action Client 并连接到服务器
      2. 发送 Goal（I2C 通信参数）到服务器
      3. 接收并处理服务器的 Feedback（反馈信息）
      4. 等待并处理服务器的 Result（最终结果）
    """
    
    def __init__(self, device_addr, register_addr, data):
        """
        构造函数 - 初始化客户端
        
        参数:
          device_addr: I2C 设备地址 (0x00-0x7F)
          register_addr: 寄存器地址 (0x00-0xFF)
          data: 要写入的数据 (0x00-0xFF)
        
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
        #   - 'i2c_comm': Action 名称，必须与服务器端的 Action 名称一致
        #   - I2CCommAction: Action 类型（由 .action 文件生成）
        self.client = actionlib.SimpleActionClient('i2c_comm', I2CCommAction)
        
        # ==================== 2. 等待服务器上线 ====================
        # wait_for_server() 阻塞等待服务器启动
        # 如果服务器未启动，此函数会一直等待
        rospy.loginfo('⏳ 等待 Action Server 上线...')
        self.client.wait_for_server()
        rospy.loginfo('✅ Action Server 已连接')
        
        # ==================== 3. 创建并发送 Goal ====================
        # 创建 Goal 对象
        goal = I2CCommGoal()
        
        # 设置 Goal 的参数
        goal.device_address = device_addr      # I2C 设备地址
        goal.register_address = register_addr  # 寄存器地址
        goal.data = data                       # 要写入的数据
        
        # 发送 Goal
        # send_goal() 参数说明:
        #   - goal: 要发送的目标
        #   - feedback_cb: 反馈回调函数，当服务器发送 feedback 时调用
        rospy.loginfo(f"📤 发送 Goal:")
        rospy.loginfo(f"   设备地址: 0x{device_addr:02X} ({device_addr})")
        rospy.loginfo(f"   寄存器地址: 0x{register_addr:02X} ({register_addr})")
        rospy.loginfo(f"   写入数据: 0x{data:02X} ({data})")
        
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        # ==================== 4. 等待服务器返回结果 ====================
        # wait_for_result() 等待服务器返回结果
        # Duration(5.0) 设置最大等待时间为 5 秒
        rospy.loginfo('⏳ 等待服务器返回结果...')
        
        if self.client.wait_for_result(rospy.Duration(5.0)):
            # ==================== 5. 处理并显示结果 ====================
            # get_result() 获取服务器返回的结果
            result = self.client.get_result()
            
            # 检查操作是否成功
            if result.success:
                rospy.loginfo("=" * 50)
                rospy.loginfo("✅ I2C 通信成功！")
                rospy.loginfo(f"   设备地址: 0x{device_addr:02X}")
                rospy.loginfo(f"   寄存器地址: 0x{register_addr:02X}")
                rospy.loginfo(f"   写入数据: 0x{data:02X} ({data})")
                rospy.loginfo(f"   读取数据: 0x{result.received_data:02X} ({result.received_data})")
                
                # 检查读写是否一致
                if result.received_data == data:
                    rospy.loginfo("   ✅ 读写数据一致！")
                else:
                    rospy.logwarn("   ⚠️  读写数据不一致")
                
                rospy.loginfo("=" * 50)
            else:
                rospy.logwarn("=" * 50)
                rospy.logwarn("❌ I2C 通信失败！")
                rospy.logwarn(f"   设备地址: 0x{device_addr:02X}")
                rospy.logwarn(f"   寄存器地址: 0x{register_addr:02X}")
                rospy.logwarn(f"   写入数据: 0x{data:02X}")
                rospy.logwarn("   可能原因: 设备无响应、设备地址错误、权限不足")
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
                    feedback.status.data 是状态描述
        
        说明:
          Feedback 用于服务器向客户端报告任务执行进度
          在 I2C 通信场景中，Feedback 告知客户端当前操作状态
        """
        rospy.loginfo(f"📢 Feedback: {feedback.status.data}")


# ==================== 主函数 ====================
if __name__ == '__main__':
    """
    主函数 - 程序入口
    
    功能:
      1. 初始化 ROS 节点
      2. 从命令行参数读取 I2C 通信参数
      3. 创建 I2CCommClient 实例
      4. 处理异常并优雅退出
      
    参数说明:
      _device_address: I2C 设备地址，例如 0x50
      _register_address: 寄存器地址，例如 0x00
      _data: 要写入的数据，例如 0xAA
             
    示例:
      python3 i2c_comm_client.py _device_address:=0x50 _register_address:=0x00 _data:=0xAA
    """
    try:
        # ==================== 1. 初始化 ROS 节点 ====================
        # init_node() 创建一个 ROS 节点
        # 必须在参数读取之前初始化节点
        rospy.init_node('i2c_comm_client')
        rospy.loginfo("正在初始化 I2C 通信 Action Client...")
        
        # ==================== 2. 从参数服务器读取通信参数 ====================
        # 默认值: 0x50 (EEPROM 常用地址)
        device_addr = rospy.get_param('~device_address', 0x50)
        
        # 默认值: 0x00 (第一个寄存器)
        register_addr = rospy.get_param('~register_address', 0x00)
        
        # 默认值: 0xAA (测试数据)
        data = rospy.get_param('~data', 0xAA)
        
        rospy.loginfo(f"========================================")
        rospy.loginfo(f"I2C 通信 Action Client")
        rospy.loginfo(f"========================================")
        
        # ==================== 3. 创建客户端实例 ====================
        # 构造函数中会执行完整的通信流程
        client = I2CCommClient(device_addr, register_addr, data)
        
    except rospy.ROSInterruptException:
        # 捕获 ROS 中断异常（Ctrl+C）
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        # 捕获其他异常
        rospy.logerr(f'❌ 客户端运行错误: {e}')