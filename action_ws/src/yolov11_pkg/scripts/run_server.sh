#!/bin/bash

# 解决 OpenMP 库冲突的启动脚本

export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

SCRIPT_PATH="/home/jetson/Desktop/Jetson_Nano/action_ws/src/yolov11_pkg/scripts/yolov11_inference_server.py"

python3 "$SCRIPT_PATH" "$@"