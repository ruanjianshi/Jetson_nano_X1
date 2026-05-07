#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
形状检测服务器 (Shape Detection Server)
==========================================
基于 OpenCV 轮廓分析的实时形状检测 ROS Action 服务端。

检测原理:
  1. 自适应阈值(adaptiveThreshold) + 大津阈值(Otsu) 双通道二值化
  2. 提取外轮廓, 过滤小面积噪声
  3. approxPolyDP 多边形近似 + 圆形度/矩形度/坚固度多特征融合判断
  4. 通过面积反比估算距离(需标定)

已知限制 (Known Issues):
  - 对光照变化敏感, 强光/阴影导致检测不稳定
  - 需要前景形状与背景有明显对比度
  - 复杂纹理背景会产生大量误检
  - approxPolyDP 顶点数在边缘不清晰时跳变, 导致形状误判

优化方向 (TODO):
  - [ ] 使用深度学习模型 (轻量CNN) 做形状分类, 替代特征工程
  - [ ] 增加背景建模/减除, 分离前景形状
  - [ ] 结合颜色追踪做 ROI 区域约束
  - [ ] 边缘增强 (CLAHE 直方图均衡化)
  - [ ] 多帧融合/卡尔曼滤波稳定检测结果

ROS 接口:
  Action:  /shape_detection (ShapeDetection)
  话题:    /shape_detection/result_image  检测结果图像
           /shape_detection/debug        二值化调试面板(adaptive | otsu)

参数参考:
  adaptiveThreshold: blockSize=15, C=3, 椭圆核 CLOSE 1次
  Otsu:             THRESH_BINARY_INV, 椭圆核 CLOSE 1次
  approxPolyDP:     epsilon1=0.015*peri, epsilon2=0.025*peri
