# AGENTS.md

Guidelines for agentic coding assistants working on this Jetson Nano B01 (4GB RAM, aarch64) robotics project.

## Project Structure

```
Jetson_Nano/
├── action_ws/          # ROS 1 workspace (CAN, I2C, SPI, GPIO, Serial)
├── ROS_Project/        # ROS 1 workspace (main project)
├── ThreadPoolProject/  # C++ CMake project (C++20, pthread)
├── data/               # Data storage
├── tests/              # Test files
├── scripts/            # Utility scripts
└── yolo11n.pt          # YOLOv11 model
```

## Build, Lint, and Test Commands

### C++ Projects (ThreadPoolProject)

```bash
# Build
cd ThreadPoolProject && make all

# Clean
cd ThreadPoolProject && make clean

# Run interactive test
cd ThreadPoolProject && make run

# Run automated tests (non-interactive)
cd ThreadPoolProject && make test

# Run specific test number (e.g., test 7)
echo "7" | ./build/multithread_test

# CMake build
cd ThreadPoolProject && mkdir -p build && cd build && cmake .. && make
```

### ROS Projects

```bash
# Build workspace
cd action_ws && catkin_make

# Source workspace
source action_ws/devel/setup.bash

# Run node
rosrun <package> <node>

# Run launch file
roslaunch <package> <launch_file>.launch

# Test: Start roscore in terminal 1, then run node in terminal 2
```

### Python/ML Projects

```bash
# Install dependencies
pip3 install --user -r requirements.txt

# Test PyTorch GPU
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Run YOLOv11 inference (lightweight for Jetson Nano 4GB)
python3 -c "from ultralytics import YOLO; YOLO('yolo11n.pt')('image.jpg')"
```

## Code Style Guidelines

### Python (ROS and ML)

**Imports (order matters):**
1. ROS: `import rospy`, `import actionlib`
2. Standard: `import sys`, `import os`, `import time`
3. Third-party: `import numpy`, `import cv2`
4. Local: absolute imports for project modules

**Formatting:**
- 4-space indentation, PEP 8 style
- Line length: 88 chars (Black default) or 100 for ROS
- f-strings: `f"Value: {value}"`
- Shebang: `#!/usr/bin/env python3`
- Encoding: `# -*- coding: utf-8 -*-`

**Types:**
- Type hints for Python 3.8+: `from typing import List, Dict, Optional, Tuple`
- ROS message types exempt

**Naming:**
- Classes: `PascalCase` (e.g., `FibonacciServer`)
- Functions/variables: `snake_case` (e.g., `send_can_frame`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private: `_leading_underscore`

**Error Handling:**
```python
try:
    # code
except rospy.ROSInterruptException:
    pass
rospy.logerr("Error message")
rospy.logwarn("Warning")
rospy.loginfo("Info")
```

**ROS-Specific:**
- Init in `if __name__ == '__main__'` block
- Parameters: `rospy.get_param('~param', default)`
- Use `rospy.spin()` to keep alive

### C++ Projects

**Formatting:**
- 4-space indentation, braces for all control structures
- Line length: 100 chars

**Naming:**
- Classes: `PascalCase`
- Functions: `camelCase`
- Member variables: `snake_case`
- Local variables: `camelCase`
- Constants: `kCamelCase` or `UPPER_SNAKE_CASE`
- Files: `snake_case.cc`, `snake_case.h`

**Includes (order):**
1. C stdlib: `#include <stdio.h>`
2. C++ stdlib: `#include <vector>`
3. Project: `#include "my_header.h"`

**Comments:**
- Single-line: `//`
- Multi-line: `/* */`

## AI/ML Code

**Model Usage:**
- Use `yolo11n.pt` (lightweight)
- Specify device: `model(..., device='cuda:0')`
- Lower image size: `imgsz=416`, `batch=1`

**Performance:**
- Enable MAXN: `sudo nvpmodel -m 0 && sudo jetson_clocks`
- Monitor: `sudo jtop`, `free -h`, `tegrastats`

## Common Patterns

### ROS Action Server
```python
class MyActionServer:
    def __init__(self):
        self.server = actionlib.SimpleActionServer(
            'action_name', ActionMsg, self.execute, False)
        self.server.start()

    def execute(self, goal):
        if self.server.is_preempt_requested():
            self.server.set_preempted()
            return
        self.server.publish_feedback(feedback)
        self.server.set_succeeded(result)
```

### ROS Action Client
```python
class MyActionClient:
    def __init__(self):
        self.client = actionlib.SimpleActionServer('action_name', ActionMsg)
        self.client.wait_for_server()

    def send_goal(self):
        goal = ActionMsg()
        self.client.send_goal(goal)
        self.client.wait_for_result()
        return self.client.get_result()
```

## Language

- Comments/docstrings: Chinese acceptable
- Variable/function names: English
- User-facing messages: Chinese
- Log messages: Chinese with emoji (✅, ❌, 📤, 📛)
