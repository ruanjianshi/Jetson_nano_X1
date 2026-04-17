#!/usr/bin/env python3

import os
import sys
import argparse
import rospy
from pathlib import Path


class PT2ONNXConverter:
    def __init__(self):
        self.workspace = Path(__file__).parent.parent.parent
        self.models_dir = self.workspace / 'models'
        self.models_dir.mkdir(exist_ok=True)

    def convert_yolo_to_onnx(self, pt_path: str, output_path: str = None,
                             imgsz: int = 640, simplify: bool = True) -> bool:
        try:
            from ultralytics import YOLO
        except ImportError as e:
            rospy.logerr(f"❌ 缺少依赖: {e}")
            rospy.loginfo("请运行: pip3 install ultralytics")
            return False

        rospy.loginfo(f"📥 加载 YOLO 模型: {pt_path}")
        model = YOLO(pt_path)

        if output_path is None:
            output_path = str(self.models_dir / Path(pt_path).with_suffix('.onnx').name)

        rospy.loginfo(f"🔄 正在导出 ONNX 模型...")
        rospy.loginfo(f"   输入尺寸: {imgsz}x{imgsz}")
        rospy.loginfo(f"   简化模型: {simplify}")

        try:
            success = model.export(format='onnx', imgsz=imgsz, simplify=simplify)
            rospy.loginfo(f"✅ YOLO ONNX 模型已导出: {success}")
            return True
        except Exception as e:
            rospy.logerr(f"❌ YOLO ONNX 导出失败: {e}")
            return False

    def convert_rl_model_to_onnx(self, pt_path: str, output_path: str = None,
                                 input_shape: tuple = None) -> bool:
        try:
            import torch
        except ImportError as e:
            rospy.logerr(f"❌ 缺少 PyTorch: {e}")
            return False

        rospy.loginfo(f"📥 加载强化学习模型: {pt_path}")

        try:
            model = torch.load(pt_path, map_location='cpu')
        except Exception as e:
            rospy.logerr(f"❌ 模型加载失败: {e}")
            return False

        if output_path is None:
            output_path = str(self.models_dir / Path(pt_path).with_suffix('.onnx').name)

        rospy.loginfo(f"🔄 正在导出 RL ONNX 模型...")
        rospy.loginfo(f"   输出路径: {output_path}")

        try:
            if isinstance(model, dict) and 'model' in model:
                model = model['model']

            if hasattr(model, 'export'):
                model.export(format='onnx', imgsz=input_shape)
            else:
                dummy_input = torch.randn(1, *input_shape) if input_shape else torch.randn(1, 3, 640, 640)
                torch.onnx.export(model, dummy_input, output_path,
                                verbose=False, opset_version=11)

            rospy.loginfo(f"✅ RL ONNX 模型已导出: {output_path}")
            return True
        except Exception as e:
            rospy.logerr(f"❌ RL ONNX 导出失败: {e}")
            return False

    def convert_pt_to_onnx(self, pt_path: str, output_path: str = None,
                          model_type: str = 'yolo', imgsz: int = 640,
                          simplify: bool = True, input_shape: tuple = None) -> bool:
        if model_type == 'yolo':
            return self.convert_yolo_to_onnx(pt_path, output_path, imgsz, simplify)
        elif model_type == 'rl':
            return self.convert_rl_model_to_onnx(pt_path, output_path, input_shape)
        else:
            rospy.logerr(f"❌ 不支持的模型类型: {model_type}")
            return False


