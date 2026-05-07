#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
形状检测客户端 (Shape Detection Client)
==========================================
ROS Action 客户端, 向 shape_detection 服务器发送形状检测请求。

用法:
  rosrun opencv_cuda_pkg shape_detection_client.py --shape circle
  rosrun opencv_cuda_pkg shape_detection_client.py --shape all --ref-distance 50 --ref-area 10000

参数:
  --shape      检测形状: triangle / square / rectangle / pentagon / hexagon / circle / all
  --camera     摄像头索引 (默认 0)
  --width      图像宽度 (默认 640)
  --height     图像高度 (默认 480)
  --min-area   最小面积过滤 (默认 1000)
  --ref-distance  参考距离 cm (默认 50.0)
  --ref-area      参考面积 像素 (默认 10000.0)
  --list       显示支持的形状列表
"""

import rospy
import actionlib
import sys
from opencv_cuda_pkg.msg import ShapeDetectionAction, ShapeDetectionGoal, ShapeDetectionResult, ShapeDetectionFeedback

SHAPE_LIST = ['triangle', 'square', 'rectangle', 'pentagon', 'hexagon', 'circle', 'all']

class ShapeDetectionClient:
    """形状检测 Action 客户端"""

    def __init__(self):
        rospy.init_node('shape_detection_client', anonymous=True)

        self.client = actionlib.SimpleActionClient('shape_detection', ShapeDetectionAction)
        rospy.loginfo("🔍 等待形状检测服务器启动...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 服务器已连接")

    def send_goal(self, shape_name='all', camera_index=0, width=640, height=480,
                  min_area=1000, similarity=0.8, publish_image=True,
                  ref_distance=50.0, ref_area=10000.0):
        """发送检测目标到服务端"""
        goal = ShapeDetectionGoal()
        goal.shape_name = shape_name
        goal.camera_index = camera_index
        goal.width = width
        goal.height = height
        goal.min_area = min_area
        goal.similarity = similarity
        goal.publish_image = publish_image
        goal.ref_distance = ref_distance
        goal.ref_area = ref_area

        rospy.loginfo(f"📤 发送检测目标:")
        rospy.loginfo(f"  形状: {shape_name}")
        rospy.loginfo(f"  摄像头: {camera_index}")
        rospy.loginfo(f"  分辨率: {width}x{height}")
        rospy.loginfo(f"  最小面积: {min_area}")
        rospy.loginfo(f"  参考标定: {ref_distance}cm @ 面积{ref_area}")

        self.client.send_goal(goal, feedback_cb=self.feedback_callback)
        self.client.wait_for_result()

        result = self.client.get_result()
        self.display_result(result)
        return result

    def feedback_callback(self, feedback):
        """接收并显示实时反馈 (坐标/距离/FPS)"""
        rospy.loginfo(f"📊 {feedback.status}")

    def display_result(self, result):
        """显示最终检测结果统计"""
        if not result:
            rospy.logerr("❌ 没有收到结果")
            return

        print("\n" + "=" * 60)
        print("🔷 形状检测结果")
        print("=" * 60)
        print(f"成功: {'是' if result.success else '否'}")
        print(f"消息: {result.message}")
        print(f"检测到的目标总数: {result.num_detections}")
        print(f"总处理时间: {result.total_time:.3f} 秒")
        print(f"平均帧率: {result.avg_fps:.2f} FPS")
        print("=" * 60 + "\n")

def show_shape_menu():
    print("\n" + "=" * 40)
    print("🔷 支持的形状:")
    print("=" * 40)
    for i, shape in enumerate(SHAPE_LIST, 1):
        print(f"  {i}. {shape}")
    print("=" * 40)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='形状检测客户端')
    parser.add_argument('--shape', '-s', type=str, default='all',
                       help=f'检测形状 (默认: all)')
    parser.add_argument('--camera', '-cam', type=int, default=0,
                       help='摄像头索引 (默认: 0)')
    parser.add_argument('--width', '-w', type=int, default=640,
                       help='图像宽度 (默认: 640)')
    parser.add_argument('--height', type=int, default=480,
                       help='图像高度 (默认: 480)')
    parser.add_argument('--min-area', '-a', type=int, default=1000,
                       help='最小面积 (默认: 1000)')
    parser.add_argument('--no-publish', action='store_true',
                       help='不发布处理后图像')
    parser.add_argument('--list', '-l', action='store_true',
                       help='显示支持的形状列表')
    parser.add_argument('--ref-distance', type=float, default=50.0,
                       help='参考距离(cm) (默认: 50.0)')
    parser.add_argument('--ref-area', type=float, default=10000.0,
                       help='参考距离下的像素面积 (默认: 10000)')

    args = parser.parse_args()

    if args.list:
        show_shape_menu()
        return

    shape = args.shape.lower()
    if shape not in SHAPE_LIST:
        rospy.logerr(f"❌ 不支持的形状: {shape}")
        show_shape_menu()
        sys.exit(1)

    client = ShapeDetectionClient()

    try:
        result = client.send_goal(
            shape_name=shape,
            camera_index=args.camera,
            width=args.width,
            height=args.height,
            min_area=args.min_area,
            publish_image=not args.no_publish,
            ref_distance=args.ref_distance,
            ref_area=args.ref_area
        )

        if result and result.success:
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
