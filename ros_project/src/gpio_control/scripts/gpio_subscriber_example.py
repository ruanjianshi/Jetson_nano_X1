#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32, Bool
import time

class GPIOSubscriber:
    def __init__(self):
        rospy.init_node('gpio_subscriber_example')
        
        # 订阅GPIO状态话题
        rospy.Subscriber('gpio/state', Int32, self.state_callback)
        
        # 订阅GPIO状态指示话题
        rospy.Subscriber('gpio/status', Bool, self.status_callback)
        
        # 发布GPIO控制命令
        self.gpio_write_pub = rospy.Publisher('gpio/write', Int32, queue_size=10)
        
        rospy.sleep(1)  # 等待连接
        
        rospy.loginfo('GPIO Subscriber Example Node started')
        rospy.loginfo('Listening to GPIO state changes...')
        
        # 发送一些测试命令
        self.send_test_commands()
        
        rospy.spin()
    
    def state_callback(self, msg):
        """GPIO状态回调"""
        rospy.loginfo(f'GPIO State received: {msg.data}')
    
    def status_callback(self, msg):
        """GPIO状态指示回调"""
        rospy.loginfo(f'GPIO Status: {"Active" if msg.data else "Inactive"}')
    
    def send_test_commands(self):
        """发送测试命令"""
        rospy.loginfo('Sending test commands...')
        
        for i in range(3):
            msg = Int32()
            msg.data = i
            self.gpio_write_pub.publish(msg)
            rospy.loginfo(f'Sent test command {i}')
            time.sleep(0.5)
        
        rospy.loginfo('Test commands sent')

if __name__ == '__main__':
    try:
        subscriber = GPIOSubscriber()
    except rospy.ROSInterruptException:
        pass