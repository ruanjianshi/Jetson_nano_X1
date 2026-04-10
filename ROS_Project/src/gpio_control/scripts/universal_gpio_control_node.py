#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32, Bool, String
from gpio_control.srv import GPIOControl, GPIOControlResponse
import Jetson.GPIO as GPIO
import time
import ast

class UniversalGPIOControlNode:
    """通用GPIO控制节点 - 支持任意GPIO引脚切换"""
    
    def __init__(self):
        rospy.init_node('universal_gpio_control_node')
        
        # GPIO配置参数
        gpio_pins_param = rospy.get_param('~gpio_pins', "[18, 19, 31, 32, 33, 35, 36, 37, 38, 40]")
        self.default_direction = rospy.get_param('~default_direction', 'out')
        gpio_mode_str = rospy.get_param('~gpio_mode', 'BOARD')
        
        # 安全解析GPIO引脚列表
        try:
            if isinstance(gpio_pins_param, list):
                self.gpio_pins = gpio_pins_param
            elif isinstance(gpio_pins_param, str):
                self.gpio_pins = ast.literal_eval(gpio_pins_param)
            else:
                self.gpio_pins = [18, 19, 31, 32, 33, 35, 36, 37, 38, 40]
        except:
            self.gpio_pins = [18, 19, 31, 32, 33, 35, 36, 37, 38, 40]
        
        # 确保所有引脚都是整数
        self.gpio_pins = [int(pin) for pin in self.gpio_pins]
        
        # GPIO模式配置
        if isinstance(gpio_mode_str, str):
            mode_mapping = {
                'BOARD': GPIO.BOARD,
                'BCM': GPIO.BCM, 
                'TEGRA_SOC': GPIO.TEGRA_SOC
            }
            self.gpio_mode = mode_mapping.get(gpio_mode_str, GPIO.BOARD)
        else:
            self.gpio_mode = int(gpio_mode_str)
        
        # GPIO状态管理
        self.pin_directions = {pin: self.default_direction for pin in self.gpio_pins}
        self.pin_states = {pin: GPIO.LOW for pin in self.gpio_pins}
        
        # 初始化GPIO
        self.init_gpio()
        
        # GPIO功能映射
        self.gpio_functions = self.get_gpio_functions()
        
        # ROS话题和服务
        rospy.Subscriber('gpio/write', Int32, self.write_gpio)
        rospy.Subscriber('gpio/read', Int32, self.read_gpio)
        rospy.Subscriber('gpio/set_direction', Int32, self.set_gpio_direction)
        rospy.Subscriber('gpio/set_output', Int32, self.set_gpio_output)
        rospy.Subscriber('gpio/set_input', Int32, self.set_gpio_input)
        rospy.Subscriber('gpio/toggle', Int32, self.toggle_gpio)
        rospy.Subscriber('gpio/set_all_direction', String, self.set_all_direction)
        
        self.gpio_state_pub = rospy.Publisher('gpio/state', Int32, queue_size=10)
        self.gpio_direction_pub = rospy.Publisher('gpio/direction', Int32, queue_size=10)
        self.gpio_info_pub = rospy.Publisher('gpio/info', String, queue_size=10)
        
        self.control_service = rospy.Service('gpio_control', GPIOControl, self.control_service_callback)
        
        # 定时状态发布
        rospy.Timer(rospy.Duration(0.1), self.publish_gpio_states)
        
        rospy.loginfo('Universal GPIO Control Node initialized')
        self.log_gpio_info()
    
    def get_gpio_functions(self):
        """获取GPIO功能映射"""
        return {
            18: "GPIO18_PWM",
            19: "GPIO19_PWM",
            21: "GPIO21_I2C_SDA",
            22: "GPIO22_I2C_SCL",
            23: "GPIO23_SPI_SCLK",
            24: "GPIO24_SPI_MISO",
            29: "GPIO29_UART_RX",
            31: "GPIO31_GPIO",
            32: "GPIO32_GPIO",
            33: "GPIO33_GPIO",
            35: "GPIO35_GPIO",
            36: "GPIO36_GPIO",
            37: "GPIO37_GPIO",
            38: "GPIO38_GPIO",
            40: "GPIO40_GPIO",
        }
    
    def init_gpio(self):
        """初始化所有GPIO引脚"""
        GPIO.setmode(self.gpio_mode)
        
        for pin in self.gpio_pins:
            try:
                direction = GPIO.OUT if self.pin_directions[pin] == 'out' else GPIO.IN
                GPIO.setup(pin, direction)
                GPIO.output(pin, GPIO.LOW)
                rospy.loginfo(f'GPIO {pin} initialized as {self.pin_directions[pin]}')
            except Exception as e:
                rospy.logerr(f'Failed to initialize GPIO {pin}: {e}')
    
    def write_gpio(self, msg):
        """写入GPIO电平（一次性设置）"""
        if msg.data < 0 or msg.data >= len(self.gpio_pins):
            rospy.logwarn(f'Invalid pin index: {msg.data}')
            return
        
        pin = self.gpio_pins[msg.data]
        
        if self.pin_directions[pin] != 'out':
            rospy.logwarn(f'GPIO {pin} is not in output mode')
            return
        
        try:
            GPIO.output(pin, GPIO.HIGH)
            self.pin_states[pin] = GPIO.HIGH
            rospy.loginfo(f'GPIO {pin} set to HIGH')
        except Exception as e:
            rospy.logerr(f'Failed to write GPIO {pin}: {e}')
    
    def read_gpio(self, msg):
        """读取GPIO状态"""
        if msg.data < 0 or msg.data >= len(self.gpio_pins):
            rospy.logwarn(f'Invalid pin index: {msg.data}')
            return
        
        pin = self.gpio_pins[msg.data]
        
        try:
            state = GPIO.input(pin)
            self.gpio_state_pub.publish(Int32(data=int(state)))
            rospy.loginfo(f'GPIO {pin} state: {state}')
        except Exception as e:
            rospy.logerr(f'Failed to read GPIO {pin}: {e}')
    
    def set_gpio_direction(self, msg):
        """设置单个GPIO方向"""
        pin_index = msg.data
        direction = msg.data  # 0=input, 1=output
        
        if pin_index < 0 or pin_index >= len(self.gpio_pins):
            rospy.logwarn(f'Invalid pin index: {pin_index}')
            return
        
        pin = self.gpio_pins[pin_index]
        direction_str = 'out' if direction == 1 else 'in'
        
        try:
            gpio_direction = GPIO.OUT if direction == 1 else GPIO.IN
            GPIO.setup(pin, gpio_direction)
            self.pin_directions[pin] = direction_str
            rospy.loginfo(f'GPIO {pin} set to {direction_str} mode')
        except Exception as e:
            rospy.logerr(f'Failed to set direction for GPIO {pin}: {e}')
    
    def set_gpio_output(self, msg):
        """设置GPIO为输出"""
        self.set_gpio_direction(msg)
    
    def set_gpio_input(self, msg):
        """设置GPIO为输入"""
        self.set_gpio_direction(Int32(data=msg.data*0))  # 强制设为0（输入）
    
    def toggle_gpio(self, msg):
        """切换GPIO状态"""
        if msg.data < 0 or msg.data >= len(self.gpio_pins):
            rospy.logwarn(f'Invalid pin index: {msg.data}')
            return
        
        pin = self.gpio_pins[msg.data]
        
        if self.pin_directions[pin] != 'out':
            rospy.logwarn(f'GPIO {pin} is not in output mode')
            return
        
        try:
            current_state = GPIO.input(pin)
            new_state = GPIO.HIGH if current_state == GPIO.LOW else GPIO.LOW
            GPIO.output(pin, new_state)
            self.pin_states[pin] = new_state
            rospy.loginfo(f'GPIO {pin} toggled to {"HIGH" if new_state == GPIO.HIGH else "LOW"}')
        except Exception as e:
            rospy.logerr(f'Failed to toggle GPIO {pin}: {e}')
    
    def set_all_direction(self, msg):
        """设置所有GPIO方向"""
        direction_str = msg.data
        direction = GPIO.OUT if direction_str == 'out' else GPIO.IN
        
        for pin_index, pin in enumerate(self.gpio_pins):
            try:
                GPIO.setup(pin, direction)
                self.pin_directions[pin] = direction_str
                rospy.loginfo(f'GPIO {pin} set to {direction_str} mode')
            except Exception as e:
                rospy.logerr(f'Failed to set direction for GPIO {pin}: {e}')
    
    def control_service_callback(self, req):
        """GPIO控制服务回调"""
        pin = req.pin_number
        
        if pin not in self.gpio_pins:
            rospy.logwarn(f'Invalid GPIO pin: {pin}')
            res = GPIOControlResponse()
            res.success = False
            res.message = f'Invalid GPIO pin: {pin}'
            return res
        
        try:
            if self.pin_directions[pin] != 'out':
                GPIO.setup(pin, GPIO.OUT)
                self.pin_directions[pin] = 'out'
            
            GPIO.output(pin, GPIO.HIGH if req.state else GPIO.LOW)
            
            res = GPIOControlResponse()
            res.success = True
            res.message = f'GPIO {pin} set to {"HIGH" if req.state else "low"}'
            return res
            
        except Exception as e:
            res = GPIOControlResponse()
            res.success = False
            res.message = f'GPIO control error: {e}'
            return res
    
    def publish_gpio_states(self, event):
        """发布所有GPIO状态"""
        for pin in self.gpio_pins:
            try:
                state = GPIO.input(pin)
                self.gpio_state_pub.publish(Int32(data=int(state)))
            except Exception as e:
                rospy.logerr(f'Failed to read GPIO {pin}: {e}')
    
    def log_gpio_info(self):
        """记录GPIO信息"""
        rospy.loginfo('=' * 60)
        rospy.loginfo('Universal GPIO Control Node - GPIO Configuration')
        rospy.loginfo('=' * 60)
        rospy.loginfo(f'GPIO Mode: BOARD ({self.gpio_mode})')
        rospy.loginfo(f'Total GPIO Pins: {len(self.gpio_pins)}')
        rospy.loginfo('=' * 60)
        
        for i, pin in enumerate(self.gpio_pins):
            direction = self.pin_directions[pin]
            function = self.gpio_functions.get(pin, "Unknown")
            state = self.pin_states[pin]
            state_str = "HIGH" if state == GPIO.HIGH else "LOW"
            
            rospy.loginfo(f'[{i:2d}] GPIO {pin:2d} | {function:20s} | {direction:8s} | {state_str:4s}')
        
        rospy.loginfo('=' * 60)

if __name__ == '__main__':
    try:
        node = UniversalGPIOControlNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        GPIO.cleanup()
        rospy.loginfo('Universal GPIO Control Node shutdown')