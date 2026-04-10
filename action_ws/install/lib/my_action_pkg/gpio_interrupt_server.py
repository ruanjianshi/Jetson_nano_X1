#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
GPIO 中断 Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，配置 GPIO 引脚为中断模式
  - 使用 GPIO 库检测 GPIO 引脚的中断事件
  - 支持上升沿、下降沿、双边沿检测
  - 支持去抖动（debounce）功能
  - 通过 Feedback 实时发送中断事件给客户端
  - 统计中断次数
  
硬件连接:
  Jetson Nano GPIO (BCM 编号):
    - GPIO 0-27: 可用的 GPIO 引脚
    - 部分引脚有特殊功能，请查看引脚图
  
使用方法:
  source install/setup.bash
  sudo rosrun my_action_pkg gpio_interrupt_server.py
  
作者: Jetson Nano
日期: 2026-03-30
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from my_action_pkg.msg import GPIOInterruptAction, GPIOInterruptFeedback, GPIOInterruptResult  # 自定义 Action 消息类型
from std_msgs.msg import String   # ROS 标准字符串消息类型
import time                       # 时间库
import threading                  # 线程库
try:
    import Jetson.GPIO as GPIO   # Jetson Nano 专用 GPIO 库
except ImportError:
    try:
        import RPi.GPIO as GPIO  # Raspberry Pi GPIO 库（兼容）
    except ImportError:
        print("错误: 无法导入 GPIO 库，请安装 Jetson.GPIO 或 RPi.GPIO")
        GPIO = None


