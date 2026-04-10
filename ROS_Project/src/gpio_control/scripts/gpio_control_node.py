#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32, Bool
from gpio_control.srv import GPIOControl
import time

class GPIOControlNodePython:
    def __init__(self):
        rospy.init_node('gpio_control_node')
        
        # GPIO配置参数
        self.gpio_pins = rospy.get_param('~gpio_pins', [21, 22, 23, 24, 27, 28, 29, 30])
        self.pin_direction = rospy.get_param('~pin_direction', 'out')
        
        # GPIO功能分配
        self.gpio_mapping = {
            21: "LED_Green",
            22: "LED_Red", 
            23: "LED_Yellow",
            24: "Device_Relay1",
            27: "Device_Relay2",
            28: "Sensor_Input",
            29: "System_Reset",
            30: "Status_Indicator"
        }
        
        # 初始化GPIO
        self.init_gpio()
        
        # ROS话题和服务
        rospy.Subscriber('gpio/write', Int32, self.write_callback)
        rospy.Subscriber('gpio/set_direction', Int32, self.set_direction_callback)
        rospy.Subscriber('gpio/set_mode', Bool, self.set_mode_callback)
        
        self.state_pub = rospy.Publisher('gpio/state', Int32, queue_size=10)
        self.status_pub = rospy.Publisher('gpio/status', Bool, queue_size=10)
        
        self.control_service = rospy.Service('gpio_control', GPIOControl, self.control_service_callback)
        
        # 定时读取GPIO状态
        rospy.Timer(rospy.Duration(0.1), self.read_gpio_state)
        
        rospy.loginfo('GPIO Control Node initialized')
        self.log_gpio_info()
    
    def init_gpio(self):
        """初始化GPIO引脚"""
        for pin in self.gpio_pins:
            try:
                with open(f'/sys/class/gpio/export', 'w') as f:
                    f.write(str(pin))
                time.sleep(0.1)
                
                direction_file = f'/sys/class/gpio/gpio{pin}/direction'
                with open(direction_file, 'w') as f:
                    f.write(self.pin_direction)
                    
                rospy.loginfo(f'GPIO {pin} ({self.gpio_mapping.get(pin, "Unknown")}) initialized as {self.pin_direction}')
                
            except Exception as e:
                rospy.logerr(f'Failed to initialize GPIO {pin}: {e}')
    
    def write_callback(self, msg):
        """写入GPIO电平"""
        pin_index = msg.data
        
        if pin_index < 0 or pin_index >= len(self.gpio_pins):
            rospy.logwarn(f'Invalid pin index: {pin_index}')
            return
        
        pin = self.gpio_pins[pin_index]
        
        if self.pin_direction != 'out':
            rospy.logwarn(f'GPIO {pin} is not in output mode')
            return
        
        try:
            # 先设置高电平
            with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                f.write('1')
            
            # 短暂延迟
            time.sleep(0.05)
            
            # 设置回低电平
            with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                f.write('0')
                
            rospy.loginfo(f'GPIO {pin} ({self.gpio_mapping.get(pin, "Unknown")}) pulse sent')
            
        except Exception as e:
            rospy.logerr(f'Failed to write GPIO {pin}: {e}')
    
    def read_gpio_state(self, event):
        """读取GPIO状态"""
        for i, pin in enumerate(self.gpio_pins):
            try:
                value_file = f'/sys/class/gpio/gpio{pin}/value'
                with open(value_file, 'r') as f:
                    value = int(f.read().strip())
                    self.state_pub.publish(Int32(data=value))
                    
            except Exception as e:
                rospy.logerr(f'Failed to read GPIO {pin}: {e}')
    
    def control_service_callback(self, req, res):
        """GPIO控制服务回调"""
        pin = req.pin_number
        
        if pin not in self.gpio_pins:
            rospy.logwarn(f'Invalid GPIO pin: {pin}')
            res.success = False
            res.message = f'Invalid GPIO pin: {pin}'
            return True
        
        try:
            with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                f.write('1' if req.state else '0')
            
            res.success = True
            res.message = f'GPIO {pin} set to {"high" if req.state else "low"}'
            
        except Exception as e:
            res.success = False
            res.message = f'GPIO control error: {e}'
        
        return True
    
    def set_direction_callback(self, msg):
        """设置GPIO方向"""
        if msg.data == 0:
            direction = 'in'
        elif msg.data == 1:
            direction = 'out'
        else:
            rospy.logwarn(f'Invalid direction: {msg.data}')
            return
        
        for pin in self.gpio_pins:
            try:
                direction_file = f'/sys/class/gpio/gpio{pin}/direction'
                with open(direction_file, 'w') as f:
                    f.write(direction)
                rospy.loginfo(f'GPIO {pin} set to {direction}')
                
            except Exception as e:
                rospy.logerr(f'Failed to set direction for GPIO {pin}: {e}')
    
    def set_mode_callback(self, msg):
        """设置GPIO模式（用于特殊功能）"""
        mode = 'out' if msg.data else 'in'
        rospy.loginfo(f'Setting all GPIOs to {mode} mode')
        
        for pin in self.gpio_pins:
            try:
                direction_file = f'/sys/class/gpio/gpio{pin}/direction'
                with open(direction_file, 'w') as f:
                    f.write(mode)
                    
            except Exception as e:
                rospy.logerr(f'Failed to set mode for GPIO {pin}: {e}')
    
    def cleanup(self):
        """清理GPIO资源"""
        for pin in self.gpio_pins:
            try:
                with open('/sys/class/gpio/unexport', 'w') as f:
                    f.write(str(pin))
            except:
                pass
    
    def log_gpio_info(self):
        """记录GPIO信息"""
        rospy.loginfo('=' * 50)
        rospy.loginfo('GPIO Configuration Summary')
        rospy.loginfo('=' * 50)
        for pin in self.gpio_pins:
            direction_file = f'/sys/class/gpio/gpio{pin}/direction'
            with open(direction_file, 'r') as f:
                current_direction = f.read().strip()
            rospy.loginfo(f'  GPIO {pin:2d} | {self.gpio_mapping.get(pin, "Unknown"):20s} | {current_direction:10s}')
        rospy.loginfo('=' * 50)

if __name__ == '__main__':
    try:
        node = GPIOControlNodePython()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        node.cleanup()
        rospy.loginfo('GPIO Control Node shutdown')