"""

import rospy
import actionlib
import cv2
import numpy as np
import time
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from opencv_cuda_pkg.msg import ShapeDetectionAction, ShapeDetectionGoal, ShapeDetectionResult, ShapeDetectionFeedback

# 每种形状的绘制颜色 (BGR)
SHAPE_COLORS = {
    'triangle': (0, 255, 255),   # 黄色
    'square': (0, 255, 0),        # 绿色
    'rectangle': (255, 0, 0),     # 蓝色
    'pentagon': (255, 0, 255),    # 紫色
    'hexagon': (0, 165, 255),     # 橙色
    'circle': (0, 0, 255),        # 红色
    'ellipse': (255, 128, 0),     # 深橙
    'unknown': (128, 128, 128)    # 灰色
}

class ShapeDetectionServer:
    """形状检测 ROS Action 服务端"""

    def __init__(self):
        rospy.init_node('shape_detection_server', anonymous=True)

        self.bridge = CvBridge()
        self.cap = None            # OpenCV VideoCapture 对象
        self.current_fps = 0.0     # 当前帧率

        # 发布检测结果图像
        self.image_pub = rospy.Publisher(
            '/shape_detection/result_image',
            Image,
            queue_size=1
        )
        # 发布调试二值化图像 (adaptive 和 otsu 并列)
        self.debug_pub = rospy.Publisher(
            '/shape_detection/debug',
            Image,
            queue_size=1
        )

        # Action 服务端
        self.server = actionlib.SimpleActionServer(
            'shape_detection',
            ShapeDetectionAction,
            self.execute_callback,
            False
        )
        self.server.start()

        rospy.loginfo("✅ 形状检测服务器已启动")
        rospy.loginfo("📤 /shape_detection/result_image  /shape_detection/debug")

    def multi_threshold(self, gray):
        """
        多方法二值化融合: adaptiveThreshold(主) + Otsu(辅)
        返回两个二值化 mask
        """
        # 高斯模糊降噪
        blur = cv2.GaussianBlur(gray, (7, 7), 0)

        # 方法1: 自适应高斯阈值 (对局部光照变化鲁棒)
        #  blockSize=15, C=3 => 更大的块, 更平滑的分割
        th1 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 15, 3)

        # 椭圆核形态学闭运算: 连接断裂轮廓, 填充小孔洞
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        th1 = cv2.morphologyEx(th1, cv2.MORPH_CLOSE, kernel)

        # 方法2: 大津全局阈值 (作为备用方案)
        _, th2 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        th2 = cv2.morphologyEx(th2, cv2.MORPH_CLOSE, kernel)

        return [th1, th2]

    def detect_shape(self, cnt):
        """
        形状识别核心算法

        特征融合策略:
          1. solidity (坚固度): area / hull_area, 过滤不规则轮廓
          2. circularity (圆形度): 4*pi*area/peri^2, 区分圆/多边形
          3. rectangularity (矩形度): area / minAreaRect_area, 区分矩形/其他
          4. approxPolyDP 双精度顶点数: 粗/细两个 epsilon 综合判断

        返回: (shape_name, vertices, circularity)
        """
        area = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        if peri == 0 or area == 0:
            return 'unknown', 0, 0.0

        # 坚固度: 过滤非凸/不规则轮廓 (如背景纹理)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        if solidity < 0.70:
            return 'unknown', 0, 0.0

        # 圆形度: 1.0=完美圆, 0.78=正方形, 0.60=正三角形
        circ = 4 * np.pi * area / (peri * peri)

        # 矩形度: 轮廓面积 / 最小外接矩形面积
        rect = cv2.minAreaRect(cnt)
        box = cv2.boxPoints(rect)
        box = box.astype(int)
        box_area = cv2.contourArea(box)
        rectang = area / box_area if box_area > 0 else 0

        # 双精度多边形近似 (两套参数综合判断, 减少顶点数跳变)
        epsilon1 = 0.015 * peri     # 高精度
        approx1 = cv2.approxPolyDP(cnt, epsilon1, True)
        v1 = len(approx1)

        epsilon2 = 0.025 * peri     # 低精度 (更稳定)
        approx2 = cv2.approxPolyDP(cnt, epsilon2, True)
        v2 = len(approx2)

        # ---- 圆形判断 ----
        if circ > 0.80:
            # 高圆形度但顶点为4: 可能是正方形(特例)
            if 0.85 <= rectang <= 1.0 and v2 == 4:
                x, y, w, h = cv2.boundingRect(approx2)
                ratio = float(w) / h if h > 0 else 0
                if 0.80 <= ratio <= 1.20:
                    return 'square', 4, circ
                return 'rectangle', 4, circ
            return 'circle', v1, circ

        # ---- 三角形 ----
        if v2 == 3:
            return 'triangle', 3, circ

        # ---- 四边形 (正方形/长方形) ----
        if v2 == 4:
            x, y, w, h = cv2.boundingRect(approx2)
            ratio = float(w) / h if h > 0 else 0
            if 0.80 <= ratio <= 1.20:
                return 'square', 4, circ
            return 'rectangle', 4, circ

        # ---- 五边形 / 六边形 ----
        if v2 == 5:
            return 'pentagon', 5, circ

        if v2 == 6:
            return 'hexagon', 6, circ

        # ---- 多顶点圆形 (边缘粗糙的圆) ----
        if v2 >= 8 and circ > 0.55:
            return 'circle', v1, circ

        # ---- 降级判断 ----
        if circ > 0.70 and v1 <= 6:
            return 'unknown', v1, circ

        if v2 <= 6:
            return 'polygon', v2, circ

        return 'unknown', v1, circ

    def draw_shape(self, frame, cnt, shape_name, cx, cy, area, vertices, distance):
        """
        在图像上绘制检测结果

        绘制内容:
          - 轮廓线 (彩色)
          - 中心点 (圆点)
          - 形状名 + 坐标 + 距离
          - 面积(A) + 顶点数(V) + 圆形度(C)
          - 边界框 (黄色矩形)
        """
        color = SHAPE_COLORS.get(shape_name, (128, 128, 128))

        # 轮廓线
        cv2.drawContours(frame, [cnt], -1, color, 2)
        # 中心点
        cv2.circle(frame, (cx, cy), 3, (0, 0, 0), -1)
        cv2.circle(frame, (cx, cy), 2, color, -1)

        # 标注: 形状名 + 坐标 + 距离
        label = f"{shape_name.upper()} ({cx},{cy}) D:{distance:.1f}cm"
        cv2.putText(frame, label, (cx - 70, cy - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

        # 标注: 面积/顶点数/圆形度
        peri = cv2.arcLength(cnt, True)
        circ = 4 * np.pi * area / (peri * peri) if peri > 0 else 0
        info = f"A:{area:.0f} V:{vertices} C:{circ:.2f}"
        cv2.putText(frame, info, (cx - 70, cy + 3),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 200, 200), 1)

        # 边界框
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 1)

        return frame

    def estimate_distance(self, area, ref_area, ref_distance):
        """
        基于面积的简单距离估算

        原理: 物体距离越远, 成像面积越小, 面积与距离平方成反比
        distance = sqrt(ref_area / area) * ref_distance

        需要标定: ref_distance(参考距离, cm) 和 ref_area(参考面积, 像素)
        """
        if area <= 0 or ref_area <= 0:
            return 999.9
        return min(np.sqrt(ref_area / area) * ref_distance, 999.9)

    def execute_callback(self, goal):
        """
        Action 回调: 处理客户端请求, 启动形状检测主循环
        """
        rospy.loginfo(f"🎯 检测: 形状={goal.shape_name}")

        result = ShapeDetectionResult()
        result.success = False

        # 参数校验
        target_shape = goal.shape_name.lower()
        valid_shapes = ['triangle', 'square', 'rectangle', 'pentagon', 'hexagon', 'circle', 'all']
        if target_shape not in valid_shapes:
            result.message = f"不支持的形状: {target_shape}"
            self.server.set_aborted(result)
            return

        # 打开摄像头
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(goal.camera_index if goal.camera_index >= 0 else 0)

        if not self.cap.isOpened():
            result.message = f"无法打开摄像头"
            self.server.set_aborted(result)
            return

        # 设置分辨率
        width = goal.width if goal.width > 0 else 640
        height = goal.height if goal.height > 0 else 480
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 读取参数
        min_area = max(300, goal.min_area)
        publish_image = goal.publish_image
        ref_distance = goal.ref_distance if goal.ref_distance > 0 else 50.0
        ref_area = goal.ref_area if goal.ref_area > 0 else 10000.0

        rospy.loginfo(f"📷 {width}x{height}, min_area={min_area}, 参考: {ref_distance}cm @ 面积{ref_area}")

        # 统计变量
        total_frames = 0
        total_detections = 0
        start_time = time.time()
        fps_time = start_time
        fps_counter = 0
        current_fps = 0.0
        last_activity = time.time()

        # ---- 主检测循环 ----
        while not rospy.is_shutdown():
            # 抢占/超时检查
            if self.server.is_preempt_requested():
                rospy.loginfo("📛 抢占")
                break
            if time.time() - last_activity > 30.0:
                rospy.logwarn("⚠️ 超时")
                break

            ret, frame = self.cap.read()
            if not ret:
                break

            detect_start = time.time()

            # Step 1: 灰度化 + 多方法二值化
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            masks = self.multi_threshold(gray)

            # Step 2: 提取轮廓 (两通道分别提取, 按面积过滤后去重)
            all_contours = {}
            for mi, mask in enumerate(masks):
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area < min_area:
                        continue
                    all_contours.setdefault(mi, []).append((cnt, area))

            # Step 3: 去重 (同一轮廓可能被两通道检测到)
            detections = []
            seen = set()
            for mi in sorted(all_contours.keys()):  # 优先 adaptive(0) 的结果
                for cnt, area in all_contours[mi]:
                    # 用轮廓首4点做简易去重 key
                    approx_key = tuple(map(int, cnt.ravel()[:4]))
                    if approx_key in seen:
                        continue
                    seen.add(approx_key)

                    # Step 4: 形状分类
                    shape_name, vertices, circ = self.detect_shape(cnt)
                    if shape_name == 'unknown':
                        continue
                    if target_shape != 'all' and shape_name != target_shape:
                        continue

                    # 计算中心点
                    M = cv2.moments(cnt)
                    if M['m00'] == 0:
                        continue
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])

                    # 距离估算
                    dist = self.estimate_distance(area, ref_area, ref_distance)

                    detections.append({
                        'shape': shape_name,
                        'center': (cx, cy),
                        'area': area,
                        'contour': cnt,
                        'vertices': vertices,
                        'distance': dist
                    })

            # FPS 统计
            total_frames += 1
            total_detections += len(detections)
            fps_counter += 1
            if time.time() - fps_time >= 1.0:
                current_fps = fps_counter / (time.time() - fps_time)
                fps_counter = 0
                fps_time = time.time()

            # 发布结果图像 (无论是否检测到)
            if publish_image:
                display = frame.copy()
                for det in detections:
                    display = self.draw_shape(display, det['contour'], det['shape'],
                                            det['center'][0], det['center'][1],
                                            det['area'], det['vertices'], det['distance'])

                if not detections:
                    cv2.putText(display, "NONE", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                img_msg = self.bridge.cv2_to_imgmsg(display, encoding="bgr8")
                img_msg.header.stamp = rospy.Time.now()
                self.image_pub.publish(img_msg)

                # 调试图像: adaptive | otsu 并列显示
                m1 = cv2.cvtColor(masks[0], cv2.COLOR_GRAY2BGR)
                m2 = cv2.cvtColor(masks[1], cv2.COLOR_GRAY2BGR)
                debug_img = np.hstack([m1, m2])
                cv2.putText(debug_img, "adaptive", (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                cv2.putText(debug_img, "otsu", (m1.shape[1]+5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                debug_msg = self.bridge.cv2_to_imgmsg(debug_img, encoding="bgr8")
                debug_msg.header.stamp = rospy.Time.now()
                self.debug_pub.publish(debug_msg)

            self.current_fps = current_fps

            # 发送反馈
            feedback = ShapeDetectionFeedback()
            feedback.frame_count = total_frames
            feedback.fps = current_fps

            if detections:
                det = detections[0]
                feedback.detected_shape = det['shape']
                feedback.status = f"{det['shape'].upper()} X:{det['center'][0]} Y:{det['center'][1]} D:{det['distance']:.1f}cm A:{det['area']:.0f} FPS:{current_fps:.1f}"
            else:
                feedback.detected_shape = 'none'
                t = target_shape.upper() if target_shape != 'all' else 'ANY'
                feedback.status = f"未检测到 {t} | FPS:{current_fps:.1f}"

            feedback.detections_count = len(detections)
            feedback.processing_time = time.time() - detect_start
            self.server.publish_feedback(feedback)
            last_activity = time.time()

        # 清理
        if self.cap is not None:
            self.cap.release()

        # 填充结果
        elapsed = time.time() - start_time
        result.success = True
        result.message = f"完成: {target_shape}"
        result.num_detections = total_detections
        result.total_time = elapsed
        result.avg_fps = total_frames / elapsed if elapsed > 0 else 0.0

        if self.server.is_preempt_requested():
            self.server.set_preempted(result)
        else:
            self.server.set_succeeded(result)

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    try:
        ShapeDetectionServer().run()
    except Exception as e:
        rospy.logerr(f"❌ {e}")
