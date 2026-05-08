#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

jetson_display.py - Jetson side: receive YOLO results from PC and display

Subscribes to:
  /yolo/result_image/compressed  -- annotated image from PC
  /yolo/detections               -- JSON detection list from PC

Auto-detects display: GUI mode if monitor connected, text-only if headless.

Usage:
  rosrun distributed_comm jetson_display.py
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

import rospy
import cv2
import json
import os
import numpy as np
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String


def has_display():
    return 'DISPLAY' in os.environ and os.environ['DISPLAY']


class JetsonDisplay:
    def __init__(self):
        rospy.init_node('jetson_display', anonymous=True)

        self.img_sub = rospy.Subscriber('/yolo/result_image/compressed', CompressedImage,
                                        self.image_callback, queue_size=2)
        self.det_sub = rospy.Subscriber('/yolo/detections', String,
                                        self.det_callback, queue_size=10)

        self.last_detections = []
        self.frame_count = 0
        self.last_print = rospy.Time.now()

        if has_display():
            cv2.namedWindow('YOLO Distributed (PC infer)', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('YOLO Distributed (PC infer)', 800, 600)
            rospy.loginfo("[Display] GUI mode - showing annotated images")
        else:
            rospy.loginfo("[Display] Text mode (no display) - printing detections")

    def image_callback(self, msg):
        np_arr = np.frombuffer(msg.data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        if has_display():
            if self.last_detections:
                text = "Detections: {}".format(len(self.last_detections))
                cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 0), 2)
            cv2.imshow('YOLO Distributed (PC infer)', image)
            if cv2.waitKey(1) & 0xFF == 27:
                rospy.signal_shutdown('ESC pressed')

        self.frame_count += 1

    def det_callback(self, msg):
        try:
            detections = json.loads(msg.data)
        except (json.JSONDecodeError, ValueError):
            return

        self.last_detections = detections

        if not has_display() and detections:
            items = []
            for d in detections:
                cx = d.get('cx', 0)
                cy = d.get('cy', 0)
                dist = d.get('dist_m', 0)
                items.append("{} {:.0f}% ({:.0f},{:.0f}) {:.1f}m".format(
                    d['class_name'], d['confidence'] * 100, cx, cy, dist))
            rospy.loginfo("[Detection] {}".format(", ".join(items)))

    def run(self):
        r = rospy.Rate(0.2)
        while not rospy.is_shutdown():
            if not has_display():
                rospy.loginfo_throttle(10, "[Display] received {} frames, last: {} detections".format(
                    self.frame_count, len(self.last_detections)))
            r.sleep()

        cv2.destroyAllWindows()


if __name__ == '__main__':
    try:
        JetsonDisplay().run()
    except rospy.ROSInterruptException:
        pass
