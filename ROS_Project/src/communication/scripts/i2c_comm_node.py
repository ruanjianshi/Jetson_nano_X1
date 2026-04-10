#!/usr/bin/env python3
"""
Jetson Nano I2C通信节点
支持I2C总线读写操作
"""

import rospy
from std_msgs.msg import Int32, String
import smbus2
import threading
import time

class I2CCommNode:
    """I2C通信节点类"""
    
    def __init__(self):
        rospy.init_node('i2c_comm_node')
        
        # 获取参数
        self.i2c_bus = rospy.get_param('~i2c_bus', 1)  # I2C总线号
        self.device_address = rospy.get_param('~device_address', 0x48)  # 默认I2C地址
        self.auto_scan = rospy.get_param('~auto_scan', False)  # 自动扫描I2C设备
        self.enable_echo = rospy.get_param('~enable_echo', False)
        
        # I2C对象
        self.bus = None
        self.connected = False
        self.running = True
        
        # 状态
        self.tx_count = 0
        self.rx_count = 0
        self.error_count = 0
        
        # 锁
        self.i2c_lock = threading.Lock()
        
        # 初始化I2C
        self.connect_i2c()
        
        # ROS话题
        rospy.Subscriber('i2c/write_byte', Int32, self.write_byte_callback)
        rospy.Subscriber('i2c/write_bytes', String, self.write_bytes_callback)
        rospy.Subscriber('i2c/read_byte', Int32, self.read_byte_callback)
        rospy.Subscriber('i2c/set_address', Int32, self.set_address_callback)
        
        self.rx_pub = rospy.Publisher('i2c/rx_byte', Int32, queue_size=10)
        self.rx_bytes_pub = rospy.Publisher('i2c/rx_bytes', String, queue_size=10)
        self.status_pub = rospy.Publisher('i2c/status', String, queue_size=10)
        
        # 定时器
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        rospy.loginfo('I2C通信节点已启动')
        rospy.loginfo(f'I2C总线: {self.i2c_bus}')
        rospy.loginfo(f'设备地址: 0x{self.device_address:02X}')
    
    def connect_i2c(self):
        """连接I2C总线"""
        with self.i2c_lock:
            try:
                self.bus = smbus2.SMBus(self.i2c_bus)
                self.connected = True
                rospy.loginfo(f'成功连接到I2C总线 {self.i2c_bus}')
                
                # 自动扫描I2C设备
                if self.auto_scan:
                    self.scan_i2c_devices()
                    
            except Exception as e:
                self.connected = False
                rospy.logerr(f'I2C连接失败: {e}')
    
    def disconnect_i2c(self):
        """断开I2C连接"""
        with self.i2c_lock:
            if self.bus:
                self.bus.close()
                self.connected = False
                rospy.loginfo('I2C已断开')
    
    def scan_i2c_devices(self):
        """扫描I2C总线上的设备"""
        rospy.loginfo('扫描I2C设备...')
        
        devices = []
        for addr in range(0x03, 0x78):  # I2C地址范围
            try:
                self.bus.write_byte(addr, 0)
                devices.append(addr)
                rospy.loginfo(f'  发现设备: 0x{addr:02X}')
            except:
                pass
        
        if devices:
            rospy.loginfo(f'总共发现 {len(devices)} 个I2C设备')
        else:
            rospy.logwarn('未发现I2C设备')
        
        return devices
    
    def write_byte_callback(self, msg):
        """写入单个字节"""
        if not self.connected:
            rospy.logwarn('I2C未连接')
            return
        
        try:
            with self.i2c_lock:
                self.bus.write_byte(self.device_address, msg.data)
                self.tx_count += 1
                
                if self.enable_echo:
                    rospy.loginfo(f'写入字节: 0x{msg.data:02X}')
                    
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'I2C写入错误: {e}')
    
    def write_bytes_callback(self, msg):
        """写入多个字节"""
        if not self.connected:
            rospy.logwarn('I2C未连接')
            return
        
        try:
            # 解析字节序列
            data_list = [int(x, 16) for x in msg.data.split()]
            
            with self.i2c_lock:
                if len(data_list) == 1:
                    self.bus.write_byte(self.device_address, data_list[0])
                else:
                    self.bus.write_i2c_block_data(self.device_address, data_list)
                
                self.tx_count += len(data_list)
                
                if self.enable_echo:
                    hex_str = ' '.join(f'0x{x:02X}' for x in data_list)
                    rospy.loginfo(f'写入字节: {hex_str}')
                    
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'I2C写入错误: {e}')
    
    def read_byte_callback(self, msg):
        """读取单个字节"""
        if not self.connected:
            rospy.logwarn('I2C未连接')
            return
        
        try:
            with self.i2c_lock:
                if msg.data >= 0:
                    # 从指定寄存器读取
                    data = self.bus.read_byte_data(self.device_address, msg.data)
                else:
                    # 读取当前字节
                    data = self.bus.read_byte(self.device_address)
                
                self.rx_count += 1
                self.rx_pub.publish(Int32(data=data))
                
                if self.enable_echo:
                    rospy.loginfo(f'读取字节: 0x{data:02X}')
                    
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'I2C读取错误: {e}')
    
    def set_address_callback(self, msg):
        """设置I2C设备地址"""
        self.device_address = msg.data
        rospy.loginfo(f'I2C设备地址已设置为: 0x{msg.data:02X}')
    
    def publish_status(self, event):
        """发布状态信息"""
        status = {
            'connected': self.connected,
            'bus': self.i2c_bus,
            'device_address': f'0x{self.device_address:02X}',
            'tx_count': self.tx_count,
            'rx_count': self.rx_count,
            'error_count': self.error_count
        }
        
        status_str = str(status).replace('\'', '"')
        self.status_pub.publish(String(data=status_str))
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        self.disconnect_i2c()
        rospy.loginfo('I2C通信节点已关闭')

def main():
    """主函数"""
    node = None
    try:
        node = I2CCommNode()
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