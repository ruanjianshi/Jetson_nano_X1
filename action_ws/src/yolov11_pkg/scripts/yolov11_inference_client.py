#!/usr/bin/env python3

import rospy
import actionlib
import sys
from yolov11_pkg.msg import Yolov11InferenceAction, Yolov11InferenceGoal, Yolov11InferenceResult, Yolov11InferenceFeedback
from yolov11_pkg.msg import DetectionResult


class YOLOv11InferenceClient:
    def __init__(self):
        rospy.init_node('yolov11_inference_client', anonymous=True)
        
        self.client = actionlib.SimpleActionClient('yolov11_inference', Yolov11InferenceAction)
        rospy.loginfo("🔍 等待服务器启动...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 服务器已连接")

    def send_goal(self, input_type: str, input_source: str, 
                  model_path: str = '', confidence_threshold: float = 0.5,
                  iou_threshold: float = 0.45, device: str = 'cuda:0',
                  save_image_path: str = ''):
        goal = Yolov11InferenceGoal()
        goal.model_path = model_path
        goal.input_type = input_type
        goal.input_source = input_source
        goal.confidence_threshold = confidence_threshold
        goal.iou_threshold = iou_threshold
        goal.device = device
        goal.save_image_path = save_image_path
        
        rospy.loginfo(f"📤 发送推理目标:")
        rospy.loginfo(f"  类型: {input_type}")
        rospy.loginfo(f"  源: {input_source}")
        if model_path:
            rospy.loginfo(f"  模型: {model_path}")
        rospy.loginfo(f"  参数: conf={confidence_threshold}, iou={iou_threshold}, device={device}")
        
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
        print("📊 YOLOv11 推理结果")
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
    import rospkg
    
    parser = argparse.ArgumentParser(description='YOLOv11 推理客户端')
    parser.add_argument('--type', required=True, choices=['topic', 'image_file', 'camera', 'video_file'],
                       help='输入类型: topic, image_file, camera, video_file')
    parser.add_argument('--source', required=True, help='输入源: 话题名/文件路径/摄像头索引')
    parser.add_argument('--model', default='', help='模型文件路径（可选）')
    parser.add_argument('--conf', type=float, default=0.5, help='置信度阈值')
    parser.add_argument('--iou', type=float, default=0.45, help='IOU 阈值')
    parser.add_argument('--device', default='cuda:0', help='设备 (cuda:0 或 cpu)')
    parser.add_argument('--save', default='', help='保存推理结果图片的路径（仅对图像文件有效）')
    
    args = parser.parse_args()
    
    client = YOLOv11InferenceClient()
    
    try:
        result = client.send_goal(
            input_type=args.type,
            input_source=args.source,
            model_path=args.model,
            confidence_threshold=args.conf,
            iou_threshold=args.iou,
            device=args.device,
            save_image_path=args.save
        )
        
        if result and result.num_detections >= 0:
            rospy.loginfo("✅ 推理成功完成")
            sys.exit(0)
        else:
            rospy.logerr("❌ 推理失败")
            sys.exit(1)
            
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
        sys.exit(1)
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
        sys.exit(1)


if __name__ == '__main__':
    main()