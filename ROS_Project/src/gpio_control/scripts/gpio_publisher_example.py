#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32
import time

class GPIOPublisher:
    def __init__(self):
        rospy.init_node('gpio_publisher_example')
        
        self.gpio_write_pub = rospy.Publisher('gpio/write', Int32, queue_size=10)
        rospy.sleep(1)  # 等待发布者连接
        
        rospy.loginfo('GPIO Publisher Example Node started')
        self.publish_gpio_commands()
    
    def publish_gpio_commands(self):
        """发布GPIO控制命令"""
        rospy.loginfo('Publishing GPIO commands...')
        
        # 模拟控制不同的GPIO引脚
        pin_sequence = [0, 1, 2, 3, 4, 5, 6, 7]  # GPIO索引
        
        for pin_index in pin_sequence:
            msg = Int32()
            msg.data = pin_index
            self.gpio_write_pub.publish(msg)
            rospy.loginfo(f'Sent command to GPIO pin index {pin_index}')
            time.sleep(1)  # 每个引脚间隔1秒
        
        rospy.loginfo('GPIO commands completed')

if __name__ == '__main__':
    try:
        publisher = GPIOPublisher()
    except rospy.ROSInterruptException:
        pass