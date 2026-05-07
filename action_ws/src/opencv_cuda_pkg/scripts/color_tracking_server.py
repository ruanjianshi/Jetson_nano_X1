#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
import cv2
import numpy as np
import time
from collections import deque
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from opencv_cuda_pkg.msg import ColorTrackingAction, ColorTrackingGoal, ColorTrackingResult, ColorTrackingFeedback

COLOR_RANGES = {
    'red': {
        'lower1': np.array([0, 100, 100]),
        'upper1': np.array([10, 255, 255]),
        'lower2': np.array([160, 100, 100]),
        'upper2': np.array([180, 255, 255]),
        'bgr': (0, 0, 255)
    },
    'green': {
        'lower': np.array([35, 100, 100]),
        'upper': np.array([85, 255, 255]),
        'bgr': (0, 255, 0)
    },
    'blue': {
        'lower': np.array([100, 150, 100]),
        'upper': np.array([140, 255, 255]),
        'bgr': (255, 0, 0)
    },
    'yellow': {
        'lower': np.array([20, 100, 100]),
        'upper': np.array([40, 255, 255]),
        'bgr': (0, 255, 255)
    },
    'orange': {
        'lower': np.array([10, 100, 100]),
        'upper': np.array([25, 255, 255]),
        'bgr': (0, 165, 255)
    },
    'purple': {
        'lower': np.array([130, 100, 100]),
        'upper': np.array([170, 255, 255]),
        'bgr': (255, 0, 255)
    },
    'pink': {
        'lower': np.array([140, 100, 100]),
        'upper': np.array([170, 255, 255]),
        'bgr': (203, 192, 255)
    },
    'cyan': {
        'lower': np.array([80, 100, 100]),
        'upper': np.array([100, 255, 255]),
        'bgr': (255, 255, 0)
    },
    'white': {
        'lower': np.array([0, 0, 200]),
        'upper': np.array([180, 50, 255]),
        'bgr': (255, 255, 255)
    },
    'black': {
        'lower': np.array([0, 0, 0]),
        'upper': np.array([180, 255, 50]),
        'bgr': (0, 0, 0)
    }
}

