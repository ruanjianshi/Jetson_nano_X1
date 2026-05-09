#!/usr/bin/env python3
"""
Jetson Nano 串口通信节点
支持多种串口配置和自动重连
"""

import rospy
from std_msgs.msg import String
import serial
import serial.tools.list_ports
import threading
import time

class SerialCommNode:
    """串口通信节点类"""
    
    def __init__(self):
        rospy.init_node('serial_comm_node')
        
        # 获取参数
        self.serial_port = rospy.get_param('~serial_port', '/dev/ttyTHS1')
        self.baud_rate = rospy.get_param('~baud_rate', 115200)
        self.timeout = rospy.get_param('~timeout', 1.0)
        self.auto_reconnect = rospy.get_param('~auto_reconnect', True)
        self.reconnect_interval = rospy.get_param('~reconnect_interval', 2.0)
        self.enable_echo = rospy.get_param('~enable_echo', False)
        
        # 串口对象
        self.ser = None
        self.connected = False
        self.running = True
        
        # 状态
        self.tx_count = 0
        self.rx_count = 0
        self.error_count = 0
        
        # 锁
        self.serial_lock = threading.Lock()
        
        # 自动检测串口
        if self.serial_port == 'auto':
            self.serial_port = self.detect_serial_port()
            if self.serial_port:
                rospy.loginfo(f'自动检测到串口: {self.serial_port}')
            else:
                rospy.logwarn('未检测到可用的串口')
        
        # 初始化串口
        self.connect_serial()
        
        # ROS话题
        rospy.Subscriber('serial/tx', String, self.tx_callback, queue_size=10)
        self.rx_pub = rospy.Publisher('serial/rx', String, queue_size=10)
        self.status_pub = rospy.Publisher('serial/status', String, queue_size=10)
        
        # 定时器
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        self.read_timer = rospy.Timer(rospy.Duration(0.01), self.rx_read)
        
        # 重连线程
        if self.auto_reconnect and not self.connected:
            self.reconnect_thread = threading.Thread(target=self.reconnect_loop, daemon=True)
            self.reconnect_thread.start()
        
        rospy.loginfo('串口通信节点已启动')
        rospy.loginfo(f'串口配置: {self.serial_port}@{self.baud_rate}bps')
    
    def detect_serial_port(self):
        """自动检测可用的串口"""
        ports = serial.tools.list_ports.comports()
        
        # 优先级顺序
        preferred_ports = ['/dev/ttyTHS1', '/dev/ttyTHS2', '/dev/ttyUSB0', '/dev/ttyUSB1']
        
        # 检查首选端口
        for port in preferred_ports:
            if any(p.device == port for p in ports):
                return port
        
        # 如果没有首选端口，返回第一个可用端口
        if ports:
            return ports[0].device
        
        return None
    
    def connect_serial(self):
        """连接串口"""
        with self.serial_lock:
            if self.ser and self.ser.is_open:
                self.ser.close()
            
            try:
                self.ser = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.baud_rate,
                    timeout=self.timeout,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                if self.ser.is_open:
                    self.connected = True
                    rospy.loginfo(f'成功连接到串口: {self.serial_port}')
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                else:
                    self.connected = False
                    rospy.logerr('串口连接失败')
                    
            except serial.SerialException as e:
                self.connected = False
                rospy.logerr(f'串口连接异常: {e}')
            except Exception as e:
                self.connected = False
                rospy.logerr(f'未知错误: {e}')
    
    def disconnect_serial(self):
        """断开串口连接"""
        with self.serial_lock:
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.connected = False
                rospy.loginfo('串口已断开')
    
    def reconnect_loop(self):
        """重连循环"""
        while self.running and not self.connected:
            rospy.loginfo(f'尝试重新连接串口: {self.serial_port}')
            self.connect_serial()
            
            if not self.connected:
                rospy.loginfo(f'等待 {self.reconnect_interval} 秒后重试...')
                time.sleep(self.reconnect_interval)
    
    def tx_callback(self, msg):
        """发送回调函数"""
        if not self.connected:
            rospy.logwarn('串口未连接，无法发送数据')
            return
        
        try:
            with self.serial_lock:
                if self.ser and self.ser.is_open:
                    data = msg.data.encode('utf-8', errors='ignore')
                    self.ser.write(data)
                    self.tx_count += 1
                    
                    if self.enable_echo:
                        rospy.loginfo(f'发送 [{self.tx_count}]: {msg.data}')
                    
        except serial.SerialException as e:
            self.error_count += 1
            rospy.logerr(f'串口发送错误: {e}')
            self.handle_disconnect()
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'发送异常: {e}')
    
    def rx_read(self, event):
        """读取串口数据"""
        if not self.connected:
            return
        
        try:
            with self.serial_lock:
                if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    
                    try:
                        decoded = data.decode('utf-8', errors='ignore')
                        if decoded.strip():
                            self.rx_pub.publish(String(data=decoded))
                            self.rx_count += 1
                            
                            if self.enable_echo:
                                rospy.loginfo(f'接收 [{self.rx_count}]: {decoded.strip()}')
                    except UnicodeDecodeError:
                        rospy.logwarn(f'接收到的数据无法解码: {data.hex()}')
                        
        except serial.SerialException as e:
            self.error_count += 1
            rospy.logerr(f'串口读取错误: {e}')
            self.handle_disconnect()
        except Exception as e:
            self.error_count += 1
            rospy.logerr(f'读取异常: {e}')
    
    def handle_disconnect(self):
        """处理断开连接"""
        self.connected = False
        rospy.logwarn('串口连接断开')
        
        if self.auto_reconnect:
            if not hasattr(self, 'reconnect_thread') or not self.reconnect_thread.is_alive():
                self.reconnect_thread = threading.Thread(target=self.reconnect_loop, daemon=True)
                self.reconnect_thread.start()
    
    def publish_status(self, event):
        """发布状态信息"""
        status = {
            'connected': self.connected,
            'port': self.serial_port if self.connected else 'disconnected',
            'baud_rate': self.baud_rate,
            'tx_count': self.tx_count,
            'rx_count': self.rx_count,
            'error_count': self.error_count
        }
        
        status_str = str(status).replace('\'', '"')
        self.status_pub.publish(String(data=status_str))
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        self.disconnect_serial()
        rospy.loginfo('串口通信节点已关闭')

def main():
    """主函数"""
    node = None
    try:
        node = SerialCommNode()
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