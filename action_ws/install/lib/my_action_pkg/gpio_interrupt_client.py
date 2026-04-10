#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
GPIO 中断 Action Client
========================================
功能说明:
  - 作为 ROS Action 客户端，向服务器发送 GPIO 中断配置请求
  - 接收服务器的反馈信息（Feedback）- 中断事件
  - 接收服务器的最终结果（Result）
  - 实时显示 GPIO 中断事件
  - 统计中断次数
  
使用方法:
  source install/setup.bash
  python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/gpio_interrupt_client.py \
      _pin_number:=18 \
      _edge_mode:=2 \
      _debounce_ms:=50
  
作者: Jetson Nano
日期: 2026-03-30
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from my_action_pkg.msg import GPIOInterruptAction, GPIOInterruptGoal  # 自定义 Action 消息类型
from std_msgs.msg import String   # ROS 标准字符串消息类型
import time                       # 时间库


# ==================== GPIOInterruptClient 类定义 ====================
class GPIOInterruptClient:
    """
    GPIO 中断 Action Client 类
    
    职责:
      1. 创建 Action Client 并连接到服务器
      2. 发送 Goal（GPIO 中断配置参数）到服务器
      3. 接收并处理服务器的 Feedback（中断事件）
      4. 等待并处理服务器的 Result（最终结果）
      5. 实时显示中断统计信息
    """
    
    # 边沿模式常量
    RISING = 0   # 上升沿
    FALLING = 1  # 下降沿
    BOTH = 2     # 双边沿
    
    def __init__(self, pin_number, edge_mode, debounce_ms, duration=30):
        """
        构造函数 - 初始化客户端
        
        参数:
          pin_number: GPIO 引脚号 (BCM 编号)
          edge_mode: 边沿模式 (0=上升沿, 1=下降沿, 2=双边沿)
          debounce_ms: 去抖动时间 (毫秒)
          duration: 持续监听时间（秒），默认 30 秒
        
        执行流程:
          1. 创建 Action Client
          2. 等待服务器上线
          3. 创建并发送 Goal
          4. 持续接收 Feedback（中断事件）
          5. 显示统计结果
        """
        
        # 边沿模式映射
        edge_names = {
            self.RISING: "上升沿",
            self.FALLING: "下降沿",
            self.BOTH: "双边沿"
        }
        
        self.edge_name = edge_names.get(edge_mode, f"未知 ({edge_mode})")
        self.interrupt_count = 0
        self.last_event_type = ""
        
        # ==================== 1. 创建 Action Client ====================
        # SimpleActionClient 是 ROS 提供的简化 Action Client 实现
        # 参数说明:
        #   - 'gpio_interrupt': Action 名称，必须与服务器端的 Action 名称一致
        #   - GPIOInterruptAction: Action 类型（由 .action 文件生成）
        self.client = actionlib.SimpleActionClient('gpio_interrupt', GPIOInterruptAction)
        
        # ==================== 2. 等待服务器上线 ====================
        # wait_for_server() 阻塞等待服务器启动
        # 如果服务器未启动，此函数会一直等待
        rospy.loginfo('⏳ 等待 Action Server 上线...')
        self.client.wait_for_server()
        rospy.loginfo('✅ Action Server 已连接')
        
        # ==================== 3. 创建并发送 Goal ====================
        # 创建 Goal 对象
        goal = GPIOInterruptGoal()
        
        # 设置 Goal 的参数
        goal.pin_number = pin_number    # GPIO 引脚号
        goal.edge_mode = edge_mode      # 边沿模式
        goal.debounce_ms = debounce_ms  # 去抖动时间
        
        # 发送 Goal
        # send_goal() 参数说明:
        #   - goal: 要发送的目标
        #   - feedback_cb: 反馈回调函数，当服务器发送 feedback 时调用
        rospy.loginfo(f"📤 发送 Goal:")
        rospy.loginfo(f"   GPIO 引脚: {pin_number} (BCM 编号)")
        rospy.loginfo(f"   边沿模式: {self.edge_name}")
        rospy.loginfo(f"   去抖动时间: {debounce_ms} ms")
        rospy.loginfo(f"   监听时长: {duration} 秒")
        
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        # ==================== 4. 等待结果或超时 ====================
        rospy.loginfo("=" * 60)
        rospy.loginfo("🔔 开始监听 GPIO 中断事件...")
        rospy.loginfo("=" * 60)
        rospy.loginfo("提示: 按下 Ctrl+C 取消监听")
        rospy.loginfo("")
        
        # wait_for_result() 等待服务器返回结果
        # Duration(duration) 设置最大等待时间
        if self.client.wait_for_result(rospy.Duration(duration)):
            # ==================== 5. 处理并显示结果 ====================
            # get_result() 获取服务器返回的结果
            result = self.client.get_result()
            
            # 显示统计结果
            rospy.loginfo("")
            rospy.loginfo("=" * 60)
            if result.success:
                rospy.loginfo("✅ GPIO 中断监听完成！")
                rospy.loginfo(f"   GPIO 引脚: {pin_number}")
                rospy.loginfo(f"   边沿模式: {self.edge_name}")
                rospy.loginfo(f"   总中断次数: {result.interrupt_count}")
                rospy.loginfo("=" * 60)
            else:
                rospy.logwarn("❌ GPIO 中断监听失败！")
                rospy.logwarn(f"   GPIO 引脚: {pin_number}")
                rospy.logwarn("   可能原因: GPIO 引脚配置错误、权限不足")
                rospy.logwarn("=" * 60)
        else:
            # 超时
            rospy.loginfo("")
            rospy.loginfo("=" * 60)
            rospy.loginfo(f"⏱️  监听超时 ({duration} 秒)")
            rospy.loginfo("   中断统计:")
            rospy.loginfo(f"   总中断次数: {self.interrupt_count}")
            rospy.loginfo("=" * 60)
            
            # 取消 Goal
            self.client.cancel_goal()
    
    # ==================== 反馈回调函数 ====================
    def feedback_cb(self, feedback):
        """
        反馈回调函数
        
        当服务器发送 feedback 时，Action Client 会自动调用此函数
        
        参数:
          feedback: 服务器发送的反馈信息
                    feedback.event_type.data 是事件类型 ("rising", "falling", "level")
                    feedback.timestamp 是时间戳（纳秒）
                    feedback.pin_level 是 GPIO 电平 (0=LOW, 1=HIGH)
        
        说明:
          Feedback 用于服务器向客户端报告中断事件和 GPIO 电平状态
          - 中断事件: event_type = "rising" 或 "falling"
          - 电平状态: event_type = "level" (每 2 秒发送一次)
        """
        # 判断反馈类型
        if feedback.event_type.data == "level":
            # GPIO 电平反馈
            level_str = "HIGH" if feedback.pin_level == 1 else "LOW"
            
            # 转换时间戳为可读格式
            timestamp_sec = feedback.timestamp / 1e9
            timestamp_str = time.strftime('%H:%M:%S', time.localtime(timestamp_sec))
            
            # 打印电平状态
            rospy.loginfo(f"📊 GPIO 电平状态: {level_str} at {timestamp_str}")
            
        else:
            # 中断事件反馈
            # 增加中断计数
            self.interrupt_count += 1
            self.last_event_type = feedback.event_type.data
            
            # 转换时间戳为可读格式
            timestamp_sec = feedback.timestamp / 1e9
            timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_sec))
            timestamp_ms = int((feedback.timestamp % 1e9) / 1e6)
            
            # 获取边沿类型的中文名称
            edge_map = {
                "rising": "上升沿",
                "falling": "下降沿"
            }
            edge_cn = edge_map.get(feedback.event_type.data, feedback.event_type.data)
            
            # 打印中断事件
            rospy.loginfo(f"🔔 中断 #{self.interrupt_count}: "
                         f"{edge_cn} "
                         f"at {timestamp_str}.{timestamp_ms:03d}")
            
            # 同时显示电平
            level_str = "HIGH" if feedback.pin_level == 1 else "LOW"
            rospy.loginfo(f"   GPIO 电平: {level_str}")


