#!/usr/bin/env python3

import os
import sys
import rospy
import numpy as np
import time
from typing import List, Dict, Optional, Tuple
import onnxruntime as ort


class RLONNXInference:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.model_path = model_path
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])

        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]

        self.input_shape = self.session.get_inputs()[0].shape
        self.output_shape = self.session.get_outputs()[0].shape

        rospy.loginfo(f"✅ RL ONNX 模型加载: {model_path}")
        rospy.loginfo(f"   输入: {self.input_names} {self.input_shape}")
        rospy.loginfo(f"   输出: {self.output_names} {self.output_shape}")

    def infer(self, obs: np.ndarray) -> Dict:
        start_time = time.time()

        if obs.ndim == 1:
            obs = obs.reshape(1, -1)

        if obs.shape[1] != self.input_shape[1]:
            rospy.logerr(f"输入维度不匹配: {obs.shape[1]} vs {self.input_shape[1]}")
            return {'success': False, 'error': 'Input dimension mismatch'}

        try:
            outputs = self.session.run(self.output_names, {self.input_names[0]: obs.astype(np.float32)})
            inference_time = time.time() - start_time

            return {
                'success': True,
                'action': outputs[0],
                'inference_time': inference_time
            }
        except Exception as e:
            rospy.logerr(f"❌ 推理失败: {e}")
            return {'success': False, 'error': str(e)}


class JumpModelNode:
    def __init__(self):
        rospy.init_node('jump_model_inference', anonymous=True)

        default_model = rospy.get_param('~model_path',
            '/home/jetson/Desktop/Jetson_Nano/action_ws/src/sim2real_pkg/models/jump_model.onnx')
        default_rate = rospy.get_param('~inference_rate', 50.0)

        self.inference = None
        self.last_inference_time = 0
        self.inference_rate = rospy.Rate(default_rate)

        if os.path.exists(default_model):
            try:
                self.inference = RLONNXInference(default_model)
                rospy.loginfo(f"✅ 模型加载成功")
            except Exception as e:
                rospy.logerr(f"❌ 模型加载失败: {e}")
        else:
            rospy.logwarn(f"⚠️ 模型文件不存在: {default_model}")
            rospy.loginfo("请上传 .onnx 模型文件到 models/ 目录")

        rospy.loginfo("✅ Jump Model 推理节点已启动")
        rospy.loginfo(f"   模型: {default_model}")
        rospy.loginfo(f"   推理频率: {default_rate} Hz")

    def run(self):
        rospy.loginfo("🎯 等待推理请求...")

        while not rospy.is_shutdown():
            if self.inference is None:
                rospy.sleep(1.0)
                continue

            self.inference_rate.sleep()

        rospy.loginfo("📛 节点已关闭")


def main():
    node = JumpModelNode()
    node.run()


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        rospy.loginfo("📛 节点被中断")
    except KeyboardInterrupt:
        rospy.loginfo("📛 用户中断")
