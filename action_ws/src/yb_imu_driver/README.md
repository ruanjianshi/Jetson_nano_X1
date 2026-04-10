# YbImu Driver ROS功能包

基于YbImuLib库的高精度九轴IMU驱动ROS功能包，支持I2C和串口通信方式，采用Action通信架构，同时支持实时Topic数据发布。

## 功能特性

- ✅ 支持九轴IMU（加速度计、陀螺仪、磁力计）
- ✅ 支持I2C和串口两种通信方式
- ✅ 基于ROS Action通信架构
- ✅ **实时Topic数据发布**（独立后台线程）
- ✅ 支持单次/连续读取传感器数据
- ✅ 支持IMU校准（陀螺仪、加速度计、磁力计、温度）
- ✅ 支持设置融合算法（六轴/九轴）
- ✅ 支持实时反馈机制
- ✅ 输出完整的传感器数据（四元数、欧拉角、气压计）

## 架构说明

### 混合通信架构

本功能包采用**Action + Topic混合通信架构**：

1. **Action Server**：接收客户端请求（读取、校准、配置等操作）
2. **实时Topic发布**：后台独立线程持续发布IMU数据

两者独立运行，互不干扰！

### Action通信架构

两个独立的Action服务器：

- **imu_i2c**: I2C通信Action服务器
- **imu_serial**: 串口通信Action服务器

支持的操作：

| 操作类型 | 值 | 说明 |
|---------|---|------|
| 单次读取 | 0 | 读取一次所有传感器数据 |
| 连续读取 | 1 | 持续读取传感器数据，带实时反馈 |
| IMU校准 | 2 | 校准陀螺仪和加速度计 |
| 磁力计校准 | 3 | 校准磁力计 |
| 温度校准 | 4 | 校准温度传感器 |
| 设置融合算法 | 5 | 设置六轴或九轴融合算法 |

### 实时Topic发布

Action Server启动时自动创建后台发布线程：

| Topic名称 | 消息类型 | 说明 |
|-----------|----------|------|
| `/imu_serial/data` | `sensor_msgs/Imu` | 加速度、陀螺仪、四元数 |
| `/imu_serial/mag` | `geometry_msgs/Vector3` | 磁力计数据 (uT) |
| `/imu_serial/temperature` | `geometry_msgs/Vector3` | 高度(m)、温度(°C)、气压 |
| `/imu_i2c/data` | `sensor_msgs/Imu` | 加速度、陀螺仪、四元数 |
| `/imu_i2c/mag` | `geometry_msgs/Vector3` | 磁力计数据 (uT) |
| `/imu_i2c/temperature` | `geometry_msgs/Vector3` | 高度(m)、温度(°C)、气压 |

## 依赖项

### ROS依赖
- rospy
- actionlib
- actionlib_msgs
- sensor_msgs
- geometry_msgs
- std_msgs

### Python依赖
- python3-serial
- python3-smbus2
- YbImuLib（需手动安装）

## 安装

### 1. 安装YbImuLib库

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws/YbImuLib
sudo python3 setup.py install
sudo pip3 install pyserial smbus2
```

### 2. 编译ROS功能包

```bash
cd /home/jetson/Desktop/Jetson_Nano/action_ws
catkin_make
source devel/setup.bash
```

## 使用方法

### 1. 启动Action Server

**串口方式：**
```bash
roslaunch yb_imu_driver imu_serial.launch serial_port:=/dev/ttyUSB0 report_rate:=50
```

**I2C方式：**
```bash
roslaunch yb_imu_driver imu_i2c.launch i2c_port:=7
```

启动后，Action Server会：
- ✅ 初始化IMU设备
- ✅ 创建Action Server接收客户端请求
- ✅ 自动启动后台线程实时发布数据

### 2. RViz可视化（推荐）

**启动IMU服务器和RViz可视化：**
```bash
roslaunch yb_imu_driver imu_visualization.launch serial_port:=/dev/ttyUSB0
```

RViz会自动显示：
- 🟢 **绿色方框** - 表示IMU设备姿态
- 🔴🟢🔵 **坐标轴** - 红色X、绿色Y、蓝色Z轴
- 📐 **网格** - 参考坐标系

**自定义启动参数：**
```bash
roslaunch yb_imu_driver imu_visualization.launch \
  serial_port:=/dev/ttyUSB0 \           # 串口设备
  use_rviz:=true \                      # 是否启动RViz
  realtime_publish_rate:=50.0           # 实时发布频率
```

**仅启动服务器（不带RViz）：**
```bash
roslaunch yb_imu_driver imu_visualization.launch use_rviz:=false
```

### 3. 查看实时数据（新终端）

```bash
# 查看完整IMU数据
rostopic echo /imu_serial/data

