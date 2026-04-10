#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
I2C 通信 Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，接收客户端发送的 I2C 写入请求
  - 使用 smbus2 库通过 I2C 总线与设备通信
  - 支持向指定设备地址和寄存器写入数据
  - 支持从指定设备地址和寄存器读取数据
  - 支持参数配置（I2C 总线编号等）
  
硬件连接:
  Jetson Nano I2C1:
    - 引脚 3 (GPIO 2/I2C1_SDA): SDA 数据线
    - 引脚 5 (GPIO 3/I2C1_SCL): SCL 时钟线
    - 设备路径: /dev/i2c-1
  
使用方法:
  source install/setup.bash
  sudo rosrun my_action_pkg i2c_comm_server.py
  
作者: Jetson Nano
日期: 2026-03-30
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
from smbus2 import SMBus, i2c_msg  # SMBus2 库（I2C 通信）
import time                       # 时间库
from my_action_pkg.msg import I2CCommAction, I2CCommFeedback, I2CCommResult  # 自定义 Action 消息类型
from std_msgs.msg import String   # ROS 标准字符串消息类型


# ==================== I2CCommServer 类定义 ====================
class I2CCommServer:
    """
    I2C 通信 Action Server 类
    
    职责:
      1. 初始化 ROS 节点和 I2C 总线
      2. 创建 Action Server 接收客户端请求
      3. 执行 I2C 写入和读取操作
      4. 返回操作结果给客户端
    """
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        
        功能:
          1. 初始化 ROS 节点
          2. 从参数服务器读取配置参数
          3. 初始化 I2C 总线
          4. 创建并启动 Action Server
        """
        
        # ==================== 1. 初始化 ROS 节点 ====================
        rospy.init_node('i2c_comm_server')
        rospy.loginfo("正在初始化 I2C 通信 Action Server...")
        
        # ==================== 2. 从参数服务器读取配置 ====================
        # rospy.get_param('~param_name', default_value)
        # '~' 表示私有命名空间，例如: /i2c_comm_server/i2c_bus
        self.i2c_bus = rospy.get_param('~i2c_bus', 1)                    # I2C 总线编号，默认 1 (/dev/i2c-1)
        self.enable_scan = rospy.get_param('~enable_scan', False)         # 是否扫描总线上的设备
        self.enable_echo = rospy.get_param('~enable_echo', True)          # 是否启用日志回显
        
        # I2C 总线对象
        self.bus = None
        self.connected = False
        
        # ==================== 3. 初始化 I2C 总线 ====================
        self.init_i2c_bus()
        
        # ==================== 4. 扫描 I2C 设备（可选） ====================
        if self.enable_scan:
            self.scan_i2c_devices()
        
        # ==================== 5. 创建并启动 Action Server ====================
        # SimpleActionServer 是 ROS 提供的简化 Action Server 实现
        # 参数说明:
        #   - 'i2c_comm': Action 名称，客户端需要使用相同名称连接
        #   - I2CCommAction: Action 类型（由 .action 文件生成）
        #   - self.execute: 执行回调函数，当收到 goal 时调用
        #   - False: 不自动启动，需要手动 start()
        self.server = actionlib.SimpleActionServer(
            'i2c_comm', 
            I2CCommAction, 
            self.execute, 
            False
        )
        
        # 启动服务器
        self.server.start()
        
        # 打印启动成功信息
        rospy.loginfo(f"✅ I2C 通信 Action Server 已启动")
        rospy.loginfo(f"   I2C 总线: /dev/i2c-{self.i2c_bus}")
        rospy.loginfo(f"   Action 名称: i2c_comm")
    
    # ==================== I2C 总线初始化函数 ====================
    def init_i2c_bus(self):
        """
        初始化 I2C 总线
        
        功能:
          1. 打开 I2C 总线设备
          2. 更新连接状态标志
          
        异常处理:
          - 捕获 I2C 连接异常并记录错误日志
          
        说明:
          Jetson Nano 上通常有两个 I2C 总线:
          - /dev/i2c-0 (I2C0): 引脚 27 (SDA), 28 (SCL)
          - /dev/i2c-1 (I2C1): 引脚 3 (SDA1), 5 (SCL1)
        """
        try:
            # SMBus() 打开 I2C 总线
            # 参数说明:
            #   - i2c_bus: I2C 总线编号，例如 1 表示 /dev/i2c-1
            self.bus = SMBus(self.i2c_bus)
            
            # 更新连接状态
            self.connected = True
            
            # 记录连接成功日志
            rospy.loginfo(f"✅ I2C 总线已成功打开: /dev/i2c-{self.i2c_bus}")
            
        except FileNotFoundError:
            # I2C 设备不存在
            self.connected = False
            rospy.logerr(f'❌ I2C 设备不存在: /dev/i2c-{self.i2c_bus}')
            rospy.logerr('   提示: 请确保 I2C 已启用，或检查总线编号')
            
        except PermissionError:
            # 权限不足
            self.connected = False
            rospy.logerr(f'❌ 权限不足: 无法访问 /dev/i2c-{self.i2c_bus}')
            rospy.logerr('   提示: 请使用 sudo 运行')
            
        except Exception as e:
            # 其他异常
            self.connected = False
            rospy.logerr(f'❌ I2C 初始化错误: {e}')
    
    # ==================== 扫描 I2C 设备函数 ====================
    def scan_i2c_devices(self):
        """
        扫描 I2C 总线上的设备
        
        功能:
          1. 遍历所有可能的 I2C 地址 (0x03-0x77)
          2. 尝试与每个地址通信
          3. 列出所有响应的设备地址
          
        说明:
          I2C 设备地址范围通常是 0x03 到 0x77
          某些地址是保留的，不用于设备
        """
        if not self.connected:
            rospy.logwarn('⚠️  I2C 未连接，跳过设备扫描')
            return
        
        rospy.loginfo('🔍 正在扫描 I2C 设备...')
        
        devices_found = []
        
        # 遍历 I2C 地址范围 (0x03 - 0x77)
        for addr in range(0x03, 0x78):
            try:
                # 尝试读取一个字节
                # 如果设备存在，会返回数据
                self.bus.read_byte(addr)
                devices_found.append(addr)
                
            except IOError:
                # 设备不存在或无响应
                pass
            
            except Exception as e:
                # 其他错误
                pass
        
        # 显示扫描结果
        if devices_found:
            rospy.loginfo(f'✅ 发现 {len(devices_found)} 个 I2C 设备:')
            for addr in devices_found:
                rospy.loginfo(f'   - 0x{addr:02X} ({addr})')
        else:
            rospy.logwarn('⚠️  未发现任何 I2C 设备')
    
    # ==================== Action 执行回调函数 ====================
    def execute(self, goal):
        """
        执行 Goal 的回调函数
        
        当客户端发送一个 Goal 时，Action Server 会自动调用此函数
        
        参数:
          goal: 客户端发送的目标，包含 I2C 通信参数
                goal.device_address: I2C 设备地址 (0x00-0x7F)
                goal.register_address: 寄存器地址
                goal.data: 要写入的数据
        
        执行流程:
          1. 检查 I2C 连接状态
          2. 从 goal 中获取通信参数
          3. 发送 Feedback 给客户端
          4. 向 I2C 设备写入数据
          5. 从 I2C 设备读取数据
          6. 返回 Result 给客户端
        """
        
        # ==================== 1. 检查 I2C 连接状态 ====================
        if not self.connected:
            rospy.logerr('❌ I2C 未连接，无法执行任务')
            
            # 创建失败结果
            result = I2CCommResult()
            result.received_data = 0
            result.success = False
            
            # 终止 Goal 并返回失败
            self.server.set_aborted(result)
            return
        
        # ==================== 2. 获取通信参数 ====================
        device_addr = goal.device_address      # I2C 设备地址
        register_addr = goal.register_address  # 寄存器地址
        data_to_write = goal.data              # 要写入的数据
        
        rospy.loginfo(f"📥 收到 Goal:")
        rospy.loginfo(f"   设备地址: 0x{device_addr:02X} ({device_addr})")
        rospy.loginfo(f"   寄存器地址: 0x{register_addr:02X} ({register_addr})")
        rospy.loginfo(f"   写入数据: 0x{data_to_write:02X} ({data_to_write})")
        
        # ==================== 3. 发送 Feedback 给客户端 ====================
        feedback = I2CCommFeedback()
        feedback.status = String(data=f"正在写入设备 0x{device_addr:02X}")
        self.server.publish_feedback(feedback)
        
        # ==================== 4. 向 I2C 设备写入数据 ====================
        try:
            # 写入数据到指定寄存器
            # write_byte_data(addr, reg, data) 写入一个字节到寄存器
            if self.enable_echo:
                rospy.loginfo(f"📤 正在写入数据: 0x{data_to_write:02X} -> 寄存器 0x{register_addr:02X}")
            
            self.bus.write_byte_data(device_addr, register_addr, data_to_write)
            
            # 等待设备处理
            time.sleep(0.01)  # 10ms
            
            # ==================== 5. 从 I2C 设备读取数据 ====================
            # read_byte_data(addr, reg) 从寄存器读取一个字节
            if self.enable_echo:
                rospy.loginfo(f"📥 正在读取数据: <- 寄存器 0x{register_addr:02X}")
            
            received_data = self.bus.read_byte_data(device_addr, register_addr)
            
            if self.enable_echo:
                rospy.loginfo(f"✅ 读取数据: 0x{received_data:02X} ({received_data})")
            
            # ==================== 6. 返回成功结果 ====================
            result = I2CCommResult()
            result.received_data = received_data
            result.success = True
            
            self.server.set_succeeded(result)
            rospy.loginfo("✅ I2C 通信成功")
            
        except IOError as e:
            # I/O 错误（设备无响应等）
            rospy.logerr(f'❌ I2C I/O 错误: {e}')
            rospy.logerr('   可能原因: 设备地址错误、设备未连接、设备不支持该操作')
            
            result = I2CCommResult()
            result.received_data = 0
            result.success = False
            
            self.server.set_aborted(result)
            
        except Exception as e:
            # 其他异常
            rospy.logerr(f'❌ I2C 通信错误: {e}')
            
            result = I2CCommResult()
            result.received_data = 0
            result.success = False
            
            self.server.set_aborted(result)
    
    # ==================== 清理函数 ====================
    def cleanup(self):
        """
        清理资源
        
        功能:
          1. 关闭 I2C 总线
          2. 释放系统资源
        """
        if self.bus:
            try:
                self.bus.close()
                rospy.loginfo('I2C 总线已关闭')
            except Exception as e:
                rospy.logerr(f'关闭 I2C 总线时出错: {e}')


# ==================== 主函数 ====================
if __name__ == '__main__':
    """
    主函数 - 程序入口
    
    功能:
      1. 创建 I2CCommServer 实例
      2. 保持节点运行，等待 Goal 请求
      3. 处理异常并优雅退出
    """
    server = None
    try:
        # 创建服务器实例
        # 构造函数中会初始化 ROS 节点和 I2C 总线
        server = I2CCommServer()
        
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