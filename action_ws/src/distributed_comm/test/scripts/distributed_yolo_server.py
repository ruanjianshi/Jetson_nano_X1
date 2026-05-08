#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

distributed_yolo_server.py - PC-side YOLOv11 inference for distributed system

Subscribes to /camera/image/compressed (JPEG stream from Jetson camera),
runs YOLOv11 inference (CPU or CUDA), publishes annotated image and detection JSON.

Topics:
  Subscribe: /camera/image/compressed   (sensor_msgs/CompressedImage, from Jetson)
  Publish:   /yolo/result_image/compressed (sensor_msgs/CompressedImage, to Jetson)
  Publish:   /yolo/detections              (std_msgs/String JSON, to Jetson)

Usage:
  rosrun distributed_comm distributed_yolo_server.py _model_path:=yolo11n.pt _device:=cuda:0

Params:
  _model_path       (str,   "yolo11n.pt")   YOLO model file path
  _conf             (float, 0.5)            Confidence threshold
  _iou              (float, 0.45)           IOU-NMS threshold
  _device           (str,   "cpu")          "cpu" or "cuda:0"
  _imgsz            (int,   640)            Inference image size
  _jpeg_quality     (int,   75)             JPEG encode quality for result image
  _ref_height_m     (float, 1.7)            Real-world object height (meters)
  _ref_px           (float, 300)            Pixel height at ref_distance_m
  _ref_distance_m   (float, 2.0)            Calibration reference distance (meters)
  _venv_path        (str,   "")             Extra Python site-packages path for ultralytics
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

import rospy
import cv2
import json
import time
import sys
import os
import numpy as np
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String


def _try_import_ultralytics(extra_paths=None):
    """Try to import ultralytics.YOLO, searching multiple venv paths first.
    ROS1 Noetic uses system Python3.8; if ultralytics is in a venv/conda
    (e.g., miniconda3 env), we inject its site-packages into sys.path."""
    for path in (extra_paths or []):
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)
    # @brief Auto-detect common venv/conda locations
    for path in [
        os.path.expanduser('~/miniconda3/envs/yolo/lib/python3.10/site-packages'),
        os.path.expanduser('~/miniconda3/envs/yolo/lib/python3.8/site-packages'),
        os.path.expanduser('~/yolo/lib/python3.8/site-packages'),
        os.path.expanduser('~/yolo/lib/python3.10/site-packages'),
        os.path.expanduser('~/anaconda3/envs/yolo/lib/python3.8/site-packages'),
        os.path.expanduser('~/.virtualenvs/yolo/lib/python3.8/site-packages'),
    ]:
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)
    try:
        from ultralytics import YOLO
        return YOLO
    except Exception as e:
        sys.stderr.write("[WARN] Cannot import ultralytics: {}\n".format(e))
        return None


YOLO = _try_import_ultralytics()


