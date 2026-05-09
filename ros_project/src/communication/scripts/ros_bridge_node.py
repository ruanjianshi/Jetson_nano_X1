#!/usr/bin/env python3
import rospy
from std_msgs.msg import String, Int32

class ROSBridgeNodePython:
    def __init__(self):
        rospy.init_node('ros_bridge_node_python')
        
        rospy.Subscriber('bridge/input', String, self.bridge_callback)
        self.output_pub = rospy.Publisher('bridge/output', Int32, queue_size=10)
        
        rospy.loginfo('ROS Bridge Node started')
    
    def bridge_callback(self, msg):
        try:
            value = int(msg.data)
            self.output_pub.publish(Int32(data=value))
        except ValueError:
            rospy.logwarn('Invalid input value')

if __name__ == '__main__':
    node = ROSBridgeNodePython()
    rospy.spin()