# ==================== GPIOInterruptServer 类定义 ====================
class GPIOInterruptServer:
    """
    GPIO 中断 Action Server 类
    
    职责:
      1. 初始化 ROS 节点和 GPIO 库
      2. 创建 Action Server 接收客户端请求
      3. 配置 GPIO 引脚为中断模式
      4. 检测中断事件并发送 Feedback
      5. 统计中断次数
      6. 清理 GPIO 资源
    """
    
    # 边沿模式常量
    RISING = 0   # 上升沿
    FALLING = 1  # 下降沿
    BOTH = 2     # 双边沿
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        
        功能:
          1. 初始化 ROS 节点
          2. 初始化 GPIO 库
          3. 创建并启动 Action Server
        """
        
        # ==================== 1. 初始化 ROS 节点 ====================
        rospy.init_node('gpio_interrupt_server')
        rospy.loginfo("正在初始化 GPIO 中断 Action Server...")
        
        # ==================== 2. 检查 GPIO 库 ====================
        if GPIO is None:
            rospy.logerr('❌ GPIO 库未安装，请先安装: pip3 install Jetson.GPIO')
            rospy.logerr('   或: pip3 install RPi.GPIO')
            return
        
        # ==================== 3. 初始化 GPIO 库 ====================
        # GPIO.setmode() 设置 GPIO 编号模式
        # GPIO.BCM: 使用 Broadcom SOC 通道编号
        # GPIO.BOARD: 使用物理引脚编号
        try:
            GPIO.setmode(GPIO.BCM)
            rospy.loginfo("✅ GPIO 库已初始化 (BCM 模式)")
        except Exception as e:
            rospy.logerr(f'❌ GPIO 初始化失败: {e}')
            return
        
        # 中断计数和状态
        self.interrupt_count = 0
        self.running = False
        self.current_pin = None
        self.last_interrupt_time = 0
        self.debounce_ms = 0
        self.last_level_feedback_time = 0  # 上次发送电平反馈的时间
        
        # ==================== 4. 创建并启动 Action Server ====================
        # SimpleActionServer 是 ROS 提供的简化 Action Server 实现
        # 参数说明:
        #   - 'gpio_interrupt': Action 名称，客户端需要使用相同名称连接
        #   - GPIOInterruptAction: Action 类型（由 .action 文件生成）
        #   - self.execute: 执行回调函数，当收到 goal 时调用
        #   - False: 不自动启动，需要手动 start()
        self.server = actionlib.SimpleActionServer(
            'gpio_interrupt', 
            GPIOInterruptAction, 
            self.execute, 
            False
        )
        
        # 启动服务器
        self.server.start()
        
        # 打印启动成功信息
        rospy.loginfo(f"✅ GPIO 中断 Action Server 已启动")
        rospy.loginfo(f"   Action 名称: gpio_interrupt")
        rospy.loginfo(f"   等待客户端配置 GPIO 中断...")
        
        # 注册清理函数（程序退出时自动调用）
        rospy.on_shutdown(self.cleanup)
    
    # ==================== 中断回调函数 ====================
    def interrupt_callback(self, channel):
        """
        GPIO 中断回调函数
        
        当检测到 GPIO 中断时，此函数会被 GPIO 库自动调用
        
        参数:
          channel: GPIO 通道号（BCM 编号）
        
        功能:
          1. 检查去抖动时间
          2. 更新中断计数
          3. 检测边沿类型
          4. 发送 Feedback 给客户端
        """
        # 获取当前时间戳
        current_time = time.time() * 1e9  # 转换为纳秒
        time_diff_ms = (current_time - self.last_interrupt_time) / 1e6
        
        # 去抖动检查
        if self.debounce_ms > 0 and time_diff_ms < self.debounce_ms:
            return  # 忽略频繁中断
        
        # 更新最后中断时间
        self.last_interrupt_time = current_time
        
        # 增加中断计数
        self.interrupt_count += 1
        
        # 读取当前 GPIO 状态
        try:
            current_state = GPIO.input(channel)
        except Exception as e:
            rospy.logerr(f'读取 GPIO 状态失败: {e}')
            return
        
        # 判断边沿类型
        if current_state == GPIO.HIGH:
            event_type = "rising"   # 上升沿
        else:
            event_type = "falling"  # 下降沿
        
        # 发送 Feedback 给客户端
        feedback = GPIOInterruptFeedback()
        feedback.event_type = String(data=event_type)
        feedback.timestamp = int(current_time)
        feedback.pin_level = 1 if current_state == GPIO.HIGH else 0
        
        self.server.publish_feedback(feedback)
        
        # 打印中断信息
        rospy.loginfo(f"🔔 中断 #{self.interrupt_count}: 引脚 {channel}, "
                     f"类型: {event_type}, "
                     f"状态: {'HIGH' if current_state else 'LOW'}")
    
    # ==================== Action 执行回调函数 ====================
    def execute(self, goal):
        """
        执行 Goal 的回调函数
        
        当客户端发送一个 Goal 时，Action Server 会自动调用此函数
        
        参数:
          goal: 客户端发送的目标，包含 GPIO 中断配置参数
                goal.pin_number: GPIO 引脚号 (BCM 编号)
                goal.edge_mode: 边沿模式 (0=上升沿, 1=下降沿, 2=双边沿)
                goal.debounce_ms: 去抖动时间 (毫秒)
        
        执行流程:
          1. 清理之前的 GPIO 配置
          2. 配置 GPIO 引脚为输入模式
          3. 设置中断检测
          4. 等待中断事件
          5. 返回统计结果
        """
        
        # ==================== 1. 清理之前的配置 ====================
        # 先清理之前配置的引脚
        if self.current_pin is not None:
            try:
                GPIO.remove_event_detect(self.current_pin)
                GPIO.cleanup(self.current_pin)
                rospy.loginfo(f"清理之前配置的引脚: {self.current_pin}")
            except Exception as e:
                rospy.logwarn(f"清理引脚时出错: {e}")
        
        # 然后清理所有 GPIO（防止冲突）
        try:
            GPIO.cleanup()
            rospy.loginfo("清理所有 GPIO 资源")
        except Exception as e:
            rospy.logwarn(f"清理 GPIO 资源时出错: {e}")
        
        # 重新初始化 BCM 模式（因为 cleanup 会清除模式设置）
        GPIO.setmode(GPIO.BCM)
        
        # ==================== 2. 获取配置参数 ====================
        pin_number = goal.pin_number       # GPIO 引脚号
        edge_mode = goal.edge_mode        # 边沿模式
        debounce_ms = goal.debounce_ms    # 去抖动时间
        
        # 重置中断计数
        self.interrupt_count = 0
        self.current_pin = pin_number
        self.debounce_ms = debounce_ms
        self.running = True
        
        rospy.loginfo(f"📥 收到 Goal:")
        rospy.loginfo(f"   GPIO 引脚: {pin_number} (BCM 编号)")
        
        # 边沿模式映射
        edge_map = {
            self.RISING: GPIO.RISING,
            self.FALLING: GPIO.FALLING,
            self.BOTH: GPIO.BOTH
        }
        edge_names = {
            self.RISING: "上升沿",
            self.FALLING: "下降沿",
            self.BOTH: "双边沿"
        }
        
        # 验证边沿模式
        if edge_mode not in edge_map:
            rospy.logerr(f'❌ 无效的边沿模式: {edge_mode}')
            result = GPIOInterruptResult()
            result.success = False
            result.interrupt_count = 0
            self.server.set_aborted(result)
            return
        
        edge = edge_map[edge_mode]
        edge_name = edge_names[edge_mode]
        
        rospy.loginfo(f"   边沿模式: {edge_name} ({edge_mode})")
        rospy.loginfo(f"   去抖动时间: {debounce_ms} ms")
        
        # ==================== 3. 配置 GPIO 引脚 ====================
        try:
            # 设置 GPIO 为输入模式，启用下拉电阻（默认低电平）
            GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            rospy.loginfo(f"✅ 引脚 {pin_number} 已配置为输入模式（下拉电阻）")
            
            # 读取初始状态
            initial_state = GPIO.input(pin_number)
            rospy.loginfo(f"   初始状态: {'HIGH' if initial_state else 'LOW'}")
            
        except Exception as e:
            rospy.logerr(f'❌ GPIO 配置失败: {e}')
            result = GPIOInterruptResult()
            result.success = False
            result.interrupt_count = 0
            self.server.set_aborted(result)
            return
        
        # ==================== 4. 设置中断检测 ====================
        try:
            # add_event_detect() 设置中断检测
            # 参数说明:
            #   - channel: GPIO 通道号
            #   - edge: 边沿类型 (RISING, FALLING, BOTH)
            #   - callback: 回调函数
            #   - bouncetime: 去抖动时间（毫秒）
            GPIO.add_event_detect(
                pin_number,
                edge,
                callback=self.interrupt_callback,
                bouncetime=debounce_ms
            )
            rospy.loginfo(f"✅ 中断检测已启用，等待中断事件...")
            
        except Exception as e:
            rospy.logerr(f'❌ 中断检测设置失败: {e}')
            result = GPIOInterruptResult()
            result.success = False
            result.interrupt_count = 0
            self.server.set_aborted(result)
            return
        
        # ==================== 5. 等待中断或取消 ====================
        # 持续检测中断，直到收到取消请求
        rate = rospy.Rate(10)  # 10 Hz
        preempted = False
        self.last_level_feedback_time = 0
        
        try:
            while not rospy.is_shutdown():
                # 检查是否收到取消请求
                if self.server.is_preempt_requested():
                    rospy.loginfo("⏹️  收到取消请求")
                    self.server.set_preempted()
                    preempted = True
                    break
                
                # ==================== 定期发送 GPIO 电平反馈 ====================
                # 每 2 秒发送一次当前 GPIO 电平状态
                current_time = time.time()
                if current_time - self.last_level_feedback_time >= 2.0:
                    try:
                        # 读取当前 GPIO 电平
                        pin_level = GPIO.input(pin_number)
                        
                        # 发送反馈信息
                        feedback = GPIOInterruptFeedback()
                        feedback.event_type = String(data="level")
                        feedback.timestamp = int(current_time * 1e9)
                        feedback.pin_level = 1 if pin_level == GPIO.HIGH else 0
                        
                        self.server.publish_feedback(feedback)
                        
                        # 更新最后发送时间
                        self.last_level_feedback_time = current_time
                        
                        # 打印电平信息（仅首次和状态变化时）
                        rospy.loginfo(f"📊 GPIO {pin_number} 电平: {'HIGH' if pin_level == GPIO.HIGH else 'LOW'}")
                        
                    except Exception as e:
                        rospy.logwarn(f"读取 GPIO 电平失败: {e}")
                
                rate.sleep()
                
        except rospy.ROSInterruptException:
            rospy.loginfo("⏹️  收到中断信号")
            preempted = True
        
        finally:
            # ==================== 6. 清理资源 ====================
            try:
                GPIO.remove_event_detect(pin_number)
                GPIO.cleanup(pin_number)
                rospy.loginfo(f"引脚 {pin_number} 已清理")
            except Exception as e:
                rospy.logwarn(f"清理引脚时出错: {e}")
        
        # ==================== 7. 返回结果 ====================
        # 只有在未被 preempted 的情况下才设置 succeeded
        if not preempted:
            result = GPIOInterruptResult()
            result.success = True
            result.interrupt_count = self.interrupt_count
            
            self.server.set_succeeded(result)
            rospy.loginfo(f"✅ Goal 执行完成，共检测到 {self.interrupt_count} 次中断")
    
    # ==================== 清理函数 ====================
    def cleanup(self):
        """
        清理 GPIO 资源
        
        功能:
          1. 移除所有中断检测
          2. 清理所有 GPIO 引脚
        """
        rospy.loginfo("正在清理 GPIO 资源...")
        try:
            GPIO.cleanup()
            rospy.loginfo("✅ GPIO 资源已清理")
        except Exception as e:
            rospy.logerr(f'清理 GPIO 资源时出错: {e}')


# ==================== 主函数 ====================
if __name__ == '__main__':
    """
    主函数 - 程序入口
    
    功能:
      1. 创建 GPIOInterruptServer 实例
      2. 保持节点运行，等待 Goal 请求
      3. 处理异常并优雅退出
    """
    server = None
    try:
        # 创建服务器实例
        # 构造函数中会初始化 ROS 节点和 GPIO 库
        server = GPIOInterruptServer()
        
        # rospy.spin() 保持节点运行
        # 这是一个阻塞调用，直到节点被关闭（Ctrl+C）
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
        
    except rospy.ROSInterruptException:
        # 捕获 ROS 中断异常（Ctrl+C）
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        # 捕获其他异常
        rospy.logerr(f'❌ 节点运行错误: {e}')
        
    finally:
        # 清理资源
        if server:
            server.cleanup()