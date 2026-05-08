#!/bin/bash
source /home/xq/miniconda3/etc/profile.d/conda.sh
conda activate yolo
exec /home/xq/miniconda3/envs/yolo/bin/python3 -u "$@"