# 查看磁力计数据
rostopic echo /imu_serial/mag

# 查看温度和气压数据
rostopic echo /imu_serial/temperature

# 查看数据频率
rostopic hz /imu_serial/data
```

### 4. 使用Action Client（另一个终端）

**交互式模式：**
```bash
rosrun yb_imu_driver imu_serial_client.py
```

**命令行模式：**
```bash
# 单次读取
rosrun yb_imu_driver imu_serial_client.py single

# 连续读取5秒
rosrun yb_imu_driver imu_serial_client.py continuous 5

# IMU校准
rosrun yb_imu_driver imu_serial_client.py calibrate

# 磁力计校准
rosrun yb_imu_driver imu_serial_client.py calibrate_mag

# 温度校准
rosrun yb_imu_driver imu_serial_client.py calibrate_temp 25.0

# 设置九轴融合算法
rosrun yb_imu_driver imu_serial_client.py algo9

# 设置六轴融合算法
rosrun yb_imu_driver imu_serial_client.py algo6
```

### 4. 自定义Action Client示例

```python
#!/usr/bin/env python3
import rospy
import actionlib
from yb_imu_driver.msg import IMUI2CAction, IMUI2CGoal

rospy.init_node('my_imu_client')

client = actionlib.SimpleActionClient('imu_i2c', IMUI2CAction)
client.wait_for_server()

goal = IMUI2CGoal()
goal.operation_type = 0  # 单次读取

client.send_goal(goal)
client.wait_for_result()

result = client.get_result()
if result.success:
    print(f"加速度: x={result.accel_x}, y={result.accel_y}, z={result.accel_z}")
    print(f"欧拉角: roll={result.roll}, pitch={result.pitch}, yaw={result.yaw}")
```

## 参数说明

### 通用参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `debug` | bool | false | 是否打印调试信息 |
| `publish_topic` | bool | true | 是否启用实时Topic发布 |
| `realtime_publish_rate` | float | 50.0 | 实时Topic发布频率(Hz) |
| `frame_id` | string | 'imu_link' | IMU坐标系ID |

### I2C专用参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `i2c_port` | int | 7 | I2C总线端口号 |

### 串口专用参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `serial_port` | string | '/dev/ttyUSB0' | 串口设备路径 |
| `report_rate` | int | 50 | IMU采样频率(Hz, 10-100) |

### 参数使用示例

```bash
# 启动串口服务器，禁用实时发布
roslaunch yb_imu_driver imu_serial.launch serial_port:=/dev/ttyUSB0 publish_topic:=false

# 启动I2C服务器，设置实时发布频率为100Hz
roslaunch yb_imu_driver imu_i2c.launch i2c_port:=7 realtime_publish_rate:=100.0
```

## Action消息定义

### Goal
```
uint8 operation_type              # 操作类型 (0-5)
float64 duration                  # 连续读取时长(秒)
uint8 algorithm_type              # 融合算法类型: 6或9
float32 calibration_temperature   # 校准温度值
uint8 calibration_type            # 校准类型: 0=自动, 1=陀螺仪, 2=加速度计
```

### Result
```
# 传感器数据
float32 accel_x, accel_y, accel_z
float32 gyro_x, gyro_y, gyro_z
float32 mag_x, mag_y, mag_z
float32 quat_w, quat_x, quat_y, quat_z
float32 roll, pitch, yaw
float32 height, temperature, pressure, pressure_contrast

# 操作结果
bool success
string message
```

### Feedback
```
# 实时传感器数据
float32 accel_x, accel_y, accel_z
float32 gyro_x, gyro_y, gyro_z
float32 mag_x, mag_y, mag_z
float32 quat_w, quat_x, quat_y, quat_z
float32 roll, pitch, yaw

uint8 progress                    # 进度百分比(0-100)
string status                     # 状态信息
```

## 硬件连接

### I2C连接（Jetson Nano）
```
I2C1 (推荐):
  - 引脚 3 (GPIO 2/I2C1_SDA): SDA 数据线
  - 引脚 5 (GPIO 3/I2C1_SCL): SCL 时钟线
  - 设备路径: /dev/i2c-1
  - IMU地址: 0x23

I2C0:
  - 引脚 27 (SDA), 28 (SCL)
  - 设备路径: /dev/i2c-0
```

### 串口连接
```
支持的串口设备:
  - /dev/ttyUSB0
  - /dev/ttyUSB1
  - /dev/ttyTHS1
  - /dev/ttyAMA0
