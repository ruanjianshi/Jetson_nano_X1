# AGENTS.md

This file contains guidelines and commands for agentic coding assistants working on this Jetson Nano project.

## Project Overview

This is a Jetson Nano B01 (4GB RAM, aarch64) robotics project with multiple components:
- **ROS workspaces**: `action_ws/` (ROS 1), `ROS_Project/` (ROS 1)
- **C++ projects**: `ThreadPoolProject/` (CMake-based)
- **AI/ML**: YOLOv11 with PyTorch 1.13.0 and CUDA 10.2 support
- **Hardware integration**: CAN, I2C, SPI, GPIO, Serial communication

## Build, Lint, and Test Commands

### C++ Projects (ThreadPoolProject)

```bash
# Build
cd ThreadPoolProject && make all

# Clean
cd ThreadPoolProject && make clean

# Run interactive test
cd ThreadPoolProject && make run

# Run automated tests
cd ThreadPoolProject && make test

# Help
cd ThreadPoolProject && make help
```

### ROS Projects

```bash
# Build ROS workspace (from workspace root)
cd action_ws && catkin_make

# Source the workspace
source action_ws/devel/setup.bash

# Run ROS node (example)
rosrun my_action_pkg fibonacci_server

# Run ROS launch file (if available)
roslaunch my_action_pkg my_launch_file.launch

# Test individual ROS node
# Start in one terminal: roscore
# Start in another: rosrun <package> <node>
```

### Python/ML Projects

```bash
# Install Python dependencies
pip3 install --user -r requirements.txt  # if exists

# Run YOLOv11 inference
python3 -c "from ultralytics import YOLO; YOLO('yolo11n.pt')('image.jpg')"

# Test PyTorch GPU availability
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

## Code Style Guidelines

### Python (ROS and ML)

**Imports:**
- ROS imports first: `import rospy`, `import actionlib`
- Standard library next: `import sys`, `import os`, `import time`
- Third-party next: `import numpy`, `import cv2`
- Local imports last
- Use absolute imports for project modules

**Formatting:**
- Use PEP 8 style (4-space indentation)
- Line length: 88 characters (Black default) or 100 characters for ROS
- Use f-strings for string formatting: `f"Value: {value}"`
- Add shebang: `#!/usr/bin/env python3`
- Add encoding declaration: `# -*- coding: utf-8 -*-`

**Types:**
- Add type hints for new code (Python 3.8+ compatible)
- Use typing module: `from typing import List, Dict, Optional, Tuple`
- ROS message types don't need type hints

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `FibonacciServer`, `CANCommClient`)
- Functions: `snake_case` (e.g., `execute`, `send_can_frame`)
- Variables: `snake_case` (e.g., `can_id`, `fib_seq`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private members: `_leading_underscore` (e.g., `_delay`)

**Error Handling:**
- Use try/except for ROS interrupts: `except rospy.ROSInterruptException`
- Log errors with rospy: `rospy.logerr("Error message")`
- Log warnings: `rospy.logwarn("Warning message")`
- Log info: `rospy.loginfo("Info message")`
- Return meaningful error codes/exceptions

**Docstrings:**
- Use Google-style docstrings for classes and functions
- Include parameters, returns, and examples

**ROS-Specific:**
- Initialize node in `if __name__ == '__main__'` block
- Use `rospy.get_param('~param', default_value)` for parameters
- Always use private namespace `~` for node parameters
- Call `rospy.spin()` to keep node alive

### C++ Projects

**Formatting:**
- Use 4-space indentation
- Use braces for all control structures
- Line length: 100 characters

**Naming:**
- Classes: `PascalCase`
- Functions: `camelCase`
- Variables: `snake_case` for member, `camelCase` for local
- Constants: `kCamelCase` or `UPPER_SNAKE_CASE`
- Files: `snake_case.cc`, `snake_case.h`

**Includes:**
- C standard library first: `#include <stdio.h>`
- C++ standard library next: `#include <vector>`
- Project headers last: `#include "my_header.h"`

**Comments:**
- Use `//` for single-line comments
- Use `/* */` for multi-line comments
- Add file headers with author and date

### AI/ML Code

**Model Usage:**
- Use `yolo11n.pt` for Jetson Nano 4GB (lightweight)
- Specify device explicitly: `model(..., device='cuda:0')`
- Lower image size for speed: `imgsz=416`
- Use batch=1 to avoid OOM

**Performance:**
- Enable MAXN mode before inference: `sudo jetson_clocks`
- Monitor with `sudo jtop`
- Export to ONNX for production if needed

## Project Structure

```
Jetson_Nano/
├── action_ws/          # ROS 1 workspace (CAN, I2C, SPI, GPIO, Serial)
│   ├── src/            # Source packages
│   ├── devel/          # Development space (generated)
│   └── build/          # Build space (generated)
├── ROS_Project/        # ROS 1 workspace (main project)
├── ThreadPoolProject/  # C++ CMake project
├── data/               # Data storage
├── tests/              # Test files
├── scripts/            # Utility scripts
├── README/             # Documentation
└── yolo11n.pt          # YOLOv11 model
```

## Testing

### Running a Single Test

**C++ Projects:**
```bash
cd ThreadPoolProject && make test
```

**ROS Nodes:**
```bash
# Start roscore in terminal 1
roscore

# Run specific node in terminal 2
rosrun my_action_pkg fibonacci_server

# Run client in terminal 3
rosrun my_action_pkg fibonacci_client
```

**Python Scripts:**
```bash
python3 /path/to/script.py
```

## Common Patterns

### ROS Action Server Pattern
```python
class MyActionServer:
    def __init__(self):
        self.server = actionlib.SimpleActionServer(
            'action_name', ActionMsg, self.execute, False)
        self.server.start()

    def execute(self, goal):
        # Process goal
        if self.server.is_preempt_requested():
            self.server.set_preempted()
            return
        self.server.publish_feedback(feedback)
        self.server.set_succeeded(result)
```

### ROS Action Client Pattern
```python
class MyActionClient:
    def __init__(self):
        self.client = actionlib.SimpleActionClient('action_name', ActionMsg)
        self.client.wait_for_server()

    def send_goal(self):
        goal = ActionMsg()
        self.client.send_goal(goal)
        self.client.wait_for_result()
        return self.client.get_result()
```

## Performance Considerations

- Jetson Nano has 4GB RAM - use lightweight models
- GPU: NVIDIA Tegra X1 (Maxwell, 128 CUDA cores)
- For YOLOv11: use `yolo11n.pt`, `imgsz=416`, `batch=1`
- Enable MAXN mode: `sudo nvpmodel -m 0 && sudo jetson_clocks`
- Monitor memory with `free -h`
- Monitor GPU with `tegrastats`

## Language

- Code comments and docstrings: Chinese is acceptable
- Variable/function names: English
- User-facing messages: Chinese (for this project)
- Log messages: Chinese with emoji indicators (✅, ❌, 📤, 📛)