class ColorTrackingServer:
    def __init__(self):
        rospy.init_node('color_tracking_server', anonymous=True)

        self.bridge = CvBridge()
        self.cap = None
        self.position_history = deque(maxlen=30)
        self.current_color_name = 'red'
        self.current_color_bgr = (0, 0, 255)
        self.running = False
        self.current_fps = 0.0

        self.image_pub = rospy.Publisher(
            '/color_tracking/result_image',
            Image,
            queue_size=1
        )

        self.server = actionlib.SimpleActionServer(
            'color_tracking',
            ColorTrackingAction,
            self.execute_callback,
            False
        )
        self.server.start()

        rospy.loginfo("✅ 颜色追踪服务器已启动")
        rospy.loginfo(f"📤 结果图像话题: /color_tracking/result_image")
        rospy.loginfo(f"🎯 支持颜色: {', '.join(COLOR_RANGES.keys())}")

    def get_color_mask(self, hsv, color_name):
        color = COLOR_RANGES.get(color_name.lower())
        if not color:
            return None

        if 'lower1' in color:
            mask1 = cv2.inRange(hsv, color['lower1'], color['upper1'])
            mask2 = cv2.inRange(hsv, color['lower2'], color['upper2'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, color['lower'], color['upper'])

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask, kernel, iterations=2)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def detect_objects(self, frame, mask, min_area, keep_largest=True):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                cx, cy = x + w // 2, y + h // 2
                detections.append({
                    'bbox': (x, y, w, h),
                    'center': (cx, cy),
                    'area': area
                })

        if keep_largest and detections:
            detections = [max(detections, key=lambda d: d['area'])]

        return detections

    def draw_detections(self, frame, detections, color_bgr, color_name, ref_area, ref_distance):
        result = frame.copy()

        for i, det in enumerate(detections):
            x, y, w, h = det['bbox']
            cx, cy = det['center']
            area = det['area']

            estimated_distance = self.estimate_distance(area, ref_area, ref_distance)

            cv2.rectangle(result, (x, y), (x + w, y + h), color_bgr, 1)
            cv2.circle(result, (cx, cy), 3, (0, 0, 0), -1)
            cv2.circle(result, (cx, cy), 2, color_bgr, -1)

            label = f"({cx},{cy}) {estimated_distance:.1f}cm"
            cv2.putText(result, label, (x, y - 3),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, color_bgr, 1)

            self.position_history.append((cx, cy))

        if len(self.position_history) > 1:
            for i in range(1, len(self.position_history)):
                cv2.line(result, self.position_history[i-1], self.position_history[i],
                        (255, 255, 0), 1)

        cv2.putText(result, f"{color_name.upper()} | FPS: {self.current_fps:.1f} | {len(detections)}", 
                   (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        return result

    def estimate_distance(self, area, ref_area, ref_distance):
        if area <= 0:
            return 999.9
        distance = np.sqrt(ref_area / max(area, 1)) * ref_distance
        return min(distance, 999.9)

    def execute_callback(self, goal):
        rospy.loginfo(f"🎯 收到追踪请求: 颜色={goal.color_name}, 摄像头={goal.camera_index}")

        result = ColorTrackingResult()
        result.success = False
        result.message = ""
        result.num_detections = 0
        result.total_time = 0.0
        result.avg_fps = 0.0

        color_name = goal.color_name.lower()
        if color_name not in COLOR_RANGES:
            result.message = f"不支持的颜色: {color_name}"
            rospy.logerr(f"❌ {result.message}")
            self.server.set_aborted(result)
            return

        self.current_color_name = color_name
        self.current_color_bgr = COLOR_RANGES[color_name]['bgr']

        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(goal.camera_index if goal.camera_index >= 0 else 0)

        if not self.cap.isOpened():
            result.message = f"无法打开摄像头 {goal.camera_index}"
            rospy.logerr(f"❌ {result.message}")
            self.server.set_aborted(result)
            return

        width = goal.width if goal.width > 0 else 640
        height = goal.height if goal.height > 0 else 480
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        min_area = max(100, goal.min_area)
        publish_image = goal.publish_image
        ref_distance = goal.ref_distance if goal.ref_distance > 0 else 50.0
        ref_area = goal.ref_area if goal.ref_area > 0 else 10000

        rospy.loginfo(f"📷 分辨率: {width}x{height}, 最小面积: {min_area}, 参考距离: {ref_distance}cm @ 面积: {ref_area}")

        total_frames = 0
        total_detections = 0
        start_time = time.time()
        fps_time = start_time
        fps_counter = 0
        current_fps = 0.0

        self.running = True
        self.position_history.clear()
        last_client_activity = time.time()
        client_timeout = 30.0

        while self.running and not rospy.is_shutdown():
            if self.server.is_preempt_requested():
                rospy.loginfo("📛 收到抢占请求，停止追踪")
                break

            if time.time() - last_client_activity > client_timeout:
                rospy.logwarn(f"⚠️ 客户端超时({client_timeout}s)，停止追踪")
                break

            ret, frame = self.cap.read()
            if not ret:
                rospy.logwarn("⚠️ 无法读取帧")
                break

            detect_start = time.time()

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = self.get_color_mask(hsv, color_name)

            if mask is None:
                continue

            detections = self.detect_objects(frame, mask, min_area, keep_largest=True)

            process_time = time.time() - detect_start
            total_frames += 1
            total_detections += len(detections)

            fps_counter += 1
            if time.time() - fps_time >= 1.0:
                current_fps = fps_counter / (time.time() - fps_time)
                fps_counter = 0
                fps_time = time.time()

            if detections:
                result_frame = self.draw_detections(frame, detections, self.current_color_bgr, color_name, ref_area, ref_distance)

                if publish_image:
                    img_msg = self.bridge.cv2_to_imgmsg(result_frame, encoding="bgr8")
                    img_msg.header.stamp = rospy.Time.now()
                    img_msg.header.frame_id = "camera"
                    self.image_pub.publish(img_msg)

            if total_frames % 10 == 0:
                rospy.loginfo(f"🔴 {color_name.upper()} 追踪: 帧={total_frames}, 检测={len(detections)}, FPS={current_fps:.1f}")

            feedback = ColorTrackingFeedback()
            feedback.frame_count = total_frames
            feedback.fps = current_fps
            self.current_fps = current_fps
            
            if detections:
                det = detections[0]
                cx, cy = det['center']
                area = det['area']
                dist = self.estimate_distance(area, ref_area, ref_distance)
                feedback.status = f"X:{cx} Y:{cy} A:{area:.0f} D:{dist:.1f}cm FPS:{current_fps:.1f}"
            else:
                feedback.status = f"未检测到 {color_name.upper()} | FPS:{current_fps:.1f}"
            
            feedback.detections_count = len(detections)
            feedback.processing_time = process_time
            self.server.publish_feedback(feedback)
            last_client_activity = time.time()

        if self.cap is not None:
            self.cap.release()

        elapsed = time.time() - start_time

        result.success = True
        result.message = f"追踪完成: {color_name.upper()}"
        result.num_detections = total_detections
        result.total_time = elapsed
        result.avg_fps = total_frames / elapsed if elapsed > 0 else 0.0

        rospy.loginfo(f"✅ 追踪完成: 帧={total_frames}, 检测={total_detections}, 平均FPS={result.avg_fps:.2f}")

        if self.server.is_preempt_requested():
            rospy.loginfo("📛 目标被抢占")
            self.server.set_preempted(result)
        else:
            self.server.set_succeeded(result)

    def run(self):
        rospy.loginfo("🎯 等待颜色追踪目标...")
        rospy.spin()

if __name__ == '__main__':
    try:
        server = ColorTrackingServer()
        server.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
