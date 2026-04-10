#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
SPI 通信 Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，接收客户端发送的 SPI 通信请求
  - 使用 spidev 库通过 SPI 总线与设备通信
  - 支持写入数据并读取回环数据
  - 支持参数配置（SPI 总线、设备地址等）
  
硬件连接:
  Jetson Nano SPI0:
    - 引脚 19 (GPIO 10/MOSI1): MOSI 主出从入
    - 引脚 21 (GPIO 9/MISO1): MISO 主入从出
    - 引脚 23 (GPIO 11/SCLK1): SCLK 时钟
    - 引脚 24 (GPIO 8/CE0): CE0 片选 0
    - 引脚 26 (GPIO 7/CE1): CE1 片选 1
    - 设备路径: /dev/spidev0.0 (CE0), /dev/spidev0.1 (CE1)
  
使用方法:
  source install/setup.bash
  sudo rosrun my_action_pkg spi_comm_server.py
  
作者: Jetson Nano
日期: 2026-03-31
"""

import rospy
import actionlib
import spidev
from my_action_pkg.msg import SPICommAction, SPICommFeedback, SPICommResult
from std_msgs.msg import String


class SPICommServer:
    """
    SPI 通信 Action Server 类
    
    职责:
      1. 初始化 ROS 节点和 SPI 总线
      2. 创建 Action Server 接收客户端请求
      3. 执行 SPI 写入和读取操作
      4. 返回操作结果给客户端
    """
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        
        功能:
          1. 初始化 ROS 节点
          2. 从参数服务器读取配置参数
          3. 初始化 SPI 总线
          4. 创建并启动 Action Server
        """
        
        rospy.init_node('spi_comm_server')
        rospy.loginfo("正在初始化 SPI 通信 Action Server...")
        
        self.enable_echo = rospy.get_param('~enable_echo', True)
        
        self.spi = None
        self.connected = False
        
        rospy.loginfo(f"✅ SPI 通信 Action Server 已启动")
        rospy.loginfo(f"   Action 名称: spi_comm")
        
        self.server = actionlib.SimpleActionServer(
            'spi_comm', 
            SPICommAction, 
            self.execute, 
            False
        )
        self.server.start()
    
    def init_spi(self, spi_bus, device_address):
        """
        初始化 SPI 总线
        
        参数:
          spi_bus: SPI 总线编号 (0, 1, 2)
          device_address: 设备地址/片选编号 (0, 1)
        """
        try:
            if self.spi:
                self.spi.close()
            
            self.spi = spidev.SpiDev()
            self.spi.open(spi_bus, device_address)
            
            self.spi.max_speed_hz = 1000000
            self.spi.mode = 0
            self.spi.bits_per_word = 8
            
            self.connected = True
            rospy.loginfo(f"✅ SPI 已成功打开: /dev/spidev{spi_bus}.{device_address}")
            
        except FileNotFoundError:
            self.connected = False
            rospy.logerr(f'❌ SPI 设备不存在: /dev/spidev{spi_bus}.{device_address}')
            
        except PermissionError:
            self.connected = False
            rospy.logerr(f'❌ 权限不足: 无法访问 /dev/spidev{spi_bus}.{device_address}')
            rospy.logerr('   提示: 请使用 sudo 运行')
            
        except Exception as e:
            self.connected = False
            rospy.logerr(f'❌ SPI 初始化错误: {e}')
    
    def execute(self, goal):
        """
        执行 Goal 的回调函数
        
        参数:
          goal: 客户端发送的目标，包含 SPI 通信参数
        """
        spi_bus = goal.spi_bus
        device_address = goal.device_address
        write_data = goal.write_data
        read_after_write = goal.read_after_write
        
        rospy.loginfo(f"📥 收到 Goal:")
        rospy.loginfo(f"   SPI 总线: {spi_bus}")
        rospy.loginfo(f"   设备地址: {device_address}")
        rospy.loginfo(f"   写入数据: 0x{write_data:02X} ({write_data})")
        rospy.loginfo(f"   写后读取: {read_after_write}")
        
        if not self.connected:
            self.init_spi(spi_bus, device_address)
        
        if not self.connected:
            rospy.logerr('❌ SPI 未连接，无法执行任务')
            result = SPICommResult()
            result.received_data = 0
            result.success = False
            self.server.set_aborted(result)
            return
        
        feedback = SPICommFeedback()
        feedback.status = String(data=f"正在写入数据 0x{write_data:02X}")
        feedback.current_data = write_data
        self.server.publish_feedback(feedback)
        
        try:
            if self.enable_echo:
                rospy.loginfo(f"📤 正在写入数据: 0x{write_data:02X}")
            
            received_data = self.spi.xfer2([write_data])
            
            if read_after_write:
                if self.enable_echo:
                    rospy.loginfo(f"📥 读取数据: 0x{received_data[0]:02X} ({received_data[0]})")
                
                feedback = SPICommFeedback()
                feedback.status = String(data=f"读取数据: 0x{received_data[0]:02X}")
                feedback.current_data = received_data[0]
                self.server.publish_feedback(feedback)
                
                result = SPICommResult()
                result.received_data = received_data[0]
                result.success = True
                
                self.server.set_succeeded(result)
                rospy.loginfo("✅ SPI 通信成功")
            else:
                if self.enable_echo:
                    rospy.loginfo(f"✅ 数据写入完成，不读取")
                
                result = SPICommResult()
                result.received_data = 0
                result.success = True
                
                self.server.set_succeeded(result)
                rospy.loginfo("✅ SPI 写入成功")
                
        except Exception as e:
            rospy.logerr(f'❌ SPI 通信错误: {e}')
            result = SPICommResult()
            result.received_data = 0
            result.success = False
            self.server.set_aborted(result)
    
    def cleanup(self):
        """
        清理资源
        """
        if self.spi:
            try:
                self.spi.close()
                rospy.loginfo('SPI 总线已关闭')
            except Exception as e:
                rospy.logerr(f'关闭 SPI 总线时出错: {e}')


if __name__ == '__main__':
    server = None
    try:
        server = SPICommServer()
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
        
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        rospy.logerr(f'❌ 节点运行错误: {e}')
        
    finally:
        if server:
            server.cleanup()