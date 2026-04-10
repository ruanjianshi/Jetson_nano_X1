#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
GPIO PWM 输出 Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，控制 GPIO 引脚输出 PWM 信号
  - 使用 Jetson.GPIO 库的 PWM 功能
  - 支持频率和占空比设置
  - 支持持续时间控制
  - 实时反馈当前占空比状态
  
硬件连接:
  Jetson Nano PWM 引脚:
    - Pin 12 (GPIO 18): PWM0
    - Pin 32 (GPIO 12): PWM0
    - Pin 33 (GPIO 13): PWM1
    - Pin 35 (GPIO 19): PWM1
  
使用方法:
  source install/setup.bash
  sudo rosrun my_action_pkg pwm_output_server.py
  
作者: Jetson Nano
日期: 2026-03-31
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from my_action_pkg.msg import PWMOutputAction, PWMOutputFeedback, PWMOutputResult  # 自定义 Action 消息类型
import time                       # 时间库
try:
    import Jetson.GPIO as GPIO   # Jetson Nano 专用 GPIO 库
except ImportError:
    try:
        import RPi.GPIO as GPIO  # Raspberry Pi GPIO 库（兼容）
    except ImportError:
        print("错误: 无法导入 GPIO 库，请安装 Jetson.GPIO 或 RPi.GPIO")
        GPIO = None


