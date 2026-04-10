#!/usr/bin/env python3
"""
Jetson Nano SPI通信节点
支持SPI总线读写操作
"""

import rospy
from std_msgs.msg import Int32, String
import spidev
import threading
import time

class SPICommNode:
    """SPI通信节点类"""
    
    def __init__(self):
        rospy.init_node('spi_comm_node')
        
        # 获取参数
        self.spi_device = rospy.get_param('~spi_device', '/dev/spidev0.0')
        self.spi_mode = rospy.get_param('~spi_mode', 0)  # SPI模式 (0-3)
        self.max_speed = rospy.get_param('~max_speed', 1000000)  # 最大速度 (Hz)
        self.bits_per_word = rospy.get_param('~bits_per_word', 8)  # 每字位数
        self.enable_echo = rospy.get_param('~enable_echo', False)
        
        # SPI对象
        self.spi = None
        self.connected = False
        self.running = True
        
        # 状态
        self.tx_count = 0
        self.rx_count = 0
        self.error_count = 0
        
        # 锁
        self.spi_lock = threading.Lock()
        
        # 初始化SPI
        self.connect_spi()
        
        # ROS话题
        rospy.Subscriber('spi/transfer', String, self.transfer_callback)
        rospy.Subscriber('spi/write', String, self.write_callback)
        rospy.Subscriber('spi/read', Int32, self.read_callback)
        
        self.rx_pub = rospy.Publisher('spi/rx', String, queue_size=10)
        self.status_pub = rospy.Publisher('spi/status', String, queue_size=10)
        
        # 定时器
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        rospy.loginfo('SPI通信节点已启动')
        rospy.loginfo(f'SPI设备: {self.spi_device}')
        rospy.loginfo(f'SPI模式: {self.spi_mode}')
        rospy.loginfo(f'最大速度: {self.max_speed}Hz')
    
    def connect_spi(self):
        """连接SPI设备"""
        with self.spi_lock:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(self.spi_device)
                self.spi.max_speed_hz = self.max_speed
                self.spi.mode = self.spi_mode
                self.spi.bits_per_word = self.bits_per_word
                self.spi.cshigh = 0
                self.spi.cshigh = 0
                self.spi.cs_low = False
                self.spi.cs_high = False
                self.spi.threewire = True
                
                self.connected = True
                rospy.loginfo(f'成功连接到SPI设备: {self.spi_device}')
                rospy.loginfo(f'  模式: {self.spi_mode}, 速度: {self.max_speed}Hz')
                
            except Exception as e:
                self.connected = False
                rospy.logerr(f'SPI连接失败: {e}')
    
    def disconnect_spi(self):
        """断开SPI连接"""
        with self.spi_lock:
            if self.spi:
                self.spi.close()
                self.connected = False
                rospy.loginfo('SPI已断开')
    
    def transfer_callback(self, msg):
        """SPI数据传输（发送和接收）"""
        if not self.connected:
            rospy.logwarn('SPI未连接')
            return
        
        try:
            # 解析要发送的数据
            data = [int(x, 16) for x in msg.data.split()]
            
            with self.spi_lock:
                # SPI传输（同时发送和接收）
                response = self.spi.xfer2(data)
                
                self.tx_count += len(data)
                self.rx_count += len(response)
                
                # 发布接收的数据
                rx_hex = ' '.join(f'0x{b:02X}' for b in response)
                self.rx_pub.publish(String(data=rx_hex))
                
                if self.enable_echo:
                    tx_hex = ' '.join(f'0x{b:02X}' for b in data)
                    rospy.loginfo(f'SPI传输: {tx_hex} -> {rx_hex}')
                    
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'SPI传输错误: {e}')
    
    def write_callback(self, msg):
        """SPI写入操作"""
        if not self.connected:
            rospy.logwarn('SPI未连接')
            return
        
        try:
            # 解析要写入的数据
            data = [int(x, 16) for x in msg.data.split()]
            
            with self.spi_lock:
                # SPI写入
                self.spi.writebytes(data)
                self.tx_count += len(data)
                
                if self.enable_echo:
                    hex_str = ' '.join(f'0x{x:02X}' for x in data)
                    rospy.loginfo(f'SPI写入: {hex_str}')
                    
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'SPI写入错误: {e}')
    
    def read_callback(self, msg):
        """SPI读取操作"""
        if not self.connected:
            rospy.logwarn('SPI未连接')
            return
        
        try:
            length = msg.data
            if length <= 0 or length > 4096:
                rospy.logwarn(f'无效的读取长度: {length}')
                return
            
            with self.spi_lock:
                # 读取指定长度的数据
                dummy = [0x00] * length
                data = self.spi.xfer2(dummy)
                
                self.rx_count += len(data)
                
                # 发布接收的数据
                rx_hex = ' '.join(f'0x{b:02X}' for b in data)
                self.rx_pub.publish(String(data=rx_hex))
                
                if self.enable_echo:
                    rospy.loginfo(f'SPI读取 {length}字节: {rx_hex}')
                    
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'SPI读取错误: {e}')
    
    def publish_status(self, event):
        """发布状态信息"""
        status = {
            'connected': self.connected,
            'device': self.spi_device,
            'mode': self.spi_mode,
            'max_speed': self.max_speed,
            'bits_per_word': self.bits_per_word,
            'tx_count': self.tx_count,
            'rx_count': self.rx_count,
            'error_count': self.error_count
        }
        
        status_str = str(status).replace('\'', '"')
        self.status_pub.publish(String(data=status_str))
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        self.disconnect_spi()
        rospy.loginfo('SPI通信节点已关闭')

def main():
    """主函数"""
    node = None
    try:
        node = SPICommNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo('收到中断信号')
    except Exception as e:
        rospy.logerr(f'节点运行错误: {e}')
    finally:
        if node:
            node.cleanup()

if __name__ == '__main__':
    main()