#!/usr/bin/env python3

import rospy
import actionlib
import sys
import json
from opencv_cuda_pkg.msg import ImageProcessingAction, ImageProcessingGoal, ImageProcessingResult, ImageProcessingFeedback


class ImageProcessingClient:
    def __init__(self):
        rospy.init_node('image_processing_client', anonymous=True)
        
        self.client = actionlib.SimpleActionClient('image_processing', ImageProcessingAction)
        rospy.loginfo("🔍 等待服务器启动...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 服务器已连接")

    def send_goal(self, input_type: str, input_source: str, operation: str,
                  params: dict = None, use_cuda: bool = True, publish: bool = True):
        goal = ImageProcessingGoal()
        goal.input_type = input_type
        goal.input_source = input_source
        goal.operation = operation
        goal.params = json.dumps(params) if params else ''
        goal.use_cuda = use_cuda
        goal.publish_processed = publish
        
        rospy.loginfo(f"📤 发送处理目标:")
        rospy.loginfo(f"  类型: {input_type}")
        rospy.loginfo(f"  源: {input_source}")
        rospy.loginfo(f"  操作: {operation}")
        rospy.loginfo(f"  CUDA: {'是' if use_cuda else '否'}")
        if params:
            rospy.loginfo(f"  参数: {params}")
        
        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        
        self.client.wait_for_result()
        
        result = self.client.get_result()
        
        self.display_result(result)
        
        return result

    def feedback_callback(self, feedback):
        rospy.loginfo(f"📊 反馈: {feedback.status} (帧: {feedback.frame_count})")

    def display_result(self, result):
        if not result:
            rospy.logerr("❌ 没有收到结果")
            return
        
        print("\n" + "="*60)
        print("📊 OpenCV 图像处理结果")
        print("="*60)
        print(f"成功: {'是' if result.success else '否'}")
        print(f"消息: {result.message}")
        print(f"处理时间: {result.processing_time:.3f} 秒")
        if result.output_info:
            print(f"输出信息: {result.output_info}")
        print("="*60 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenCV 图像处理客户端')
    parser.add_argument('--type', required=True, choices=['topic', 'image_file', 'camera', 'video_file'],
                       help='输入类型: topic, image_file, camera, video_file')
    parser.add_argument('--source', required=True, help='输入源: 话题名/文件路径/摄像头索引')
    parser.add_argument('--operation', required=True,
                       choices=['resize', 'crop', 'rotate', 'blur', 'gaussian_blur', 'canny', 'threshold', 'color_convert'],
                       help='操作类型')
    parser.add_argument('--params', default='{}', help='操作参数（JSON 格式）')
    parser.add_argument('--no-cuda', action='store_true', help='禁用 CUDA')
    parser.add_argument('--no-publish', action='store_true', help='不发布处理后的图像')
    
    args = parser.parse_args()
    
    client = ImageProcessingClient()
    
    try:
        params = json.loads(args.params) if args.params else {}
        result = client.send_goal(
            input_type=args.type,
            input_source=args.source,
            operation=args.operation,
            params=params,
            use_cuda=not args.no_cuda,
            publish=not args.no_publish
        )
        
        if result and result.success:
            rospy.loginfo("✅ 处理成功完成")
            sys.exit(0)
        else:
            rospy.logerr("❌ 处理失败")
            sys.exit(1)
            
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
        sys.exit(1)
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
        sys.exit(1)


if __name__ == '__main__':
    main()