#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32, Bool
from gpio_control.srv import GPIOControl
import Jetson.GPIO as GPIO
import time
import ast

class GPIOControlNodeJetson:
    def __init__(self):
        rospy.init_node('gpio_control_node')
        
        # GPIO配置参数 - 修复参数解析问题
        gpio_pins_param = rospy.get_param('~gpio_pins', "[18, 19, 21, 22, 23, 24, 29]")
        self.pin_direction = rospy.get_param('~pin_direction', 'out')
        gpio_mode_str = rospy.get_param('~gpio_mode', 'BOARD')
        
        # 安全地解析GPIO引脚列表
        try:
            if isinstance(gpio_pins_param, list):
                self.gpio_pins = gpio_pins_param
            elif isinstance(gpio_pins_param, str):
                self.gpio_pins = ast.literal_eval(gpio_pins_param)
            else:
                self.gpio_pins = [18, 19, 21, 22, 23, 24, 29]
        except:
            self.gpio_pins = [18, 19, 21, 22, 23, 24, 29]
        
        # 确保所有引脚都是整数
        self.gpio_pins = [int(pin) for pin in self.gpio_pins]
        
        # 将字符串转换为GPIO常量
        if isinstance(gpio_mode_str, str):
            mode_mapping = {
                'BOARD': GPIO.BOARD,
                'BCM': GPIO.BCM, 
                'TEGRA_SOC': GPIO.TEGRA_SOC
            }
            self.gpio_mode = mode_mapping.get(gpio_mode_str, GPIO.BOARD)
        else:
            self.gpio_mode = int(gpio_mode_str)
        
        # GPIO功能分配
        self.gpio_mapping = {
            18: "GPIO18_PWM",
            19: "GPIO19_PWM",
            21: "GPIO21_I2C_SDA",
            22: "GPIO22_I2C_SCL",
            23: "GPIO23_SPI_SCLK",
            24: "GPIO24_SPI_MISO",
            29: "GPIO29_UART_RX"
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
        
        rospy.loginfo('GPIO Control Node initialized with Jetson.GPIO')
        self.log_gpio_info()
    
    def init_gpio(self):
        """初始化GPIO引脚"""
        GPIO.setmode(self.gpio_mode)
        
        for pin in self.gpio_pins:
            try:
                if self.pin_direction == 'out':
                    GPIO.setup(pin, GPIO.OUT)
                else:
                    GPIO.setup(pin, GPIO.IN)
                    
                rospy.loginfo(f'GPIO {pin} ({self.gpio_mapping.get(pin, "Unknown")}) initialized as {self.pin_direction}')
                
            except Exception as e:
                rospy.logwarn(f'Failed to initialize GPIO {pin}: {e}')
    
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
            GPIO.output(pin, GPIO.HIGH)
            
            # 短暂延迟
            time.sleep(0.05)
            
            # 设置回低电平
            GPIO.output(pin, GPIO.LOW)
                
            rospy.loginfo(f'GPIO {pin} ({self.gpio_mapping.get(pin, "Unknown")}) pulse sent')
            
        except Exception as e:
            rospy.logerr(f'Failed to write GPIO {pin}: {e}')
    
    def read_gpio_state(self, event):
        """读取GPIO状态"""
        for i, pin in enumerate(self.gpio_pins):
            try:
                state = GPIO.input(pin)
                self.state_pub.publish(Int32(data=int(state)))
                    
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
            GPIO.output(pin, GPIO.HIGH if req.state else GPIO.LOW)
            
            res.success = True
            res.message = f'GPIO {pin} set to {"high" if req.state else "low"}'
            
        except Exception as e:
            res.success = False
            res.message = f'GPIO control error: {e}'
        
        return True
    
    def set_direction_callback(self, msg):
        """设置GPIO方向"""
        if msg.data == 0:
            direction = GPIO.IN
        elif msg.data == 1:
            direction = GPIO.OUT
        else:
            rospy.logwarn(f'Invalid direction: {msg.data}')
            return
        
        for pin in self.gpio_pins:
            try:
                GPIO.setup(pin, direction)
                rospy.loginfo(f'GPIO {pin} set to {"input" if direction == GPIO.IN else "output"}')
                
            except Exception as e:
                rospy.logerr(f'Failed to set direction for GPIO {pin}: {e}')
    
    def set_mode_callback(self, msg):
        """设置GPIO模式（用于特殊功能）"""
        mode = GPIO.OUT if msg.data else GPIO.IN
        rospy.loginfo(f'Setting all GPIOs to {"output" if mode == GPIO.OUT else "input"} mode')
        
        for pin in self.gpio_pins:
            try:
                GPIO.setup(pin, mode)
                    
            except Exception as e:
                rospy.logerr(f'Failed to set mode for GPIO {pin}: {e}')
    
    def cleanup(self):
        """清理GPIO资源"""
        GPIO.cleanup()
    
    def log_gpio_info(self):
        """记录GPIO信息"""
        rospy.loginfo('=' * 50)
        rospy.loginfo('GPIO Configuration Summary')
        rospy.loginfo('=' * 50)
        rospy.loginfo('GPIO Mode: BOARD ({})'.format(self.gpio_mode))
        rospy.loginfo('GPIO Direction: {}'.format(self.pin_direction))
        rospy.loginfo('Available Pins: {}'.format(len(self.gpio_pins)))
        rospy.loginfo('=' * 50)
        for pin in self.gpio_pins:
            pin_str = str(pin)
            mapping_str = self.gpio_mapping.get(pin, "Unknown")
            rospy.loginfo('  GPIO {} | {} | {}'.format(pin_str, mapping_str, self.pin_direction))
        rospy.loginfo('=' * 50)

if __name__ == '__main__':
    node = None
    try:
        node = GPIOControlNodeJetson()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        if node:
            node.cleanup()
        rospy.loginfo('GPIO Control Node shutdown')