#!/usr/bin/env python3

import sys
import os

# 在任何 import 之前设置环境变量，解决 OpenMP 库冲突
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'

import rospy
import actionlib
import cv2
import numpy as np
import time
import rospkg
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from opencv_cuda_pkg.msg import DetectionResult
from opencv_cuda_pkg.msg import OpenCVDetectionAction, OpenCVDetectionGoal, OpenCVDetectionResult, OpenCVDetectionFeedback
from typing import List, Dict, Optional, Tuple


class OpenCVDetectionServer:
    def __init__(self):
        rospy.init_node('opencv_detection_server', anonymous=True)
        
        self.bridge = CvBridge()
        self.detector = None
        self.detection_method = None
        self.class_names = []
        
        # 检查 CUDA 支持
        self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if self.cuda_available:
            rospy.loginfo("✅ CUDA 加速已启用")
        else:
            rospy.logwarn("⚠️  CUDA 不可用，将使用 CPU")
        
        # 实时推理发布器
        self.detection_result_pub = rospy.Publisher(
            '/opencv/detection_result',
            Image,
            queue_size=1
        )
        
        self.server = actionlib.SimpleActionServer(
            'opencv_detection',
            OpenCVDetectionAction,
            self.execute,
            False
        )
        self.server.start()
        
        rospy.loginfo("✅ OpenCV 目标检测服务器已启动")
        rospy.loginfo(f"🎯 服务器名称: opencv_detection")
        rospy.loginfo(f"📤 检测结果话题: /opencv/detection_result")
        rospy.loginfo("📝 支持的检测方法: haar_cascade, hog, dnn")
    
    def load_detector(self, detection_method: str, model_path: str = '', 
                     cascade_path: str = '', use_cuda: bool = True) -> bool:
        try:
            if detection_method == 'haar_cascade':
                rospy.loginfo(f"📥 加载 Haar Cascade 模型: {cascade_path}")
                
                if not cascade_path:
                    rospack = rospkg.RosPack()
                    cascade_path = rospack.get_path('opencv_cuda_pkg') + '/models/haarcascade_frontalface_default.xml'
                
                self.detector = cv2.CascadeClassifier(cascade_path)
                self.detection_method = detection_method
                self.class_names = ['face']
                rospy.loginfo("✅ Haar Cascade 模型加载成功")
                return True
            
            elif detection_method == 'hog':
                rospy.loginfo("📥 初始化 HOG 行人检测器")
                
                self.detector = cv2.HOGDescriptor()
                self.detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                self.detection_method = detection_method
                self.class_names = ['person']
                rospy.loginfo("✅ HOG 检测器初始化成功")
                return True
            
            elif detection_method == 'dnn':
                rospy.loginfo(f"📥 加载 DNN 模型: {model_path}")
                
                if not model_path:
                    rospy.logerr("❌ DNN 模型路径未指定")
                    return False
                
                # 加载预训练模型（使用 MobileNet-SSD 作为示例）
                # 这里可以加载 YOLO、SSD、MobileNet 等模型
                net = cv2.dnn.readNet(model_path)
                
                if use_cuda and self.cuda_available:
                    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
                    rospy.loginfo("✅ DNN 模型加载成功（CUDA）")
                else:
                    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
                    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
                    rospy.loginfo("✅ DNN 模型加载成功（CPU）")
                
                self.detector = net
                self.detection_method = detection_method
                
                # COCO 数据集类别
                self.class_names = [
                    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
                    'train', 'truck', 'boat', 'traffic light', 'fire hydrant',
                    'stop sign', 'parking meter', 'bench', 'bird', 'cat',
                    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
                    'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag',
                    'tie', 'suitcase', 'frisbee', 'skis', 'snowboard',
                    'sports ball', 'kite', 'baseball bat', 'baseball glove',
                    'skateboard', 'surfboard', 'tennis racket', 'bottle',
                    'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
                    'banana', 'apple', 'sandwich', 'orange', 'broccoli',
                    'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
                    'couch', 'potted plant', 'bed', 'dining table', 'toilet',
                    'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
                    'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
                    'book', 'clock', 'vase', 'scissors', 'teddy bear',
                    'hair drier', 'toothbrush'
                ]
                
                return True
            
            else:
                rospy.logerr(f"❌ 不支持的检测方法: {detection_method}")
                return False
                
        except Exception as e:
            rospy.logerr(f"❌ 检测器加载失败: {e}")
            return False
    
    def detect(self, image: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict]:
        if self.detector is None:
            return []
        
        start_time = time.time()
        
        try:
            if self.detection_method == 'haar_cascade':
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                rects = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                detections = []
                for (x, y, w, h) in rects:
                    detections.append({
                        'class_id': 0,
                        'class_name': 'face',
                        'confidence': 1.0,
                        'bbox': [float(x), float(y), float(x + w), float(y + h)],
                        'center': [float(x + w / 2), float(y + h / 2)],
                        'area': float(w * h)
                    })
                
                return detections
            
            elif self.detection_method == 'hog':
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                rects, weights = self.detector.detectMultiScale(gray, winStride=(8, 8), padding=(8, 8), scale=1.05)
                
                detections = []
                for (x, y, w, h), weight in zip(rects, weights):
                    if weight > confidence_threshold:
                        detections.append({
                            'class_id': 0,
                            'class_name': 'person',
                            'confidence': float(weight),
                            'bbox': [float(x), float(y), float(x + w), float(y + h)],
                            'center': [float(x + w / 2), float(y + h / 2)],
                            'area': float(w * h)
                        })
                
                return detections
            
            elif self.detection_method == 'dnn':
                # 使用 MobileNet-SSD 格式
                blob = cv2.dnn.blobFromImage(image, 0.007843, (300, 300), (127.5, 127.5, 127.5), swapRB=False, crop=False)
                self.detector.setInput(blob)
                detections = self.detector.forward()
                
                result_detections = []
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    if confidence > confidence_threshold:
                        box = detections[0, 0, i, 3:7] * np.array([image.shape[1], image.shape[0], image.shape[1], image.shape[0]])
                        (startX, startY, endX, endY) = box.astype("int")
                        
                        class_id = int(detections[0, 0, i, 1]) - 1
                        class_name = self.class_names[class_id] if 0 <= class_id < len(self.class_names) else 'unknown'
                        
                        result_detections.append({
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': float(confidence),
                            'bbox': [float(startX), float(startY), float(endX), float(endY)],
                            'center': [float((startX + endX) / 2), float((startY + endY) / 2)],
                            'area': float((endX - startX) * (endY - startY))
                        })
                
                return result_detections
            
            else:
                return []
            
        except Exception as e:
            rospy.logerr(f"❌ 检测失败: {e}")
            return []
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        image_draw = image.copy()
        
        colors = self._generate_colors(len(self.class_names))
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            cls_id = det['class_id']
            conf = det['confidence']
            class_name = det['class_name']
            
            color = colors[cls_id % len(colors)]
            
            cv2.rectangle(image_draw, (x1, y1), (x2, y2), color, 2)
            
            label = f"{class_name} {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(image_draw, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0] + 10, y1), color, -1)
            cv2.putText(image_draw, label, (x1 + 5, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return image_draw
    
    def _generate_colors(self, num_classes: int) -> List[tuple]:
        colors = []
        for i in range(num_classes):
            hue = i * 137.508
            rgb = self._hsv_to_rgb((hue % 360, 1.0, 1.0))
            colors.append(tuple(map(int, rgb)))
        return colors
    
    def _hsv_to_rgb(self, hsv: tuple) -> tuple:
        h, s, v = hsv
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return (r + m) * 255, (g + m) * 255, (b + m) * 255
    
    def get_image_from_topic(self, topic_name: str, timeout: float = 5.0) -> Optional[np.ndarray]:
        try:
            image_msg = rospy.wait_for_message(topic_name, Image, timeout=timeout)
            cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding="bgr8")
            return cv_image
        except rospy.ROSException as e:
            rospy.logerr(f"❌ 无法从话题 {topic_name} 获取图像: {e}")
            return None
    
    def get_image_from_file(self, file_path: str) -> Optional[np.ndarray]:
        try:
            image = cv2.imread(file_path)
            if image is None:
                rospy.logerr(f"❌ 无法读取图像文件: {file_path}")
                return None
            return image
        except Exception as e:
            rospy.logerr(f"❌ 读取图像文件失败: {e}")
            return None
    
    def get_image_from_camera(self, camera_index: int) -> Optional[np.ndarray]:
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                rospy.logerr(f"❌ 无法打开摄像头: {camera_index}")
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                rospy.logerr(f"❌ 无法从摄像头 {camera_index} 读取帧")
                return None
            
            return frame
        except Exception as e:
            rospy.logerr(f"❌ 摄像头读取失败: {e}")
            return None
    
    def process_video_file(self, file_path: str, confidence_threshold: float, 
                          nms_threshold: float, publish: bool) -> Dict:
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {'error': f'无法打开视频文件: {file_path}', 'success': False}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            rospy.loginfo(f"📹 视频信息: FPS={fps}, 总帧数={frame_count}")
            
            all_detections = []
            total_inference_time = 0.0
            processed_frames = 0
            
            while not self.server.is_preempt_requested() and processed_frames < 100:
                ret, frame = cap.read()
                if not ret:
                    break
                
                detections = self.detect(frame, confidence_threshold)
                
                if detections:
                    all_detections.extend(detections)
                    total_inference_time += 0.033  # 估算
                    processed_frames += 1
                    
                    if publish:
                        result_image = self.draw_detections(frame, detections)
                        msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                        msg.header.stamp = rospy.Time.now()
                        msg.header.frame_id = "camera"
                        self.detection_result_pub.publish(msg)
                    
                    feedback = OpenCVDetectionFeedback()
                    feedback.frame_count = processed_frames
                    feedback.fps = fps
                    feedback.status = f"处理中: {processed_frames}/{min(100, frame_count)} 帧, 检测到 {len(detections)} 个目标"
                    self.server.publish_feedback(feedback)
                else:
                    rospy.logwarn(f"⚠️  帧 {processed_frames}: 未检测到目标")
                
                if processed_frames >= 100:
                    rospy.loginfo("⚠️  已处理 100 帧，停止")
                    break
            
            cap.release()
            
            avg_inference_time = total_inference_time / processed_frames if processed_frames > 0 else 0.0
            
            return {
                'success': True,
                'detections': all_detections,
                'inference_time': total_inference_time,
                'frames_processed': processed_frames,
                'avg_inference_time': avg_inference_time
            }
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def process_camera_stream(self, camera_index: int, confidence_threshold: float,
                              nms_threshold: float, publish: bool, duration: float = 10.0) -> Dict:
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return {'error': f'无法打开摄像头: {camera_index}', 'success': False}
            
            rospy.loginfo(f"📹 摄像头 {camera_index} 已打开，开始检测...")
            rospy.loginfo(f"⏱️  检测时长: {duration} 秒")
            
            all_detections = []
            total_inference_time = 0.0
            processed_frames = 0
            start_time = time.time()
            
            while not self.server.is_preempt_requested() and (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if not ret:
                    rospy.logwarn("⚠️  无法读取帧，继续尝试...")
                    continue
                
                detect_start = time.time()
                detections = self.detect(frame, confidence_threshold)
                inference_time = time.time() - detect_start
                
                if detections:
                    all_detections.extend(detections)
                    total_inference_time += inference_time
                    processed_frames += 1
                    
                    if publish:
                        result_image = self.draw_detections(frame, detections)
                        msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                        msg.header.stamp = rospy.Time.now()
                        msg.header.frame_id = "camera"
                        self.detection_result_pub.publish(msg)
                    
                    feedback = OpenCVDetectionFeedback()
                    feedback.frame_count = processed_frames
                    feedback.fps = processed_frames / (time.time() - start_time)
                    feedback.status = f"检测中: {processed_frames} 帧, 检测到 {len(detections)} 个目标"
                    self.server.publish_feedback(feedback)
                else:
                    rospy.logwarn(f"⚠️  帧 {processed_frames}: 未检测到目标")
            
            cap.release()
            
            avg_inference_time = total_inference_time / processed_frames if processed_frames > 0 else 0.0
            
            rospy.loginfo(f"📹 实时检测完成: 处理了 {processed_frames} 帧")
            
            return {
                'success': True,
                'detections': all_detections,
                'inference_time': total_inference_time,
                'frames_processed': processed_frames,
                'avg_inference_time': avg_inference_time
            }
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def execute(self, goal):
        result = OpenCVDetectionResult()
        
        input_type = goal.input_type
        input_source = goal.input_source
        detection_method = goal.detection_method
        model_path = goal.model_path
        cascade_path = goal.cascade_path
        confidence_threshold = goal.confidence_threshold
        nms_threshold = goal.nms_threshold
        use_cuda = goal.use_cuda
        publish_processed = goal.publish_processed
        
        rospy.loginfo(f"🎯 检测请求: 类型={input_type}, 源={input_source}")
        rospy.loginfo(f"🔍 方法: {detection_method}, CUDA={'是' if use_cuda else '否'}")
        rospy.loginfo(f"⚙️  置信度: {confidence_threshold}, NMS: {nms_threshold}")
        
        if not self.load_detector(detection_method, model_path, cascade_path, use_cuda):
            rospy.logerr("❌ 检测器加载失败")
            self.server.set_aborted()
            return
        
        inference_result = None
        original_image = None
        
        if input_type == 'topic':
            rospy.loginfo(f"📷 从话题获取图像: {input_source}")
            original_image = self.get_image_from_topic(input_source)
            if original_image is None:
                self.server.set_aborted()
                return
            
            detect_start = time.time()
            detections = self.detect(original_image, confidence_threshold)
            inference_time = time.time() - detect_start
            
            if publish_processed:
                result_image = self.draw_detections(original_image, detections)
                msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                msg.header.stamp = rospy.Time.now()
                msg.header.frame_id = "camera"
                self.detection_result_pub.publish(msg)
            
            inference_result = {
                'success': True,
                'detections': detections,
                'inference_time': inference_time
            }
        
        elif input_type == 'image_file':
            rospy.loginfo(f"📄 从文件读取图像: {input_source}")
            original_image = self.get_image_from_file(input_source)
            if original_image is None:
                self.server.set_aborted()
                return
            
            detect_start = time.time()
            detections = self.detect(original_image, confidence_threshold)
            inference_time = time.time() - detect_start
            
            if publish_processed:
                result_image = self.draw_detections(original_image, detections)
                msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                msg.header.stamp = rospy.Time.now()
                msg.header.frame_id = "camera"
                self.detection_result_pub.publish(msg)
            
            inference_result = {
                'success': True,
                'detections': detections,
                'inference_time': inference_time
            }
        
        elif input_type == 'camera':
            camera_index = int(input_source) if input_source.isdigit() else 0
            rospy.loginfo(f"📹 实时摄像头检测: {camera_index}")
            inference_result = self.process_camera_stream(camera_index, confidence_threshold, 
                                                        nms_threshold, publish_processed)
        
        elif input_type == 'video_file':
            rospy.loginfo(f"🎬 处理视频文件: {input_source}")
            inference_result = self.process_video_file(input_source, confidence_threshold,
                                                       nms_threshold, publish_processed)
        
        else:
            rospy.logerr(f"❌ 不支持的输入类型: {input_type}")
            self.server.set_aborted()
            return
        
        if not inference_result.get('success'):
            rospy.logerr(f"❌ 检测失败: {inference_result.get('error', '未知错误')}")
            self.server.set_aborted()
            return
        
        detections = inference_result.get('detections', [])
        inference_time = inference_result.get('inference_time', 0.0)
        frames_processed = inference_result.get('frames_processed', 1)
        avg_inference_time = inference_result.get('avg_inference_time', inference_time)
        
        result.num_detections = len(detections)
        result.inference_time = inference_time
        result.frames_processed = frames_processed
        result.avg_inference_time = avg_inference_time
        
        for det in detections:
            detection_msg = DetectionResult()
            detection_msg.class_id = det['class_id']
            detection_msg.class_name = det['class_name']
            detection_msg.confidence = det['confidence']
            detection_msg.x1 = det['bbox'][0]
            detection_msg.y1 = det['bbox'][1]
            detection_msg.x2 = det['bbox'][2]
            detection_msg.y2 = det['bbox'][3]
            detection_msg.center_x = det['center'][0]
            detection_msg.center_y = det['center'][1]
            detection_msg.area = det['area']
            
            result.detections.append(detection_msg)
        
        rospy.loginfo(f"✅ 检测完成: {len(detections)} 个目标, 耗时 {inference_time:.3f}s")
        if frames_processed > 1:
            rospy.loginfo(f"📊 处理帧数: {frames_processed}, 平均推理时间: {avg_inference_time:.3f}s")
        
        self.server.set_succeeded(result)
    
    def run(self):
        rospy.loginfo("🎯 等待 Action 目标...")
        rospy.spin()


if __name__ == '__main__':
    try:
        server = OpenCVDetectionServer()
        server.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")