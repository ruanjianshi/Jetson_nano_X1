#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

camera_publisher.py - Jetson side camera image publisher

Opens USB/CSI camera via OpenCV cv2.VideoCapture(),
encodes frames as JPEG, publishes CompressedImage to /camera/image/compressed.
Choose low quality (50-70) to save WiFi bandwidth.

Topics:
  Publish: /camera/image/compressed (sensor_msgs/CompressedImage, JPEG)

Usage:
  rosrun distributed_comm camera_publisher.py _width:=640 _height:=480 _fps:=15 _quality:=60

Params:
  _width         (int, 640)   Image width
  _height        (int, 480)   Image height
  _fps           (int, 15)    Capture framerate
  _quality       (int, 70)    JPEG encode quality 1-100
  _camera_index  (int, 0)     /dev/videoN device index
  _flip_method   (int, 0)     0=off, 1=horizontal, -1=vertical
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

import rospy
import cv2
import numpy as np
from sensor_msgs.msg import CompressedImage


class CameraPublisher:
    def __init__(self):
        rospy.init_node('camera_publisher', anonymous=True)

        # @brief Capture parameters
        self.width        = rospy.get_param('~width', 640)
        self.height       = rospy.get_param('~height', 480)
        self.fps          = rospy.get_param('~fps', 15)
        self.quality      = rospy.get_param('~quality', 70)
        self.camera_index = rospy.get_param('~camera_index', 0)
        self.flip_method  = rospy.get_param('~flip_method', 0)

        # @brief ROS publisher: compressed image topic
        self.pub = rospy.Publisher('/camera/image/compressed', CompressedImage, queue_size=2)
        self.frame_count = 0
        self.last_print = rospy.Time.now()

        # @brief Open camera device
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            rospy.logerr("Failed to open camera /dev/video{}".format(self.camera_index))
            raise RuntimeError("Camera not available")

        # @brief Set capture resolution and fps (best-effort, camera may override)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        actual_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        rospy.loginfo("[Camera] {}x{} @ {}Hz -> /camera/image/compressed (q={})".format(
            int(actual_w), int(actual_h), self.fps, self.quality))

    def run(self):
        """Main capture loop: read frame -> JPEG encode -> publish"""
        r = rospy.Rate(self.fps)

        while not rospy.is_shutdown():
            ret, frame = self.cap.read()
            if not ret:
                rospy.logwarn("Camera read failed, retrying...")
                rospy.sleep(0.1)
                continue

            # @brief Optional flip (e.g., upside-down USB camera)
            if self.flip_method != 0:
                frame = cv2.flip(frame, self.flip_method)

            # @brief Encode to JPEG for low-bandwidth WiFi transmission
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            _, jpeg = cv2.imencode('.jpg', frame, encode_param)

            msg = CompressedImage()
            msg.header.stamp = rospy.Time.now()
            msg.header.frame_id = "camera"
            msg.format = "jpeg"
            msg.data = np.array(jpeg).tobytes()

            self.pub.publish(msg)
            self.frame_count += 1

            # @brief Print stats every 5 seconds (frame count + KB per frame)
            now = rospy.Time.now()
            if (now - self.last_print).to_sec() >= 5.0:
                rospy.loginfo("[Camera] published {} frames | {:.0f} KB/frame".format(
                    self.frame_count, len(msg.data) / 1024.0))
                self.last_print = now

            r.sleep()

        self.cap.release()


if __name__ == '__main__':
    try:
        CameraPublisher().run()
    except rospy.ROSInterruptException:
        pass
