#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge
import numpy as np

class ImageProcessorNode:
    def __init__(self):
        rospy.init_node('image_processor_node')
        
        self.bridge = CvBridge()
        self.processed_pub = rospy.Publisher('image/processed', Image, queue_size=10)
        self.contours_pub = rospy.Publisher('image/contours', Image, queue_size=10)
        
        rospy.Subscriber('camera/image_raw', Image, self.image_callback)
        
        rospy.loginfo('Image Processor Node started')
    
    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            contour_image = cv_image.copy()
            cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)
            
            processed_ros = self.bridge.cv2_to_imgmsg(edges, encoding='mono8')
            contours_ros = self.bridge.cv2_to_imgmsg(contour_image, encoding='bgr8')
            
            self.processed_pub.publish(processed_ros)
            self.contours_pub.publish(contours_ros)
            
        except Exception as e:
            rospy.logerr(f'Image processing error: {e}')

if __name__ == '__main__':
    node = ImageProcessorNode()
    rospy.spin()