class DistributedYoloServer:
    def __init__(self):
        rospy.init_node('distributed_yolo_server', anonymous=True)

        # @brief Retry import if _venv_path was specified via ROS param
        global YOLO
        if YOLO is None:
            extra = rospy.get_param('~venv_path', '')
            if extra:
                YOLO = _try_import_ultralytics([extra])
        if YOLO is None:
            rospy.logfatal("ultralytics not found in system or virtual env")
            rospy.logfatal("Set _venv_path:=/path/to/venv/lib/python3.X/site-packages")
            raise ImportError("ultralytics required")

        # @brief Inference parameters
        model_path         = rospy.get_param('~model_path', 'yolo11n.pt')
        self.conf          = rospy.get_param('~conf', 0.5)
        self.iou           = rospy.get_param('~iou', 0.45)
        self.device        = rospy.get_param('~device', 'cpu')
        self.imgsz         = rospy.get_param('~imgsz', 640)
        self.jpeg_quality  = rospy.get_param('~jpeg_quality', 75)

        # @brief Distance estimation calibration
        #   dist = ref_height_m / bbox_h * ref_px * (ref_distance_m / ref_px)
        #   Simplified: closer objects -> larger bbox_h -> smaller distance
        self.ref_height_m   = rospy.get_param('~ref_height_m', 1.7)
        self.ref_px         = rospy.get_param('~ref_px', 300)
        self.ref_distance_m = rospy.get_param('~ref_distance_m', 2.0)

        # @brief Load YOLO model
        rospy.loginfo("[YOLO] Loading model: {}  device={}".format(model_path, self.device))
        self.model = YOLO(model_path)
        self.model.to(self.device)
        rospy.loginfo("[YOLO] Model loaded OK")

        # @brief Subscribe to Jetson camera stream (compressed JPEG)
        self.sub = rospy.Subscriber('/camera/image/compressed', CompressedImage,
                                    self.callback, queue_size=2)
        # @brief Publish detection results as JSON string
        self.det_pub = rospy.Publisher('/yolo/detections', String, queue_size=10)
        # @brief Publish annotated image (compressed) back to Jetson for low-bandwidth display
        self.result_pub = rospy.Publisher('/yolo/result_image/compressed', CompressedImage, queue_size=2)

        self.frame_count = 0
        self.infer_time_sum = 0.0
        self.last_print = rospy.Time.now()

        rospy.loginfo("[YOLO] waiting for camera images from Jetson...")

    def callback(self, msg):
        """Main inference callback: decode JPEG -> YOLO infer -> publish results"""
        start = time.time()

        # @brief Decode JPEG from Jetson camera stream
        np_arr = np.frombuffer(msg.data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        # @brief Run YOLOv11 inference
        results = self.model(image, conf=self.conf, iou=self.iou,
                             imgsz=self.imgsz, device=self.device, verbose=False)
        detections = []

        # @brief Parse detection boxes: class, confidence, bbox, center, distance
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names.get(cls_id, 'unknown')
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()

            # Center of bounding box (pixel coordinates, (0,0) = top-left)
            cx = round((xyxy[0] + xyxy[2]) / 2.0, 1)
            cy = round((xyxy[1] + xyxy[3]) / 2.0, 1)

            # Distance: inverse-height model, calibrated by ref_px at ref_distance_m
            bbox_h = xyxy[3] - xyxy[1]
            dist = round(self.ref_height_m * self.ref_px / (bbox_h + 1e-6) * self.ref_distance_m / self.ref_px, 1)
            if bbox_h > self.ref_px:
                dist = round(self.ref_distance_m * self.ref_px / (bbox_h + 1e-6), 1)

            detections.append({
                'class_id':   cls_id,
                'class_name': cls_name,
                'confidence': round(conf, 4),
                'x1': round(xyxy[0], 1), 'y1': round(xyxy[1], 1),
                'x2': round(xyxy[2], 1), 'y2': round(xyxy[3], 1),
                'cx': cx, 'cy': cy,
                'dist_m': dist,
            })

        # @brief Draw bounding boxes on image using ultralytics builtin
        annotated = results[0].plot()

        dt = time.time() - start
        self.frame_count += 1
        self.infer_time_sum += dt

        # @brief Publish detection JSON if objects found
        if detections:
            det_msg = String()
            det_msg.data = json.dumps(detections, ensure_ascii=False)
            self.det_pub.publish(det_msg)

        # @brief Encode annotated image as JPEG and publish (for Jetson display)
        now = rospy.Time.now()
        _, jpeg = cv2.imencode('.jpg', annotated,
                               [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
        result_compressed = CompressedImage()
        result_compressed.header.stamp = now
        result_compressed.header.frame_id = "yolo"
        result_compressed.format = "jpeg"
        result_compressed.data = np.array(jpeg).tobytes()
        self.result_pub.publish(result_compressed)

        # @brief Print throughput stats every 3 seconds
        if (now - self.last_print).to_sec() >= 3.0:
            avg_fps = self.frame_count / (now - self.last_print).to_sec()
            avg_infer = self.infer_time_sum / self.frame_count * 1000 if self.frame_count else 0
            rospy.loginfo("[YOLO] FPS: {:.1f} | infer: {:.0f} ms | detections: {} | img: {} KB".format(
                avg_fps, avg_infer, len(detections),
                len(result_compressed.data) / 1024.0))
            self.frame_count = 0
            self.infer_time_sum = 0.0
            self.last_print = now

    def run(self):
        rospy.spin()


if __name__ == '__main__':
    try:
        DistributedYoloServer().run()
    except rospy.ROSInterruptException:
        pass
