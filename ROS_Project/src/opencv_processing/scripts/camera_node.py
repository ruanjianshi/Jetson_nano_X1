#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge

class CameraNode:
    def __init__(self):
        rospy.init_node('camera_node')
        
        self.camera_id = rospy.get_param('~camera_id', 0)
        self.bridge = CvBridge()
        
        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.image_pub = rospy.Publisher('camera/image_raw', Image, queue_size=10)
        
        rospy.Timer(rospy.Duration(0.033), self.publish_image)
        
        rospy.loginfo(f'Camera Node started on device {self.camera_id}')
    
    def publish_image(self, event):
        ret, frame = self.cap.read()
        if ret:
            ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.image_pub.publish(ros_image)
    
    def cleanup(self):
        self.cap.release()

if __name__ == '__main__':
    node = CameraNode()
    rospy.spin()
    node.cleanup()