#!/usr/bin/env python3

import os
import sys
import rospy
import numpy as np
import time
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from sim2real_pkg.msg import DetectionResult
from typing import List, Dict, Optional


class YOLOONNXInference:
    def __init__(self, model_path: str, use_gpu: bool = True):
        self.model_path = model_path
        self.input_shape = (1, 3, 640, 640)

        try:
            import onnxruntime as ort
            self.ort = ort
        except ImportError:
            rospy.logerr("❌ onnxruntime 未安装，请运行: pip3 install onnxruntime-gpu")
            raise

        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)

        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]
        self.input_shape = self.session.get_inputs()[0].shape

        rospy.loginfo(f"✅ ONNX Runtime 模型加载: {model_path}")
        rospy.loginfo(f"   输入: {self.input_names} {self.input_shape}")
        rospy.loginfo(f"   输出: {self.output_names}")
        rospy.loginfo(f"   GPU: {use_gpu}")

    def infer(self, image: np.ndarray, conf_thres: float = 0.5, iou_thres: float = 0.45) -> Dict:
        start_time = time.time()
        input_data = self._preprocess(image)

        try:
            outputs = self.session.run(self.output_names, {self.input_names[0]: input_data})
            inference_time = time.time() - start_time
            detections = self._postprocess(outputs[0], conf_thres, iou_thres)

            return {
                'success': True,
                'detections': detections,
                'inference_time': inference_time
            }
        except Exception as e:
            rospy.logerr(f"❌ ONNX Runtime 推理失败: {e}")
            return {'success': False, 'error': str(e)}

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        resized = cv2.resize(image, (self.input_shape[3], self.input_shape[2]))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = rgb.astype(np.float32) / 255.0
        transposed = np.transpose(normalized, (2, 0, 1))
        batched = np.expand_dims(transposed, axis=0)
        return np.ascontiguousarray(batched)

    def _postprocess(self, output: np.ndarray, conf_thres: float, iou_thres: float) -> List[Dict]:
        detections = []

        if output.ndim == 3:
            output = output.reshape(output.shape[0], -1)

        predictions = output.T if output.shape[0] > output.shape[1] else output

        for pred in predictions:
            if len(pred) < 5:
                continue

            obj_conf = float(pred[4])
            if obj_conf < conf_thres:
                continue

            class_id = int(np.argmax(pred[5:])) if len(pred) > 5 else 0
            class_conf = float(pred[5 + class_id]) if len(pred) > 5 else obj_conf
            total_conf = class_conf * obj_conf

            if total_conf < conf_thres:
                continue

            cx, cy, w, h = pred[0], pred[1], pred[2], pred[3]

            detections.append({
                'class_id': class_id,
                'class_name': f'class_{class_id}',
                'confidence': total_conf,
                'bbox': [float(cx - w/2), float(cy - h/2), float(cx + w/2), float(cy + h/2)],
                'center': [float(cx), float(cy)],
                'area': float(w * h)
            })

        detections.sort(key=lambda x: x['confidence'], reverse=True)
        if detections and iou_thres > 0:
            detections = self._nms(detections, iou_thres)

        return detections

    def _nms(self, detections: List[Dict], iou_thres: float) -> List[Dict]:
        if not detections:
            return []

        boxes = np.array([d['bbox'] for d in detections])
        scores = np.array([d['confidence'] for d in detections])

        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)

        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h

            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

            indices = np.where(iou <= iou_thres)[0]
            order = order[indices + 1]

        return [detections[i] for i in keep]