# ==================== 主函数 ====================
if __name__ == '__main__':
    """
    主函数 - 程序入口
    
    功能:
      1. 初始化 ROS 节点
      2. 从命令行参数读取 GPIO 中断配置参数
      3. 创建 GPIOInterruptClient 实例
      4. 处理异常并优雅退出
      
    参数说明:
      _pin_number: GPIO 引脚号 (BCM 编号)，例如 18
      _edge_mode: 边沿模式，0=上升沿, 1=下降沿, 2=双边沿
      _debounce_ms: 去抖动时间（毫秒），例如 50
      _duration: 监听时长（秒），例如 30
             
    示例:
      python3 gpio_interrupt_client.py \
          _pin_number:=18 \
          _edge_mode:=2 \
          _debounce_ms:=50 \
          _duration:=30
    """
    try:
        # ==================== 1. 初始化 ROS 节点 ====================
        # init_node() 创建一个 ROS 节点
        # 必须在参数读取之前初始化节点
        rospy.init_node('gpio_interrupt_client')
        rospy.loginfo("正在初始化 GPIO 中断 Action Client...")
        
        # ==================== 2. 从参数服务器读取配置参数 ====================
        # 默认值: 18 (Jetson Nano 常用 GPIO 引脚)
        pin_number = rospy.get_param('~pin_number', 18)
        
        # 默认值: 2 (双边沿)
        edge_mode = rospy.get_param('~edge_mode', 2)
        
        # 默认值: 50 (去抖动时间)
        debounce_ms = rospy.get_param('~debounce_ms', 50)
        
        # 默认值: 30 (监听时长)
        duration = rospy.get_param('~duration', 30)
        
        rospy.loginfo(f"========================================")
        rospy.loginfo(f"GPIO 中断 Action Client")
        rospy.loginfo(f"========================================")
        
        # ==================== 3. 创建客户端实例 ====================
        # 构造函数中会执行完整的通信流程
        client = GPIOInterruptClient(pin_number, edge_mode, debounce_ms, duration)
        
    except rospy.ROSInterruptException:
        # 捕获 ROS 中断异常（Ctrl+C）
        rospy.loginfo('')
        rospy.loginfo('📛 收到中断信号，正在退出...')
        
    except Exception as e:
        # 捕获其他异常
        rospy.logerr(f'❌ 客户端运行错误: {e}')