# ==================== PWMOutputServer 类定义 ====================
class PWMOutputServer:
    """
    GPIO PWM 输出 Action Server 类
    
    职责:
      1. 初始化 ROS 节点和 GPIO 库
      2. 创建 Action Server 接收客户端请求
      3. 配置 GPIO 引脚为 PWM 输出
      4. 设置 PWM 频率和占空比
      5. 实时反馈 PWM 状态
      6. 清理 GPIO 资源
    """
    
    # 支持 PWM 的引脚
    PWM_PINS = {
        18: "Pin 12 (PWM0)",
        12: "Pin 32 (PWM0)",
        13: "Pin 33 (PWM1)",
        19: "Pin 35 (PWM1)"
    }
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        
        功能:
          1. 初始化 ROS 节点
          2. 初始化 GPIO 库
          3. 创建并启动 Action Server
        """
        
        # ==================== 1. 初始化 ROS 节点 ====================
        rospy.init_node('pwm_output_server')
        rospy.loginfo("正在初始化 GPIO PWM 输出 Action Server...")
        
        # ==================== 2. 检查 GPIO 库 ====================
        if GPIO is None:
            rospy.logerr('❌ GPIO 库未安装，请先安装: pip3 install Jetson.GPIO')
            return
        
        # ==================== 3. 初始化 GPIO 库 ====================
        # GPIO.setmode() 设置 GPIO 编号模式
        # GPIO.BCM: 使用 Broadcom SOC 通道编号
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            rospy.loginfo("✅ GPIO 库已初始化 (BCM 模式)")
        except Exception as e:
            rospy.logerr(f'❌ GPIO 初始化失败: {e}')
            return
        
        # PWM 对象
        self.pwm = None
        self.current_pin = None
        self.running = False
        
        # ==================== 4. 创建并启动 Action Server ====================
        self.server = actionlib.SimpleActionServer(
            'pwm_output', 
            PWMOutputAction, 
            self.execute, 
            False
        )
        
        self.server.start()
        
        rospy.loginfo(f"✅ GPIO PWM 输出 Action Server 已启动")
        rospy.loginfo(f"   Action 名称: pwm_output")
        rospy.loginfo(f"   支持的 PWM 引脚: {list(self.PWM_PINS.keys())}")
        rospy.loginfo(f"   等待客户端配置 PWM...")
        
        # 注册清理函数
        rospy.on_shutdown(self.cleanup)
    
    # ==================== Action 执行回调函数 ====================
    def execute(self, goal):
        """
        执行 Goal 的回调函数
        
        参数:
          goal.pin_number: GPIO 引脚号 (BCM 编号)
          goal.frequency: PWM 频率
          goal.duty_cycle: 占空比 0-100%
          goal.duration: 持续时间（秒）
        """
        
        # ==================== 1. 清理之前的 PWM ====================
        if self.pwm is not None:
            try:
                self.pwm.stop()
                GPIO.cleanup(self.current_pin)
                rospy.loginfo(f"清理之前的 PWM: {self.current_pin}")
            except Exception as e:
                rospy.logwarn(f"清理 PWM 时出错: {e}")
        
        # ==================== 2. 获取配置参数 ====================
        pin_number = goal.pin_number
        frequency = goal.frequency
        duty_cycle = goal.duty_cycle
        duration = goal.duration
        
        rospy.loginfo(f"📥 收到 Goal:")
        rospy.loginfo(f"   GPIO 引脚: {pin_number} (BCM 编号)")
        rospy.loginfo(f"   PWM 频率: {frequency} Hz")
        rospy.loginfo(f"   占空比: {duty_cycle}%")
        rospy.loginfo(f"   持续时间: {duration} 秒")
        
        # ==================== 3. 验证引脚 ====================
        if pin_number not in self.PWM_PINS:
            rospy.logerr(f'❌ 引脚 {pin_number} 不支持 PWM')
            rospy.logerr(f'   支持的 PWM 引脚: {self.PWM_PINS}')
            result = PWMOutputResult()
            result.success = False
            self.server.set_aborted(result)
            return
        
        # ==================== 4. 配置 PWM ====================
        try:
            # 设置 GPIO 为输出模式
            GPIO.setup(pin_number, GPIO.OUT)
            
            # 创建 PWM 对象
            # GPIO.PWM(channel, frequency)
            self.pwm = GPIO.PWM(pin_number, frequency)
            
            # 启动 PWM
            self.pwm.start(duty_cycle)
            
            self.current_pin = pin_number
            self.running = True
            
            rospy.loginfo(f"✅ PWM 已启动:")
            rospy.loginfo(f"   引脚位置: {self.PWM_PINS[pin_number]}")
            rospy.loginfo(f"   频率: {frequency} Hz")
            rospy.loginfo(f"   占空比: {duty_cycle}%")
            
        except Exception as e:
            rospy.logerr(f'❌ PWM 配置失败: {e}')
            result = PWMOutputResult()
            result.success = False
            self.server.set_aborted(result)
            return
        
        # ==================== 5. 运行 PWM 并发送反馈 ====================
        start_time = time.time()
        rate = rospy.Rate(2)  # 2 Hz 反馈频率
        
        try:
            while not rospy.is_shutdown() and self.running:
                # 检查是否超时
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    rospy.loginfo(f"⏱️  持续时间结束 ({duration} 秒)")
                    break
                
                # 检查是否收到取消请求
                if self.server.is_preempt_requested():
                    rospy.loginfo("⏹️  收到取消请求")
                    self.server.set_preempted()
                    self.running = False
                    break
                
                # 发送 Feedback（当前占空比）
                feedback = PWMOutputFeedback()
                feedback.current_duty_cycle = duty_cycle
                feedback.timestamp = int(time.time() * 1e9)
                self.server.publish_feedback(feedback)
                
                rate.sleep()
                
        except rospy.ROSInterruptException:
            rospy.loginfo("⏹️  收到中断信号")
        
        finally:
            # ==================== 6. 清理资源 ====================
            try:
                if self.pwm is not None:
                    self.pwm.stop()
                    self.pwm = None
                if self.current_pin is not None:
                    GPIO.cleanup(self.current_pin)
                    rospy.loginfo(f"引脚 {self.current_pin} 已清理")
                    self.current_pin = None
                self.running = False
            except Exception as e:
                rospy.logwarn(f"清理资源时出错: {e}")
        
        # ==================== 7. 返回结果 ====================
        result = PWMOutputResult()
        result.success = True
        self.server.set_succeeded(result)
        rospy.loginfo("✅ PWM 输出任务完成")
    
    # ==================== 清理函数 ====================
    def cleanup(self):
        """清理 GPIO 资源"""
        rospy.loginfo("正在清理 PWM 资源...")
        try:
            if self.pwm is not None:
                self.pwm.stop()
                self.pwm = None
            GPIO.cleanup()
            rospy.loginfo("✅ PWM 资源已清理")
        except Exception as e:
            rospy.logerr(f'清理 PWM 资源时出错: {e}')


# ==================== 主函数 ====================
if __name__ == '__main__':
    server = None
    try:
        server = PWMOutputServer()
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在关闭...')
    except Exception as e:
        rospy.logerr(f'❌ 节点运行错误: {e}')
    finally:
        if server:
            server.cleanup()