class YOLOTensorRTInference:
    def __init__(self, engine_path: str):
        self.model_path = engine_path
        self.input_shape = (1, 3, 640, 640)

        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit
            self.trt = trt
            self.cuda = cuda
        except ImportError as e:
            rospy.logerr(f"❌ TensorRT/pycuda 未安装: {e}")
            raise

        self.TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
        self.stream = cuda.Stream()

        with open(engine_path, 'rb') as f:
            engine_bytes = f.read()

        runtime = trt.Runtime(self.TRT_LOGGER)
        self.engine = runtime.deserialize_cuda_engine(engine_bytes)
        if self.engine is None:
            raise RuntimeError("Failed to load TensorRT engine")

        self.context = self.engine.create_execution_context()

        self.inputs = []
        self.outputs = []
        self.bindings = []

        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            shape = self.engine.get_tensor_shape(name)

            tensor_size = np.prod(shape) * np.dtype(np.float32).itemsize
            tensor = cuda.mem_alloc(tensor_size)
            self.bindings.append(int(tensor))

            if self.engine.get_tensor_mode(name) == trt.TensorIOMode.INPUT:
                self.inputs.append({'name': name, 'shape': shape})
                self.input_shape = tuple(shape[1:])
            else:
                self.outputs.append({'name': name, 'shape': shape})

        rospy.loginfo(f"✅ TensorRT 引擎加载: {engine_path}")
        rospy.loginfo(f"   输入形状: {self.input_shape}")

    def infer(self, image: np.ndarray, conf_thres: float = 0.5, iou_thres: float = 0.45) -> Dict:
        start_time = time.time()
        input_data = self._preprocess(image)

        self.cuda.memcpy_htod_async(self.bindings[0], input_data, self.stream)
        self.context.execute_async_v3(stream_handle=self.stream.handle)

        output_shape = self.outputs[0]['shape'] if self.outputs else (1, 84, 8400)
        output_data = np.zeros(output_shape, dtype=np.float32)
        self.cuda.memcpy_dtoh_async(output_data, self.bindings[1], self.stream)
        self.stream.synchronize()

        inference_time = time.time() - start_time
        detections = self._postprocess(output_data, conf_thres, iou_thres)

        return {
            'success': True,
            'detections': detections,
            'inference_time': inference_time
        }

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        resized = cv2.resize(image, (self.input_shape[3], self.input_shape[2]))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        normalized = rgb.astype(np.float32) / 255.0
        transposed = np.transpose(normalized, (2, 0, 1))
        batched = np.expand_dims(transposed, axis=0)
        return np.ascontiguousarray(batched)

    def _postprocess(self, output: np.ndarray, conf_thres: float, iou_thres: float) -> List[Dict]:
        detections = []

        if output.ndim == 3:
            output = output.reshape(output.shape[0], -1)

        predictions = output.T if output.shape[0] > output.shape[1] else output

        for pred in predictions:
            if len(pred) < 5:
                continue

            obj_conf = float(pred[4])
            if obj_conf < conf_thres:
                continue

            class_id = int(np.argmax(pred[5:])) if len(pred) > 5 else 0
            class_conf = float(pred[5 + class_id]) if len(pred) > 5 else obj_conf
            total_conf = class_conf * obj_conf

            if total_conf < conf_thres:
                continue

            cx, cy, w, h = pred[0], pred[1], pred[2], pred[3]

            detections.append({
                'class_id': class_id,
                'class_name': f'class_{class_id}',
                'confidence': total_conf,
                'bbox': [float(cx - w/2), float(cy - h/2), float(cx + w/2), float(cy + h/2)],
                'center': [float(cx), float(cy)],
                'area': float(w * h)
            })

        detections.sort(key=lambda x: x['confidence'], reverse=True)
        if detections and iou_thres > 0:
            detections = self._nms(detections, iou_thres)

        return detections

    def _nms(self, detections: List[Dict], iou_thres: float) -> List[Dict]:
        if not detections:
            return []

        boxes = np.array([d['bbox'] for d in detections])
        scores = np.array([d['confidence'] for d in detections])

        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)

        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h

            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)

            indices = np.where(iou <= iou_thres)[0]
            order = order[indices + 1]

        return [detections[i] for i in keep]


class RLONNXInference:
    def __init__(self, model_path: str, input_shape: tuple):
        self.model_path = model_path
        self.input_shape = input_shape

        try:
            import onnxruntime as ort
            self.ort = ort
        except ImportError:
            rospy.logerr("❌ onnxruntime 未安装")
            raise

        self.session = ort.InferenceSession(model_path, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

        rospy.loginfo(f"✅ RL ONNX 模型加载: {model_path}")

    def infer(self, obs: np.ndarray) -> Dict:
        start_time = time.time()

        input_data = np.ascontiguousarray(obs.astype(np.float32))

        try:
            outputs = self.session.run(self.output_names, {self.input_names[0]: input_data})
            inference_time = time.time() - start_time

            return {
                'success': True,
                'action': outputs[0],
                'inference_time': inference_time
            }
        except Exception as e:
            rospy.logerr(f"❌ RL ONNX 推理失败: {e}")
            return {'success': False, 'error': str(e)}


def create_inference(model_path: str, backend: str = 'auto', model_type: str = 'yolo') -> object:
    if backend == 'auto':
        if model_path.endswith('.engine'):
            backend = 'tensorrt'
        else:
            backend = 'onnxruntime'

    if model_type == 'yolo':
        if backend == 'onnxruntime':
            return YOLOONNXInference(model_path, use_gpu=True)
        elif backend == 'tensorrt':
            return YOLOTensorRTInference(model_path)
        else:
            raise ValueError(f"不支持的后端: {backend}")
    elif model_type == 'rl':
        input_shape_str = rospy.get_param('~input_shape', '1,3,64,64')
        input_shape = tuple(map(int, input_shape_str.split(',')))
        return RLONNXInference(model_path, input_shape)
    else:
        raise ValueError(f"不支持的模型类型: {model_type}")


class Sim2RealNode:
    def __init__(self):
        rospy.init_node('sim2real_inference', anonymous=True)

        self.bridge = CvBridge()
        self.inference = None

        self.result_pub = rospy.Publisher(
            '/sim2real/inference_result', Image, queue_size=1)

        default_model = rospy.get_param('~model_path', '')
        default_type = rospy.get_param('~model_type', 'yolo')
        default_backend = rospy.get_param('~backend', 'auto')

        if default_model:
            self.load_model(default_model, default_type, default_backend)

        rospy.loginfo("✅ Sim2Real 推理节点已启动")
        rospy.loginfo("   支持后端: ONNX Runtime GPU, TensorRT")

    def load_model(self, model_path: str, model_type: str = 'yolo', backend: str = 'auto') -> bool:
        try:
            self.inference = create_inference(model_path, backend, model_type)
            rospy.loginfo(f"✅ 模型加载成功: {model_path} ({model_type}, {backend})")
            return True
        except Exception as e:
            rospy.logerr(f"❌ 模型加载失败: {e}")
            return False

    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        image_draw = image.copy()
        colors = self._generate_colors(80)

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

    def run(self):
        rospy.loginfo("🎯 等待推理请求...")
        rospy.spin()


if __name__ == '__main__':
    try:
        node = Sim2RealNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
