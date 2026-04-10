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
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from yolov11_pkg.msg import DetectionResult
from yolov11_pkg.msg import Yolov11InferenceAction, Yolov11InferenceGoal, Yolov11InferenceResult, Yolov11InferenceFeedback
from ultralytics import YOLO
import rospkg
from typing import List, Dict, Optional


class YOLOv11InferenceServer:
    def __init__(self):
        rospy.init_node('yolov11_inference_server', anonymous=True)
        
        self.bridge = CvBridge()
        self.current_model = None
        self.current_model_path = None
        self.current_class_names = None
        
        # 实时推理发布器
        self.inference_result_pub = rospy.Publisher(
            '/yolov11/inference_result',
            Image,
            queue_size=1
        )
        
        self.server = actionlib.SimpleActionServer(
            'yolov11_inference',
            Yolov11InferenceAction,
            self.execute,
            False
        )
        self.server.start()
        
        rospy.loginfo("✅ YOLOv11 推理服务器已启动")
        rospy.loginfo(f"🎯 服务器名称: yolov11_inference")
        rospy.loginfo(f"📤 推理结果话题: /yolov11/inference_result")
        rospy.loginfo("📝 支持的输入类型: topic, image_file, camera, video_file")
    
    def load_model(self, model_path: str, device: str = 'cuda:0') -> bool:
        if self.current_model is not None and self.current_model_path == model_path:
            rospy.loginfo("📦 使用已加载的模型")
            return True
        
        try:
            rospy.loginfo(f"📥 加载 YOLOv11 模型: {model_path}")
            self.current_model = YOLO(model_path)
            self.current_model.to(device)
            self.current_class_names = self.current_model.names
            self.current_model_path = model_path
            rospy.loginfo(f"✅ 模型加载成功，设备: {device}")
            rospy.loginfo(f"📊 类别数量: {len(self.current_class_names)}")
            return True
        except Exception as e:
            rospy.logerr(f"❌ 模型加载失败: {e}")
            self.current_model = None
            self.current_model_path = None
            self.current_class_names = None
            return False
    
    def infer(self, image: np.ndarray, confidence_threshold: float = 0.5,
              iou_threshold: float = 0.45, device: str = 'cuda:0') -> Dict:
        if self.current_model is None:
            return {'error': '模型未加载', 'success': False}
        
        start_time = time.time()
        
        try:
            results = self.current_model(image, conf=confidence_threshold,
                                       iou=iou_threshold, device=device,
                                       verbose=False)
            
            inference_time = time.time() - start_time
            
            if len(results) > 0:
                detections = self._parse_results(results[0])
                return {
                    'success': True,
                    'detections': detections,
                    'inference_time': inference_time,
                    'raw_result': results[0]
                }
            else:
                return {
                    'success': True,
                    'detections': [],
                    'inference_time': inference_time,
                    'raw_result': results[0] if len(results) > 0 else None
                }
        except Exception as e:
            rospy.logerr(f"❌ 推理失败: {e}")
            return {'error': str(e), 'success': False}
    
    def _parse_results(self, result) -> List[Dict]:
        detections = []
        
        if result.boxes is None:
            return detections
        
        boxes = result.boxes
        
        for i in range(len(boxes)):
            box = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_id = int(boxes.cls[i].cpu().numpy())
            
            x1, y1, x2, y2 = box
            
            detection = {
                'class_id': cls_id,
                'class_name': self.current_class_names[cls_id] if cls_id < len(self.current_class_names) else f'class_{cls_id}',
                'confidence': conf,
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'center': [(x1 + x2) / 2, (y1 + y2) / 2],
                'area': float((x2 - x1) * (y2 - y1))
            }
            detections.append(detection)
        
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        return detections
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        image_draw = image.copy()
        
        colors = self._generate_colors(len(self.current_class_names) if self.current_class_names else 80)
        
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
                          iou_threshold: float, device: str) -> Dict:
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                rospy.logerr(f"❌ 无法打开视频文件: {file_path}")
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
                
                result = self.infer(frame, confidence_threshold, iou_threshold, device)
                
                if result.get('success'):
                    all_detections.extend(result.get('detections', []))
                    total_inference_time += result.get('inference_time', 0.0)
                    processed_frames += 1
                    
                    feedback = Yolov11InferenceFeedback()
                    feedback.frame_count = processed_frames
                    feedback.fps = fps
                    feedback.status = f"处理中: {processed_frames}/{min(100, frame_count)} 帧"
                    self.server.publish_feedback(feedback)
                else:
                    rospy.logerr(f"❌ 帧推理失败: {result.get('error')}")
                
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
            rospy.logerr(f"❌ 视频处理失败: {e}")
            return {'error': str(e), 'success': False}
    
    def process_camera_stream(self, camera_index: int, confidence_threshold: float,
                              iou_threshold: float, device: str, duration: float = 10.0) -> Dict:
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                rospy.logerr(f"❌ 无法打开摄像头: {camera_index}")
                return {'error': f'无法打开摄像头: {camera_index}', 'success': False}
            
            rospy.loginfo(f"📹 摄像头 {camera_index} 已打开，开始实时推理...")
            rospy.loginfo(f"⏱️  推理时长: {duration} 秒")
            
            all_detections = []
            total_inference_time = 0.0
            processed_frames = 0
            start_time = time.time()
            
            while not self.server.is_preempt_requested() and (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if not ret:
                    rospy.logwarn("⚠️  无法读取帧，继续尝试...")
                    continue
                
                result = self.infer(frame, confidence_threshold, iou_threshold, device)
                
                if result.get('success'):
                    detections = result.get('detections', [])
                    all_detections.extend(detections)
                    total_inference_time += result.get('inference_time', 0.0)
                    processed_frames += 1
                    
                    # 绘制检测框
                    result_image = self.draw_detections(frame, detections)
                    
                    # 发布推理结果图像
                    msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                    msg.header.stamp = rospy.Time.now()
                    msg.header.frame_id = "camera"
                    self.inference_result_pub.publish(msg)
                    
                    # 发布反馈
                    feedback = Yolov11InferenceFeedback()
                    feedback.frame_count = processed_frames
                    feedback.fps = processed_frames / (time.time() - start_time)
                    feedback.status = f"推理中: {processed_frames} 帧, 检测到 {len(detections)} 个目标"
                    self.server.publish_feedback(feedback)
                else:
                    rospy.logerr(f"❌ 帧推理失败: {result.get('error')}")
            
            cap.release()
            
            avg_inference_time = total_inference_time / processed_frames if processed_frames > 0 else 0.0
            
            rospy.loginfo(f"📹 实时推理完成: 处理了 {processed_frames} 帧")
            
            return {
                'success': True,
                'detections': all_detections,
                'inference_time': total_inference_time,
                'frames_processed': processed_frames,
                'avg_inference_time': avg_inference_time
            }
            
        except Exception as e:
            rospy.logerr(f"❌ 摄像头推理失败: {e}")
            return {'error': str(e), 'success': False}
    
    def execute(self, goal):
        result = Yolov11InferenceResult()
        feedback = Yolov11InferenceFeedback()
        
        input_type = goal.input_type
        input_source = goal.input_source
        save_image_path = goal.save_image_path if goal.save_image_path else ''
        
        model_path = goal.model_path
        confidence_threshold = goal.confidence_threshold if goal.confidence_threshold > 0 else 0.5
        iou_threshold = goal.iou_threshold if goal.iou_threshold > 0 else 0.45
        device = goal.device if goal.device else 'cuda:0'
        
        if not model_path:
            rospack = rospkg.RosPack()
            model_path = rospack.get_path('yolov11_pkg') + '/models/yolo11n.pt'
        
        rospy.loginfo(f"🎯 推理请求: 类型={input_type}, 源={input_source}")
        if save_image_path:
            rospy.loginfo(f"💾 保存路径: {save_image_path}")
        rospy.loginfo(f"📦 模型: {model_path}")
        rospy.loginfo(f"⚙️  参数: conf={confidence_threshold}, iou={iou_threshold}, device={device}")
        
        if not self.load_model(model_path, device):
            rospy.logerr("❌ 模型加载失败")
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
            inference_result = self.infer(original_image, confidence_threshold, iou_threshold, device)
        
        elif input_type == 'image_file':
            rospy.loginfo(f"📄 从文件读取图像: {input_source}")
            original_image = self.get_image_from_file(input_source)
            if original_image is None:
                self.server.set_aborted()
                return
            inference_result = self.infer(original_image, confidence_threshold, iou_threshold, device)
        
        elif input_type == 'camera':
            camera_index = int(input_source) if input_source.isdigit() else 0
            rospy.loginfo(f"📹 实时摄像头推理: {camera_index}")
            inference_result = self.process_camera_stream(camera_index, confidence_threshold, iou_threshold, device)
        
        elif input_type == 'video_file':
            rospy.loginfo(f"🎬 处理视频文件: {input_source}")
            inference_result = self.process_video_file(input_source, confidence_threshold, iou_threshold, device)
        
        else:
            rospy.logerr(f"❌ 不支持的输入类型: {input_type}")
            self.server.set_aborted()
            return
        
        if not inference_result.get('success'):
            rospy.logerr(f"❌ 推理失败: {inference_result.get('error', '未知错误')}")
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
        
        # 保存推理结果图片
        if save_image_path and original_image is not None:
            try:
                result_image = self.draw_detections(original_image, detections)
                
                # 确保目录存在
                os.makedirs(os.path.dirname(save_image_path), exist_ok=True)
                
                cv2.imwrite(save_image_path, result_image)
                rospy.loginfo(f"✅ 推理结果已保存到: {save_image_path}")
            except Exception as e:
                rospy.logerr(f"❌ 保存推理结果失败: {e}")
        
        rospy.loginfo(f"✅ 推理完成: {len(detections)} 个目标, 耗时 {inference_time:.3f}s")
        if frames_processed > 1:
            rospy.loginfo(f"📊 处理帧数: {frames_processed}, 平均推理时间: {avg_inference_time:.3f}s")
        
        self.server.set_succeeded(result)
    
    def run(self):
        rospy.loginfo("🎯 等待 Action 目标...")
        rospy.spin()


if __name__ == '__main__':
    try:
        server = YOLOv11InferenceServer()
        server.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")