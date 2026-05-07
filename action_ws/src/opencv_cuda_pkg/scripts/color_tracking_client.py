#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
import sys
from opencv_cuda_pkg.msg import ColorTrackingAction, ColorTrackingGoal, ColorTrackingResult, ColorTrackingFeedback

COLOR_LIST = ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'cyan', 'white', 'black']

class ColorTrackingClient:
    def __init__(self):
        rospy.init_node('color_tracking_client', anonymous=True)

        self.client = actionlib.SimpleActionClient('color_tracking', ColorTrackingAction)
        rospy.loginfo("🔍 等待颜色追踪服务器启动...")
        self.client.wait_for_server()
        rospy.loginfo("✅ 服务器已连接")

    def send_goal(self, color_name='red', camera_index=0, width=640, height=480,
                  min_area=500, publish_image=True, ref_distance=50.0, ref_area=10000.0):
        goal = ColorTrackingGoal()
        goal.color_name = color_name
        goal.camera_index = camera_index
        goal.width = width
        goal.height = height
        goal.min_area = min_area
        goal.publish_image = publish_image
        goal.ref_distance = ref_distance
        goal.ref_area = ref_area

        rospy.loginfo(f"📤 发送追踪目标:")
        rospy.loginfo(f"  颜色: {color_name}")
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
        rospy.loginfo(f"📊 {feedback.status} | FPS: {feedback.fps:.1f} | 处理时间: {feedback.processing_time*1000:.1f}ms")

    def display_result(self, result):
        if not result:
            rospy.logerr("❌ 没有收到结果")
            return

        print("\n" + "=" * 60)
        print("🔴 颜色追踪结果")
        print("=" * 60)
        print(f"成功: {'是' if result.success else '否'}")
        print(f"消息: {result.message}")
        print(f"检测到的目标总数: {result.num_detections}")
        print(f"总处理时间: {result.total_time:.3f} 秒")
        print(f"平均帧率: {result.avg_fps:.2f} FPS")
        print("=" * 60 + "\n")

def show_color_menu():
    print("\n" + "=" * 40)
    print("🎨 支持的颜色:")
    print("=" * 40)
    for i, color in enumerate(COLOR_LIST, 1):
        print(f"  {i}. {color}")
    print("=" * 40)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='颜色追踪客户端')
    parser.add_argument('--color', '-c', type=str, default='red',
                       help=f'追踪颜色 (默认: red)')
    parser.add_argument('--camera', '-cam', type=int, default=0,
                       help='摄像头索引 (默认: 0)')
    parser.add_argument('--width', '-w', type=int, default=640,
                       help='图像宽度 (默认: 640)')
    parser.add_argument('--height', type=int, default=480,
                       help='图像高度 (默认: 480)')
    parser.add_argument('--min-area', '-a', type=int, default=500,
                       help='最小检测面积 (默认: 500)')
    parser.add_argument('--no-publish', action='store_true',
                       help='不发布处理后图像')
    parser.add_argument('--list', '-l', action='store_true',
                       help='显示支持的颜色列表')
    parser.add_argument('--ref-distance', type=float, default=50.0,
                       help='参考距离(cm)，默认: 50.0')
    parser.add_argument('--ref-area', type=float, default=10000.0,
                       help='参考面积(像素)，默认: 10000')

    args = parser.parse_args()

    if args.list:
        show_color_menu()
        return

    color = args.color.lower()
    if color not in COLOR_LIST:
        rospy.logerr(f"❌ 不支持的颜色: {color}")
        show_color_menu()
        sys.exit(1)

    client = ColorTrackingClient()

    try:
        result = client.send_goal(
            color_name=color,
            camera_index=args.camera,
            width=args.width,
            height=args.height,
            min_area=args.min_area,
            publish_image=not args.no_publish,
            ref_distance=args.ref_distance,
            ref_area=args.ref_area
        )

        if result and result.success:
            rospy.loginfo("✅ 追踪成功完成")
            sys.exit(0)
        else:
            rospy.logerr("❌ 追踪失败")
            sys.exit(1)

    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
        sys.exit(1)
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
        sys.exit(1)

if __name__ == '__main__':
    main()
