#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
GPIO PWM 输出 Action Client
========================================
功能说明:
  - 作为 ROS Action 客户端，向服务器发送 PWM 输出请求
  - 接收服务器的反馈信息（Feedback）
  - 接收服务器的最终结果（Result）
  - 实时显示 PWM 占空比状态
  
使用方法:
  source install/setup.bash
  python3 /home/jetson/Desktop/Jetson_Nano/action_ws/src/my_action_pkg/scripts/pwm_output_client.py \
      _pin_number:=18 \
      _frequency:=1000 \
      _duty_cycle:=50 \
      _duration:=5
  
作者: Jetson Nano
日期: 2026-03-31
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from my_action_pkg.msg import PWMOutputAction, PWMOutputGoal  # 自定义 Action 消息类型
import time                       # 时间库


# ==================== PWMOutputClient 类定义 ====================
class PWMOutputClient:
    """
    GPIO PWM 输出 Action Client 类
    
    职责:
      1. 创建 Action Client 并连接到服务器
      2. 发送 Goal（PWM 配置参数）到服务器
      3. 接收并处理服务器的 Feedback（PWM 状态）
      4. 等待并处理服务器的 Result（最终结果）
    """
    
    def __init__(self, pin_number, frequency, duty_cycle, duration):
        """
        构造函数 - 初始化客户端
        
        参数:
          pin_number: GPIO 引脚号 (BCM 编号)
          frequency: PWM 频率
          duty_cycle: 占空比 0-100%
          duration: 持续时间（秒）
        """
        
        # ==================== 1. 创建 Action Client ====================
        self.client = actionlib.SimpleActionClient('pwm_output', PWMOutputAction)
        
        # ==================== 2. 等待服务器上线 ====================
        rospy.loginfo('⏳ 等待 Action Server 上线...')
        self.client.wait_for_server()
        rospy.loginfo('✅ Action Server 已连接')
        
        # ==================== 3. 创建并发送 Goal ====================
        goal = PWMOutputGoal()
        goal.pin_number = pin_number
        goal.frequency = frequency
        goal.duty_cycle = duty_cycle
        goal.duration = duration
        
        rospy.loginfo(f"📤 发送 Goal:")
        rospy.loginfo(f"   GPIO 引脚: {pin_number} (BCM 编号)")
        rospy.loginfo(f"   PWM 频率: {frequency} Hz")
        rospy.loginfo(f"   占空比: {duty_cycle}%")
        rospy.loginfo(f"   持续时间: {duration} 秒")
        
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        # ==================== 4. 等待结果 ====================
        rospy.loginfo("⏳ 等待 PWM 输出完成...")
        
        if self.client.wait_for_result(rospy.Duration(duration + 10)):
            result = self.client.get_result()
            
            if result.success:
                rospy.loginfo("=" * 60)
                rospy.loginfo("✅ PWM 输出成功！")
                rospy.loginfo(f"   GPIO 引脚: {pin_number}")
                rospy.loginfo(f"   PWM 频率: {frequency} Hz")
                rospy.loginfo(f"   占空比: {duty_cycle}%")
                rospy.loginfo("=" * 60)
            else:
                rospy.logwarn("❌ PWM 输出失败！")
        else:
            rospy.logerr("❌ 等待结果超时")
    
    # ==================== 反馈回调函数 ====================
    def feedback_cb(self, feedback):
        """
        反馈回调函数
        
        参数:
          feedback.current_duty_cycle: 当前占空比
          feedback.timestamp: 时间戳
        """
        # 转换时间戳为可读格式
        timestamp_sec = feedback.timestamp / 1e9
        timestamp_str = time.strftime('%H:%M:%S', time.localtime(timestamp_sec))
        
        rospy.loginfo(f"📊 PWM 状态: 占空比 {feedback.current_duty_cycle}% at {timestamp_str}")


# ==================== 主函数 ====================
if __name__ == '__main__':
    try:
        # ==================== 1. 初始化 ROS 节点 ====================
        rospy.init_node('pwm_output_client')
        rospy.loginfo("正在初始化 GPIO PWM 输出 Action Client...")
        
        # ==================== 2. 从参数服务器读取配置参数 ====================
        pin_number = rospy.get_param('~pin_number', 18)       # 默认 GPIO 18 (Pin 12)
        frequency = rospy.get_param('~frequency', 1000)       # 默认 1 kHz
        duty_cycle = rospy.get_param('~duty_cycle', 50)       # 默认 50%
        duration = rospy.get_param('~duration', 5)            # 默认 5 秒
        
        # 验证占空比范围
        if not 0 <= duty_cycle <= 100:
            rospy.logerr(f'❌ 占空比必须在 0-100% 范围内')
            sys.exit(1)
        
        rospy.loginfo(f"========================================")
        rospy.loginfo(f"GPIO PWM 输出 Action Client")
        rospy.loginfo(f"========================================")
        
        # ==================== 3. 创建客户端实例 ====================
        client = PWMOutputClient(pin_number, frequency, duty_cycle, duration)
        
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在退出...')
    except Exception as e:
        rospy.logerr(f'❌ 客户端运行错误: {e}')