class ONNX2TensorRTConverter:
    def __init__(self):
        self.workspace = Path(__file__).parent.parent.parent
        self.models_dir = self.workspace / 'models'
        self.models_dir.mkdir(exist_ok=True)

    def convert(self, onnx_path: str, output_path: str = None,
                fp16: bool = True, workspace: int = 4) -> bool:
        try:
            import tensorrt as trt
        except ImportError as e:
            rospy.logerr(f"❌ TensorRT 未安装: {e}")
            return False

        if output_path is None:
            output_path = str(self.models_dir / Path(onnx_path).with_suffix('.engine').name)

        rospy.loginfo(f"🔄 正在构建 TensorRT 引擎...")
        rospy.loginfo(f"   ONNX 模型: {onnx_path}")
        rospy.loginfo(f"   FP16: {fp16}")
        rospy.loginfo(f"   工作空间: {workspace} GB")

        logger = trt.Logger(trt.Logger.WARNING)
        builder = trt.Builder(logger)
        network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
        config = builder.create_builder_config()
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace << 30)

        if fp16 and builder.platform_has_fast_fp16:
            config.set_flag(trt.BuilderFlag.FP16)
            rospy.loginfo("   ✅ FP16 已启用")

        parser = trt.OnnxParser(network, logger)
        with open(onnx_path, 'rb') as f:
            if not parser.parse(f.read()):
                for error in range(parser.num_error_codes):
                    rospy.logerr(f"❌ ONNX 解析错误: {parser.get_error(error)}")
                return False

        rospy.loginfo("   🔨 正在序列化引擎...")
        engine_bytes = builder.build_serialized_network(network, config)
        if engine_bytes is None:
            rospy.logerr("❌ TensorRT 引擎构建失败")
            return False

        with open(output_path, 'wb') as f:
            f.write(engine_bytes)

        rospy.loginfo(f"✅ TensorRT 引擎已构建: {output_path}")
        return True


def main():
    rospy.init_node('model_converter', anonymous=True)

    parser = argparse.ArgumentParser(description='模型转换工具 (PT->ONNX, ONNX->TensorRT)')
    parser.add_argument('--mode', type=str, default='pt2onnx',
                        choices=['pt2onnx', 'onnx2trt'],
                        help='转换模式')
    parser.add_argument('--pt', type=str, help='PyTorch 模型路径 (.pt)')
    parser.add_argument('--onnx', type=str, help='ONNX 模型路径')
    parser.add_argument('--engine', type=str, help='TensorRT 引擎输出路径')
    parser.add_argument('--type', type=str, default='yolo',
                        choices=['yolo', 'rl'],
                        help='模型类型: yolo (目标检测) 或 rl (强化学习)')
    parser.add_argument('--imgsz', type=int, default=640, help='输入图像尺寸 (YOLO)')
    parser.add_argument('--input_shape', type=str, help='RL模型输入形状, 如: 3,64,64')
    parser.add_argument('--fp16', action='store_true', default=True, help='启用 FP16')
    parser.add_argument('--workspace', type=int, default=4, help='TensorRT 工作空间 (GB)')

    args = parser.parse_args()

    if args.mode == 'pt2onnx' and args.pt:
        converter = PT2ONNXConverter()
        input_shape = None
        if args.input_shape:
            input_shape = tuple(map(int, args.input_shape.split(',')))

        rospy.loginfo(f"🚀 PT -> ONNX 转换: {args.pt}")
        rospy.loginfo(f"   模型类型: {args.type}")

        success = converter.convert_pt_to_onnx(
            args.pt, args.onnx, args.type, args.imgsz, True, input_shape
        )

        if success:
            rospy.loginfo("✅ 转换完成!")
        else:
            rospy.logerr("❌ 转换失败")

    elif args.mode == 'onnx2trt' and args.onnx:
        converter = ONNX2TensorRTConverter()

        rospy.loginfo(f"🚀 ONNX -> TensorRT 转换: {args.onnx}")

        success = converter.convert(args.onnx, args.engine, fp16=args.fp16, workspace=args.workspace)

        if success:
            rospy.loginfo("✅ 引擎构建完成!")
        else:
            rospy.logerr("❌ 引擎构建失败")

    else:
        rospy.logerr("❌ 参数不足，请查看 --help")


if __name__ == '__main__':
    main()