波特率: 115200
```

## 校准说明

### IMU校准（陀螺仪和加速度计）
校准前请将IMU水平放置并保持静止。

```bash
# 通过Action Client
rosrun yb_imu_driver imu_serial_client.py calibrate
```

### 磁力计校准
校准过程中需要将IMU在各个方向旋转，进行8字形运动。

```bash
# 通过Action Client
rosrun yb_imu_driver imu_serial_client.py calibrate_mag
```

### 温度校准
需要提供当前环境温度。

```bash
# 通过Action Client（25.0为当前温度）
rosrun yb_imu_driver imu_serial_client.py calibrate_temp 25.0
```

## 使用场景

### 场景1：实时数据订阅
```bash
# 终端1：启动服务器（自动发布数据）
roslaunch yb_imu_driver imu_serial.launch

# 终端2：订阅实时数据
rostopic echo /imu_serial/data

# 终端3：查看数据频率
rostopic hz /imu_serial/data
```

### 场景2：校准IMU
```bash
# 终端1：启动服务器
roslaunch yb_imu_driver imu_serial.launch

# 终端2：执行校准
rosrun yb_imu_driver imu_serial_client.py calibrate
```

### 场景3：混合使用
```bash
# 终端1：启动服务器（同时提供Action服务和实时数据）
roslaunch yb_imu_driver imu_serial.launch

# 终端2：订阅实时数据
rostopic echo /imu_serial/data

# 终端3：使用Action Client读取单次数据
rosrun yb_imu_driver imu_serial_client.py single

# 终端4：设置融合算法
rosrun yb_imu_driver imu_serial_client.py algo9
```

## 故障排除

### 无法连接IMU
- 检查硬件连接
- 检查I2C/串口设备权限
- 确认YbImuLib已正确安装

### Action超时
- 检查Action Server是否正常运行
- 增加client.wait_for_result()的超时时间

### 数据不准确
- 执行IMU校准
- 检查融合算法设置（推荐九轴）

### Topic无数据
- 检查`publish_topic`参数是否为`true`
- 检查Topic名称是否正确
- 使用`rostopic list`查看所有Topic

## 文件结构

```
yb_imu_driver/
├── action/
│   ├── IMUI2C.action          # I2C Action定义
│   └── IMUSerial.action       # 串口Action定义
├── scripts/
│   ├── imu_i2c_server.py      # I2C Action Server（含实时发布）
│   ├── imu_i2c_client.py      # I2C Action Client示例
│   ├── imu_serial_server.py   # 串口 Action Server（含实时发布）
│   └── imu_serial_client.py   # 串口 Action Client示例
├── launch/
│   ├── imu_i2c.launch         # I2C启动文件
│   ├── imu_serial.launch      # 串口启动文件
│   └── imu_visualization.launch  # RViz可视化启动文件
├── rviz/
│   └── imu_visualization.rviz # RViz配置文件
├── CMakeLists.txt
├── package.xml
└── README.md
```

## RViz可视化功能

### 显示内容

RViz配置文件 `imu_visualization.rviz` 包含：

1. **Grid（网格）**
   - 平面：XY平面
   - 单元格大小：0.5m
   - 颜色：灰色

2. **TF（坐标变换）**
   - 显示 `imu_link` 坐标系
   - 带箭头和坐标轴

3. **IMU（IMU显示插件）**
   - 显示方向和姿态
   - 绿色方框表示IMU设备
   - 尺寸：0.1×0.2×0.05m
   - 坐标轴显示方向

4. **Axes（坐标轴）**
   - 红色：X轴
   - 绿色：Y轴
   - 蓝色：Z轴

### 使用技巧

1. **旋转视图**
   - 鼠标左键拖动：旋转视角
   - 鼠标中键拖动：平移
   - 鼠标滚轮：缩放

2. **调整显示**
   - 在左侧面板双击 "IMU" 可调整显示属性
   - 修改方框颜色、大小等

3. **固定坐标系**
   - Fixed Frame 设置为 `imu_link`

## 许可证

TODO

## 作者

jetson

加速度计
参数	条件	典型值
量程	—	16 g
分辨率	±16 g	0.0005 g/LSB
RMS噪声	带宽=100 Hz	1.0 mg‑RMS
温漂	-40 °C ~ +85 °C	±0.15 mg/°C
带宽	—	12.5 ~ 1600 Hz
陀螺仪
参数	条件	典型值
量程	—	±2000 °/s
分辨率	±2000 °/s	0.061 (°/s)/LSB
RMS噪声	带宽=100 Hz	0.07 °/s‑RMS
温漂	-40 °C ~ +85 °C	0.015 °/s/°C
带宽	—	12.5 ~ 1600 Hz
磁力计
参数	条件	典型值
量程	—	±8 Gauss
分辨率	±8 Gauss	0.244 mGauss/LSB