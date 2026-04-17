#!/usr/bin/env python3

import os
import sys
import numpy as np
import ctypes
from pathlib import Path


class TensorRTBindings:
    def __init__(self):
        self.lib = None
        self._load_lib()

    def _load_lib(self):
        lib_paths = [
            '/usr/lib/aarch64-linux-gnu/libnvinfer.so',
            '/usr/lib/aarch64-linux-gnu/libnvinfer.so.8',
        ]
        for path in lib_paths:
            if os.path.exists(path):
                self.lib = ctypes.CDLL(path)
                self._setup_functions()
                print(f"Loaded TensorRT from {path}")
                return
        raise RuntimeError("TensorRT library not found")

    def _setup_functions(self):
        self.lib.nvinfer1_createInferRuntime.restype = ctypes.c_void_p
        self.lib.nvinfer1_createInferRuntime.argtypes = [ctypes.c_void_p]

        self.lib.nvinfer1_IRuntime_deserializeCudaEngine.restype = ctypes.c_void_p
        self.lib.nvinfer1_IRuntime_deserializeCudaEngine.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p
        ]

        self.lib.nvinfer1_IExecutionContext_create.restype = ctypes.c_void_p
        self.lib.nvinfer1_IExecutionContext_create.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self.lib.nvinfer1_IExecutionContext_enqueue.restype = ctypes.c_bool
        self.lib.nvinfer1_IExecutionContext_enqueue.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_size_t,
            ctypes.c_void_p
        ]

        self.lib.nvinfer1_IRuntime_destroy.restype = None
        self.lib.nvinfer1_IRuntime_destroy.argtypes = [ctypes.c_void_p]

        self.lib.nvinfer1_IExecutionContext_destroy.restype = None
        self.lib.nvinfer1_IExecutionContext_destroy.argtypes = [ctypes.c_void_p]

        self.lib.nvinfer1_IEngineGen_from_file.restype = ctypes.c_void_p
        self.lib.nvinfer1_IEngineGen_from_file.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        self.lib.nvinfer1_IBuilder_buildSerializedNetwork.restype = ctypes.c_void_p
        self.lib.nvinfer1_IBuilder_buildSerializedNetwork.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        ]


class TensorRTInference:
    def __init__(self, engine_path: str):
        self.engine_path = engine_path
        self.bindings = TensorRTBindings()
        self.runtime = None
        self.engine = None
        self.context = None
        self.inputs = []
        self.outputs = []
        self.bindings_list = []

        self._load_engine()
        self._setup_io()

    def _load_engine(self):
        logger = ctypes.c_void_p(0)
        self.runtime = self.bindings.lib.nvinfer1_createInferRuntime(logger)

        with open(self.engine_path, 'rb') as f:
            engine_bytes = f.read()

        self.engine = self.bindings.lib.nvinfer1_IRuntime_deserializeCudaEngine(
            self.runtime, engine_bytes, len(engine_bytes), None
        )

        if not self.engine:
            raise RuntimeError("Failed to deserialize engine")

        self.context = self.bindings.lib.nvinfer1_IExecutionContext_create(self.engine, None)
        print(f"TensorRT engine loaded: {self.engine_path}")

    def _setup_io(self):
        pass

    def infer(self, obs: np.ndarray) -> np.ndarray:
        raise NotImplementedError("RL model inference requires custom I/O setup")


def build_tensorrt_engine(onnx_path: str, engine_path: str, fp16: bool = True, workspace: int = 4):
    print("Building TensorRT engine...")
    print(f"  ONNX: {onnx_path}")
    print(f"  Engine: {engine_path}")
    print(f"  FP16: {fp16}")
    print(f"  Workspace: {workspace} GB")

    try:
        import tensorrt as trt
    except ImportError:
        print("TensorRT Python bindings not available for Python 3.8")
        print("Using ctypes approach...")

    print("Note: TensorRT Python bindings require Python 3.6")
    print("Please use one of the following alternatives:")
    print("  1. Use onnx2trt command line tool (if available)")
    print("  2. Use trtexec: /usr/src/tensorrt/bin/trtexec")
    print("  3. Build engine on x86_64 PC and copy to Jetson Nano")
    return False


def onnx_to_tensorrt_command(onnx_path: str, engine_path: str, fp16: bool = True):
    trtexec_path = "/usr/src/tensorrt/bin/trtexec"

    if not os.path.exists(trtexec_path):
        print(f"trtexec not found at {trtexec_path}")
        return False

    cmd = [
        trtexec_path,
        f"--onnx={onnx_path}",
        f"--saveEngine={engine_path}",
        f"--workspace={4 << 20}",
    ]

    if fp16:
        cmd.append("--fp16")

    print(f"Running: {' '.join(cmd)}")
    os.system(" ".join(cmd))
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RL Model TensorRT Inference")
    parser.add_argument("--model", type=str, required=True, help="Model path (.onnx or .engine)")
    parser.add_argument("--mode", type=str, default="infer", choices=["infer", "build"])
    parser.add_argument("--input_shape", type=str, default="1,174", help="Input shape")
    parser.add_argument("--output_shape", type=str, default="1,6", help="Output shape")

    args = parser.parse_args()

    if args.mode == "build":
        if args.model.endswith(".onnx"):
            engine_path = args.model.replace(".onnx", ".engine")
            onnx_to_tensorrt_command(args.model, engine_path)
        else:
            print("For build mode, provide .onnx file path")
    else:
        print("RL Model TensorRT Inference")
        print(f"Model: {args.model}")
        print(f"Input shape: {args.input_shape}")
        print(f"Output shape: {args.output_shape}")
        print("")
        print("Note: TensorRT Python bindings require Python 3.6 on this Jetson Nano")
        print("For RL model inference, please use:")
        print("  1. PyTorch inference (if model is .pt)")
        print("  2. ONNX Runtime: python3 -c 'import onnxruntime as ort; ...'")
        print("  3. Or use trtexec to build engine first")
