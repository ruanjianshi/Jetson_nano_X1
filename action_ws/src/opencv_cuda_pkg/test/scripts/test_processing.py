#!/usr/bin/env python3

import rospy
import actionlib
import cv2
import os
import json
from cv_bridge import CvBridge
from opencv_cuda_pkg.msg import ImageProcessingAction, ImageProcessingGoal
from sensor_msgs.msg import Image

class ImageProcessingSaver:
    def __init__(self):
        rospy.init_node('image_processing_saver', anonymous=True)
        
        self.bridge = CvBridge()
        self.processed_image = None
        self.result_received = False
        
        self.client = actionlib.SimpleActionClient('image_processing', ImageProcessingAction)
        
        rospy.loginfo("🔍 等待服务器启动...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 服务器已连接")
        
        self.image_sub = rospy.Subscriber('/opencv/processed_image', Image, self.image_callback)
    
    def image_callback(self, msg):
        self.processed_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        self.result_received = True
        rospy.loginfo("✅ 收到处理后的图像")
    
    def process_and_save(self, input_source: str, operation: str, 
                        params: dict = None, use_cuda: bool = True, 
                        save_path: str = None):
        goal = ImageProcessingGoal()
        goal.input_type = 'image_file'
        goal.input_source = input_source
        goal.operation = operation
        goal.params = json.dumps(params) if params else ''
        goal.use_cuda = use_cuda
        goal.publish_processed = True
        
        rospy.loginfo(f"📤 发送处理目标:")
        rospy.loginfo(f"  源: {input_source}")
        rospy.loginfo(f"  操作: {operation}")
        rospy.loginfo(f"  CUDA: {'是' if use_cuda else '否'}")
        if params:
            rospy.loginfo(f"  参数: {params}")
        
        self.client.send_goal(goal)
        
        rospy.loginfo("⏳ 等待处理结果...")
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        if result.success:
            rospy.loginfo(f"✅ 处理成功: {result.message}")
            rospy.loginfo(f"⏱️  处理时间: {result.processing_time:.3f} 秒")
            
            if save_path and self.processed_image is not None:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                cv2.imwrite(save_path, self.processed_image)
                rospy.loginfo(f"💾 结果已保存: {save_path}")
        else:
            rospy.logerr(f"❌ 处理失败: {result.message}")
        
        return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenCV 图像处理并保存结果')
    parser.add_argument('--source', required=True, help='输入图像文件路径')
    parser.add_argument('--operation', required=True,
                       choices=['resize', 'crop', 'rotate', 'blur', 'gaussian_blur', 'canny', 'threshold', 'color_convert'],
                       help='操作类型')
    parser.add_argument('--params', default='{}', help='操作参数（JSON 格式）')
    parser.add_argument('--save', required=True, help='保存处理结果的路径')
    parser.add_argument('--no-cuda', action='store_true', help='禁用 CUDA')
    
    args = parser.parse_args()
    
    saver = ImageProcessingSaver()
    
    try:
        params = json.loads(args.params) if args.params else {}
        result = saver.process_and_save(
            input_source=args.source,
            operation=args.operation,
            params=params,
            use_cuda=not args.no_cuda,
            save_path=args.save
        )
        
        if result and result.success:
            rospy.loginfo("✅ 完成")
            rospy.signal_shutdown("Success")
        else:
            rospy.logerr("❌ 处理失败")
            rospy.signal_shutdown("Failed")
            
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")


if __name__ == '__main__':
    main()