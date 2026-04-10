#!/usr/bin/env python3

import rospy
import actionlib
import sys
from opencv_cuda_pkg.msg import DetectionResult
from opencv_cuda_pkg.msg import OpenCVDetectionAction, OpenCVDetectionGoal, OpenCVDetectionResult, OpenCVDetectionFeedback


class OpenCVDetectionClient:
    def __init__(self):
        rospy.init_node('opencv_detection_client', anonymous=True)
        
        self.client = actionlib.SimpleActionClient('opencv_detection', OpenCVDetectionAction)
        rospy.loginfo("🔍 等待服务器启动...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 服务器已连接")

    def send_goal(self, input_type: str, input_source: str, detection_method: str = 'haar_cascade',
                  model_path: str = '', cascade_path: str = '', confidence_threshold: float = 0.5,
                  nms_threshold: float = 0.4, use_cuda: bool = True, publish: bool = True):
        goal = OpenCVDetectionGoal()
        goal.input_type = input_type
        goal.input_source = input_source
        goal.detection_method = detection_method
        goal.model_path = model_path
        goal.cascade_path = cascade_path
        goal.confidence_threshold = confidence_threshold
        goal.nms_threshold = nms_threshold
        goal.use_cuda = use_cuda
        goal.publish_processed = publish
        
        rospy.loginfo(f"📤 发送检测目标:")
        rospy.loginfo(f"  类型: {input_type}")
        rospy.loginfo(f"  源: {input_source}")
        rospy.loginfo(f"  方法: {detection_method}")
        rospy.loginfo(f"  CUDA: {'是' if use_cuda else '否'}")
        rospy.loginfo(f"  置信度: {confidence_threshold}")
        
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
        print("📊 OpenCV 目标检测结果")
        print("="*60)
        print(f"检测到的目标数量: {result.num_detections}")
        print(f"推理时间: {result.inference_time:.3f} 秒")
        
        if result.frames_processed > 1:
            print(f"处理帧数: {result.frames_processed}")
            print(f"平均推理时间: {result.avg_inference_time:.3f} 秒")
        
        if result.num_detections > 0:
            print("\n检测结果详情:")
            print("-" * 60)
            
            for i, det in enumerate(result.detections, 1):
                print(f"\n  [{i}] {det.class_name} (置信度: {det.confidence:.2f})")
                print(f"      边界框: ({det.x1:.0f}, {det.y1:.0f}) -> ({det.x2:.0f}, {det.y2:.0f})")
                print(f"      中心点: ({det.center_x:.0f}, {det.center_y:.0f})")
                print(f"      面积: {det.area:.0f} 像素²")
        else:
            print("\n⚠️  未检测到任何目标")
        
        print("="*60 + "\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenCV 目标检测客户端')
    parser.add_argument('--type', required=True, choices=['topic', 'image_file', 'camera', 'video_file'],
                       help='输入类型: topic, image_file, camera, video_file')
    parser.add_argument('--source', required=True, help='输入源: 话题名/文件路径/摄像头索引')
    parser.add_argument('--method', default='haar_cascade',
                       choices=['haar_cascade', 'hog', 'dnn'],
                       help='检测方法: haar_cascade, hog, dnn')
    parser.add_argument('--model', default='', help='模型文件路径（用于 DNN）')
    parser.add_argument('--cascade', default='', help='Cascade 文件路径（用于 Haar）')
    parser.add_argument('--conf', type=float, default=0.5, help='置信度阈值')
    parser.add_argument('--nms', type=float, default=0.4, help='NMS 阈值')
    parser.add_argument('--no-cuda', action='store_true', help='禁用 CUDA')
    parser.add_argument('--no-publish', action='store_true', help='不发布处理后的图像')
    
    args = parser.parse_args()
    
    client = OpenCVDetectionClient()
    
    try:
        result = client.send_goal(
            input_type=args.type,
            input_source=args.source,
            detection_method=args.method,
            model_path=args.model,
            cascade_path=args.cascade,
            confidence_threshold=args.conf,
            nms_threshold=args.nms,
            use_cuda=not args.no_cuda,
            publish=not args.no_publish
        )
        
        if result and result.num_detections >= 0:
            rospy.loginfo("✅ 检测成功完成")
            sys.exit(0)
        else:
            rospy.logerr("❌ 检测失败")
            sys.exit(1)
            
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
        sys.exit(1)
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
        sys.exit(1)


if __name__ == '__main__':
    main()