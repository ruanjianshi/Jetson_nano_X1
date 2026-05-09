# 开发指南

## 开发环境设置

### 系统要求
- Jetson Nano B01
- Ubuntu 18.04/20.04
- ROS Noetic
- Python 3.6+
- CMake 3.0+

### 1. 安装ROS Noetic
```bash
sudo apt update
sudo apt install ros-noetic-desktop-full
source /opt/ros/noetic/setup.bash
```

### 2. 安装Python依赖
```bash
pip3 install opencv-python PyQt5 numpy pyyaml Jetson.GPIO
```

### 3. 安装C++依赖
```bash
sudo apt install libboost-all-dev
```

### 4. 设置项目环境
```bash
cd /home/jetson/Desktop/Jetson_Nano/ROS_Project
source env/setup_env.sh
catkin_make
source devel/setup.bash
```

## 项目开发规范

### 目录结构规范

#### ROS包开发
每个ROS包必须包含以下标准结构：
```
<package_name>/
├── include/<package_name>/    # C++头文件
├── src/                       # C++源文件
├── scripts/                   # Python ROS节点
├── srv/                       # ROS服务定义
├── launch/                    # 包特定launch文件
├── config/                    # 包特定配置文件
├── CMakeLists.txt             # 构建配置
└── package.xml                # 包元数据
```

#### 脚本命名规范
- **ROS节点**: `<功能>_node.py`
- **工具库**: `<功能>_utils.py`
- **示例**: `<功能>_example.py`
- **测试**: `test_<功能>.py`
- **Shell脚本**: `<功能>.sh`

### 代码规范

