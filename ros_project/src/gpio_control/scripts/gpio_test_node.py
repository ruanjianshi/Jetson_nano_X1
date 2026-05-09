#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32, Bool
import time

class GPIOControlNode:
    def __init__(self):
        rospy.init_node('gpio_control_node_test')
        
        self.gpio_pins = rospy.get_param('~gpio_pins', [21, 22, 23, 24])
        self.pin_direction = rospy.get_param('~pin_direction', 'out')
        
        self.init_gpio()
        
        # 测试相关话题
        rospy.Subscriber('gpio/test_write', Int32, self.test_write_callback)
        rospy.Subscriber('gpio/test_read', Bool, self.test_read_callback)
        
        self.test_result_pub = rospy.Publisher('gpio/test_result', Int32, queue_size=10)
        
        self.test_mode = rospy.get_param('~test_mode', False)
        
        if self.test_mode:
            self.test_gpio_all()
        
        rospy.loginfo('GPIO Test Node initialized')
    
    def init_gpio(self):
        """初始化GPIO引脚"""
        for pin in self.gpio_pins:
            try:
                with open('/sys/class/gpio/export', 'w') as f:
                    f.write(str(pin))
                time.sleep(0.1)
                
                direction_file = f'/sys/class/gpio/gpio{pin}/direction'
                with open(direction_file, 'w') as f:
                    f.write(self.pin_direction)
                    
                rospy.loginfo(f'GPIO {pin} initialized as {self.pin_direction}')
                
            except Exception as e:
                rospy.logerr(f'Failed to initialize GPIO {pin}: {e}')
    
    def test_write_callback(self, msg):
        """测试GPIO写入"""
        pin_index = msg.data
        
        if pin_index < 0 or pin_index >= len(self.gpio_pins):
            rospy.logwarn(f'Invalid pin index: {pin_index}')
            return
        
        pin = self.gpio_pins[pin_index]
        
        try:
            # 设置高电平
            with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                f.write('1')
            
            time.sleep(0.05)
            
            # 设置低电平
            with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                f.write('0')
                
            rospy.loginfo(f'GPIO {pin} pulse completed')
            self.test_result_pub.publish(Int32(data=pin))
            
        except Exception as e:
            rospy.logerr(f'GPIO write test failed: {e}')
            self.test_result_pub.publish(Int32(data=-1))
    
    def test_read_callback(self, msg):
        """测试GPIO读取"""
        results = []
        
        for pin in self.gpio_pins:
            try:
                value_file = f'/sys/class/gpio/gpio{pin}/value'
                with open(value_file, 'r') as f:
                    value = int(f.read().strip())
                    results.append((pin, value))
                    
            except Exception as e:
                rospy.logerr(f'GPIO read test failed for pin {pin}: {e}')
                results.append((pin, -1))
        
        # 发布读取结果
        for pin, value in results:
            self.test_result_pub.publish(Int32(data=pin * 1000 + value))
    
    def test_gpio_all(self):
        """测试所有GPIO"""
        rospy.loginfo('Starting GPIO comprehensive test...')
        
        for pin in self.gpio_pins:
            rospy.loginfo(f'Testing GPIO {pin}...')
            
            # 测试写入
            for i in range(5):
                try:
                    with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                        f.write('1')
                    time.sleep(0.01)
                    
                    with open(f'/sys/class/gpio/gpio{pin}/value', 'w') as f:
                        f.write('0')
                    time.sleep(0.01)
                    
                except Exception as e:
                    rospy.logerr(f'GPIO {pin} test failed at iteration {i}: {e}')
            
            rospy.loginfo(f'GPIO {pin} test completed')
        
        rospy.loginfo('GPIO comprehensive test finished')
    
    def cleanup(self):
        """清理GPIO"""
        for pin in self.gpio_pins:
            try:
                with open('/sys/class/gpio/unexport', 'w') as f:
                    f.write(str(pin))
            except:
                pass

if __name__ == '__main__':
    try:
        node = GPIOControlNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        node.cleanup()
        rospy.loginfo('GPIO Test Node shutdown')