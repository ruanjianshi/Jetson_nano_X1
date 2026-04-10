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
import json
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from opencv_cuda_pkg.msg import ImageProcessingAction, ImageProcessingGoal, ImageProcessingResult, ImageProcessingFeedback
import rospkg
from typing import Dict, Any, Optional, Tuple


class OpenCVImageProcessingServer:
    def __init__(self):
        rospy.init_node('opencv_image_processing_server', anonymous=True)
        
        self.bridge = CvBridge()
        
        # 检查 CUDA 支持
        self.cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if self.cuda_available:
            rospy.loginfo("✅ CUDA 加速已启用")
        else:
            rospy.logwarn("⚠️  CUDA 不可用，将使用 CPU")
        
        # 实时推理发布器
        self.processed_image_pub = rospy.Publisher(
            '/opencv/processed_image',
            Image,
            queue_size=1
        )
        
        self.server = actionlib.SimpleActionServer(
            'image_processing',
            ImageProcessingAction,
            self.execute,
            False
        )
        self.server.start()
        
        rospy.loginfo("✅ OpenCV 图像处理服务器已启动")
        rospy.loginfo(f"🎯 服务器名称: image_processing")
        rospy.loginfo(f"📤 处理结果话题: /opencv/processed_image")
        rospy.loginfo("📝 支持的操作: resize, crop, rotate, blur, gaussian_blur, canny, threshold, color_convert")
    
    def process_image(self, image: np.ndarray, operation: str, params: Dict[str, Any], 
                      use_cuda: bool) -> Tuple[np.ndarray, Dict[str, Any]]:
        start_time = time.time()
        result_image = image.copy()
        info = {}
        
        try:
            if use_cuda and self.cuda_available:
                upload_start = time.time()
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(image)
                info['upload_time'] = time.time() - upload_start
            
            if operation == 'resize':
                width = params.get('width', 640)
                height = params.get('height', 480)
                
                if use_cuda and self.cuda_available:
                    result_gpu = cv2.cuda.resize(gpu_image, (width, height))
                    result_image = result_gpu.download()
                else:
                    result_image = cv2.resize(image, (width, height))
                
                info = {'width': width, 'height': height, 'size': result_image.shape}
            
            elif operation == 'crop':
                x = params.get('x', 0)
                y = params.get('y', 0)
                w = params.get('width', 100)
                h = params.get('height', 100)
                
                result_image = image[y:y+h, x:x+w]
                info = {'crop': (x, y, w, h), 'size': result_image.shape}
            
            elif operation == 'rotate':
                angle = params.get('angle', 90)
                
                if use_cuda and self.cuda_available:
                    result_gpu = cv2.cuda.rotate(gpu_image, cv2.cuda.ROTATE_90_CLOCKWISE if angle == 90 else cv2.cuda.ROTATE_180)
                    result_image = result_gpu.download()
                else:
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                    result_image = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))
                
                info = {'angle': angle}
            
            elif operation == 'blur':
                ksize = params.get('ksize', 15)
                
                if use_cuda and self.cuda_available:
                    result_gpu = cv2.cuda.blur(gpu_image, (ksize, ksize))
                    result_image = result_gpu.download()
                else:
                    result_image = cv2.blur(image, (ksize, ksize))
                
                info = {'ksize': ksize}
            
            elif operation == 'gaussian_blur':
                ksize = params.get('ksize', 15)
                sigma = params.get('sigma', 0)
                
                if use_cuda and self.cuda_available:
                    gpu_filter = cv2.cuda.createGaussianFilter(
                        gpu_image.type(), gpu_image.type(), (ksize, ksize), sigma)
                    result_gpu = gpu_filter.apply(gpu_image)
                    result_image = result_gpu.download()
                else:
                    result_image = cv2.GaussianBlur(image, (ksize, ksize), sigma)
                
                info = {'ksize': ksize, 'sigma': sigma}
            
            elif operation == 'canny':
                threshold1 = params.get('threshold1', 50)
                threshold2 = params.get('threshold2', 150)
                
                if use_cuda and self.cuda_available:
                    gray_gpu = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
                    detector = cv2.cuda.createCannyEdgeDetector(threshold1, threshold2, 3, False)
                    edges_gpu = detector.detect(gray_gpu)
                    result_image = edges_gpu.download()
                    result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)
                else:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    result_image = cv2.Canny(gray, threshold1, threshold2)
                    result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)
                
                info = {'threshold1': threshold1, 'threshold2': threshold2}
            
            elif operation == 'threshold':
                threshold = params.get('threshold', 127)
                max_value = params.get('max_value', 255)
                threshold_type = params.get('type', cv2.THRESH_BINARY)
                
                if use_cuda and self.cuda_available:
                    gray_gpu = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
                    _, result_gpu = cv2.cuda.threshold(gray_gpu, threshold, max_value, threshold_type)
                    result_image = result_gpu.download()
                    result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)
                else:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    _, result_image = cv2.threshold(gray, threshold, max_value, threshold_type)
                    result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)
                
                info = {'threshold': threshold, 'max_value': max_value}
            
            elif operation == 'color_convert':
                conversion = params.get('conversion', 'BGR2GRAY')
                conversion_map = {
                    'BGR2GRAY': cv2.COLOR_BGR2GRAY,
                    'BGR2RGB': cv2.COLOR_BGR2RGB,
                    'BGR2HSV': cv2.COLOR_BGR2HSV,
                    'RGB2BGR': cv2.COLOR_RGB2BGR,
                    'HSV2BGR': cv2.COLOR_HSV2BGR,
                }
                
                code = conversion_map.get(conversion, cv2.COLOR_BGR2GRAY)
                
                if use_cuda and self.cuda_available:
                    if code in [cv2.COLOR_BGR2GRAY, cv2.COLOR_RGB2GRAY]:
                        result_gpu = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
                        result_image = result_gpu.download()
                        result_image = cv2.cvtColor(result_image, cv2.COLOR_GRAY2BGR)
                    elif code == cv2.COLOR_BGR2RGB:
                        result_gpu = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2BGRA)
                        result_image = result_gpu.download()
                        result_image = cv2.cvtColor(result_image, cv2.COLOR_BGRA2BGR)
                    else:
                        result_image = cv2.cvtColor(image, code)
                else:
                    result_image = cv2.cvtColor(image, code)
                
                info = {'conversion': conversion}
            
            else:
                raise ValueError(f"不支持的操作: {operation}")
            
            processing_time = time.time() - start_time
            
            return result_image, {
                'success': True,
                'message': '处理成功',
                'info': info,
                'processing_time': processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return image, {
                'success': False,
                'message': f'处理失败: {str(e)}',
                'info': {},
                'processing_time': processing_time
            }
    
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
    
    def process_video_file(self, file_path: str, operation: str, params: Dict, 
                          use_cuda: bool, publish: bool) -> Dict:
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {'success': False, 'message': f'无法打开视频文件: {file_path}'}
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            rospy.loginfo(f"📹 视频信息: FPS={fps}, 总帧数={frame_count}")
            
            total_processing_time = 0.0
            processed_frames = 0
            
            while not self.server.is_preempt_requested() and processed_frames < 100:
                ret, frame = cap.read()
                if not ret:
                    break
                
                result_image, result = self.process_image(frame, operation, params, use_cuda)
                
                if result['success']:
                    total_processing_time += result['processing_time']
                    processed_frames += 1
                    
                    if publish:
                        msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                        msg.header.stamp = rospy.Time.now()
                        msg.header.frame_id = "camera"
                        self.processed_image_pub.publish(msg)
                    
                    feedback = ImageProcessingFeedback()
                    feedback.frame_count = processed_frames
                    feedback.fps = fps
                    feedback.status = f"处理中: {processed_frames}/{min(100, frame_count)} 帧"
                    self.server.publish_feedback(feedback)
                else:
                    rospy.logerr(f"❌ 帧处理失败: {result['message']}")
                
                if processed_frames >= 100:
                    rospy.loginfo("⚠️  已处理 100 帧，停止")
                    break
            
            cap.release()
            
            avg_processing_time = total_processing_time / processed_frames if processed_frames > 0 else 0.0
            
            return {
                'success': True,
                'message': f'处理完成: {processed_frames} 帧',
                'processing_time': total_processing_time,
                'output_info': f'平均处理时间: {avg_processing_time:.3f}s/帧'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'视频处理失败: {str(e)}'}
    
    def process_camera_stream(self, camera_index: int, operation: str, params: Dict,
                              use_cuda: bool, publish: bool, duration: float = 10.0) -> Dict:
        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                return {'success': False, 'message': f'无法打开摄像头: {camera_index}'}
            
            rospy.loginfo(f"📹 摄像头 {camera_index} 已打开，开始处理...")
            rospy.loginfo(f"⏱️  处理时长: {duration} 秒")
            
            total_processing_time = 0.0
            processed_frames = 0
            start_time = time.time()
            
            while not self.server.is_preempt_requested() and (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if not ret:
                    rospy.logwarn("⚠️  无法读取帧，继续尝试...")
                    continue
                
                result_image, result = self.process_image(frame, operation, params, use_cuda)
                
                if result['success']:
                    total_processing_time += result['processing_time']
                    processed_frames += 1
                    
                    if publish:
                        msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                        msg.header.stamp = rospy.Time.now()
                        msg.header.frame_id = "camera"
                        self.processed_image_pub.publish(msg)
                    
                    feedback = ImageProcessingFeedback()
                    feedback.frame_count = processed_frames
                    feedback.fps = processed_frames / (time.time() - start_time)
                    feedback.status = f"处理中: {processed_frames} 帧"
                    self.server.publish_feedback(feedback)
                else:
                    rospy.logerr(f"❌ 帧处理失败: {result['message']}")
            
            cap.release()
            
            avg_processing_time = total_processing_time / processed_frames if processed_frames > 0 else 0.0
            
            rospy.loginfo(f"📹 实时处理完成: 处理了 {processed_frames} 帧")
            
            return {
                'success': True,
                'message': f'处理完成: {processed_frames} 帧',
                'processing_time': total_processing_time,
                'output_info': f'平均处理时间: {avg_processing_time:.3f}s/帧'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'摄像头处理失败: {str(e)}'}
    
    def execute(self, goal):
        result = ImageProcessingResult()
        
        input_type = goal.input_type
        input_source = goal.input_source
        operation = goal.operation
        use_cuda = goal.use_cuda
        publish_processed = goal.publish_processed
        
        try:
            params = json.loads(goal.params) if goal.params else {}
        except:
            params = {}
        
        rospy.loginfo(f"🎯 处理请求: 类型={input_type}, 源={input_source}")
        rospy.loginfo(f"⚙️  操作: {operation}, CUDA={'是' if use_cuda else '否'}")
        rospy.loginfo(f"📝 参数: {params}")
        
        processing_result = None
        original_image = None
        
        if input_type == 'topic':
            rospy.loginfo(f"📷 从话题获取图像: {input_source}")
            original_image = self.get_image_from_topic(input_source)
            if original_image is None:
                self.server.set_aborted()
                return
            
            result_image, processing_result = self.process_image(original_image, operation, params, use_cuda)
            
            if processing_result['success'] and publish_processed:
                msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                msg.header.stamp = rospy.Time.now()
                msg.header.frame_id = "camera"
                self.processed_image_pub.publish(msg)
        
        elif input_type == 'image_file':
            rospy.loginfo(f"📄 从文件读取图像: {input_source}")
            original_image = self.get_image_from_file(input_source)
            if original_image is None:
                self.server.set_aborted()
                return
            
            result_image, processing_result = self.process_image(original_image, operation, params, use_cuda)
            
            if processing_result['success'] and publish_processed:
                msg = self.bridge.cv2_to_imgmsg(result_image, encoding="bgr8")
                msg.header.stamp = rospy.Time.now()
                msg.header.frame_id = "camera"
                self.processed_image_pub.publish(msg)
        
        elif input_type == 'camera':
            camera_index = int(input_source) if input_source.isdigit() else 0
            rospy.loginfo(f"📹 实时摄像头处理: {camera_index}")
            processing_result = self.process_camera_stream(camera_index, operation, params, use_cuda, publish_processed)
        
        elif input_type == 'video_file':
            rospy.loginfo(f"🎬 处理视频文件: {input_source}")
            processing_result = self.process_video_file(input_source, operation, params, use_cuda, publish_processed)
        
        else:
            rospy.logerr(f"❌ 不支持的输入类型: {input_type}")
            self.server.set_aborted()
            return
        
        result.success = processing_result.get('success', False)
        result.message = processing_result.get('message', '未知错误')
        result.processing_time = processing_result.get('processing_time', 0.0)
        result.output_info = processing_result.get('output_info', '')
        
        rospy.loginfo(f"{'✅' if result.success else '❌'} 处理完成: {result.message}")
        rospy.loginfo(f"⏱️  处理时间: {result.processing_time:.3f}s")
        
        self.server.set_succeeded(result)
    
    def run(self):
        rospy.loginfo("🎯 等待 Action 目标...")
        rospy.spin()


if __name__ == '__main__':
    try:
        server = OpenCVImageProcessingServer()
        server.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")