#### Python代码规范
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模块说明
"""

import rospy
import sys

class ClassName:
    """类说明"""
    
    def __init__(self):
        """初始化"""
        rospy.init_node('node_name')
        
    def method_name(self, param):
        """
        方法说明
        
        Args:
            param: 参数说明
            
        Returns:
            返回值说明
        """
        pass

def main():
    """主函数"""
    try:
        node = ClassName()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        rospy.loginfo('Node shutdown')

if __name__ == '__main__':
    main()
```

#### C++代码规范
```cpp
#ifndef PACKAGE_NAME_CLASS_NAME_H
#define PACKAGE_NAME_CLASS_NAME_H

#include <ros/ros.h>
#include <std_msgs/String.h>

namespace package_name {

class ClassName {
public:
    ClassName();
    ~ClassName();
    
    void init();
    void run();
    
private:
    ros::NodeHandle nh_;
    ros::Publisher pub_;
    
    void callback(const std_msgs::String::ConstPtr& msg);
};

} // namespace package_name

#endif // PACKAGE_NAME_CLASS_NAME_H
```

### ROS开发规范

#### 话题命名规范
- 使用小写字母和下划线
- 遵循`/<module>/<function>`格式
- 示例: `/gpio/write`, `/camera/image_raw`

#### 服务命名规范
- 使用小写字母和下划线
- 遵循`/<module>/<action>`格式
- 示例: `/gpio_control`, `/serial_connect`

#### 参数命名规范
- 使用小写字母和下划线
- 使用描述性名称
- 示例: `gpio_pins`, `pin_direction`

## 开发流程

### 1. 创建新ROS包
```bash
cd src
catkin_create_pkg <package_name> rospy std_msgs
cd <package_name>
```

### 2. 开发功能
- 在`scripts/`中创建Python ROS节点
- 在`src/`中创建C++源文件
- 在`include/`中创建C++头文件
- 在`srv/`中定义ROS服务

### 3. 配置构建
编辑`CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.0.2)
project(<package_name>)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
)

catkin_package()

# Python脚本
catkin_install_python(PROGRAMS
  scripts/<script_name>.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# C++可执行文件
add_executable(<node_name> src/<source_file>.cpp)
target_link_libraries(<node_name> ${catkin_LIBRARIES})
```

编辑`package.xml`:
```xml
<package>
  <name><package_name></name>
  <version>1.0.0</version>
  <description>Package description</description>
  <maintainer email="user@jetsonnano">Developer</maintainer>
  <license>MIT</license>
  
  <buildtool_depend>catkin</buildtool_depend>
  <build_depend>rospy</build_depend>
  <build_depend>std_msgs</build_depend>
  <build_export_depend>rospy</build_export_depend>
  <exec_depend>rospy</exec_depend>
  <exec_depend>std_msgs</exec_depend>
</package>
```

### 4. 构建和测试
```bash
cd /home/jetson/Desktop/Jetson_Nano/ROS_Project
catkin_make
source devel/setup.bash
rosrun <package_name> <script_name>.py
```

### 5. 更新文档
- 更新`docs/`中的相关文档
- 更新`logs/daily/`中的开发日志
- 更新`logs/progress/`中的进度记录

## 测试规范

### 单元测试
在`tests/unit/`中创建单元测试：
```python
#!/usr/bin/env python3
import unittest
import sys
sys.path.append('../../src/<package_name>/scripts')

class TestClassName(unittest.TestCase):
    def test_method(self):
        """测试方法"""
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
```

### 集成测试
在`tests/integration/`中创建集成测试：
```python
#!/usr/bin/env python3
import rospy
import unittest

class TestIntegration(unittest.TestCase):
    def test_topic_communication(self):
        """测试话题通信"""
        pass

if __name__ == '__main__':
    rospy.init_node('test_node')
    unittest.main()
```

### 运行测试
```bash
# 运行所有测试
./scripts/test.sh

# 运行单元测试
python3 tests/unit/test_<module>.py

# 运行集成测试
python3 tests/integration/test_<module>.py
```

## 文档规范

### 代码注释
- 为每个函数/类添加docstring
- 注释复杂的逻辑
- 说明参数和返回值

### 开发日志
在`logs/daily/`中记录每日开发：
```markdown
# 2025-03-27 开发日志

## 完成任务
- [x] 任务1
- [x] 任务2

## 进行中任务
- [ ] 任务3

## 遇到问题
- 问题描述1
- 解决方案1

## 下一步计划
- 计划1
- 计划2
```

### 进度跟踪
在`logs/progress/`中更新进度：
```markdown
# 项目进度跟踪

## 整体进度
- 总体: 80%
- GPIO控制: 100%
- 通信模块: 90%
- 图像处理: 70%

## 里程碑
- [x] 里程碑1
- [ ] 里程碑2
```

## 调试技巧

### ROS调试
```bash
# 查看话题列表
rostopic list

# 查看话题信息
rostopic info /topic_name

# 监听话题
rostopic echo /topic_name

# 发布消息
rostopic pub /topic_name std_msgs/String "data: 'hello'"

# 查看服务列表
rosservice list

# 调用服务
rosservice call /service_name "arg: value"

# 查看节点列表
rosnode list

# 查看节点信息
rosnode info /node_name

# 查看参数
rosparam list

# 获取参数
rosparam get /param_name

# 设置参数
rosparam set /param_name value
```

### Python调试
```python
# 使用rospy日志
rospy.loginfo("Info message")
rospy.logwarn("Warning message")
rospy.logerr("Error message")

# 使用try-except捕获异常
try:
    # 代码
except Exception as e:
    rospy.logerr(f"Error: {e}")
```

### C++调试
```cpp
// 使用ROS日志
ROS_INFO("Info message");
ROS_WARN("Warning message");
ROS_ERROR("Error message");

// 使用断言
ROS_ASSERT(condition);
```

## 性能优化

### Python优化
- 使用多线程/多进程
- 使用numpy加速数值计算
- 减少不必要的对象创建
- 使用生成器替代列表

### C++优化
- 使用移动语义
- 使用智能指针
- 避免不必要的拷贝
- 使用编译器优化

### ROS优化
- 合理设置消息队列大小
- 使用专用话题/服务
- 优化发布频率
- 使用参数服务器共享配置

## 常见问题

### 编译错误
1. 检查CMakeLists.txt配置
2. 检查依赖是否正确安装
3. 检查Python脚本权限

### 运行时错误
1. 检查ROS环境是否激活
2. 检查节点是否正确启动
3. 查看错误日志

### 通信问题
1. 检查话题/服务名称是否正确
2. 检查消息类型是否匹配
3. 检查网络连接

## 最佳实践

### 开发流程
1. 先编写测试
2. 使用版本控制
3. 定期提交代码
4. 代码审查
5. 持续集成

### 代码质量
1. 遵循PEP 8规范
2. 添加适当的注释
3. 编写单元测试
4. 使用静态分析工具

### 团队协作
1. 清晰的代码结构
2. 详细的文档
3. 有效的沟通
4. 定期的会议

## 扩展阅读

- [ROS官方教程](http://wiki.ros.org/ROS/Tutorials)
- [Python PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [C++编码规范](https://google.github.io/styleguide/cppguide.html)
- [Jetson Nano文档](https://developer.nvidia.com/embedded/jetson-nano)