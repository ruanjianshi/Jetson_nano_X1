# 串口通信使用指南

## 概述

串口通信模块提供了完整的串口通信功能，支持自动检测、自动重连、多线程安全操作，通过ROS话题和服务接口与系统集成。

## 功能特性

- **自动检测串口**: 支持自动检测可用的串口设备
- **多种波特率**: 支持9600、19200、38400、57600、115200等常用波特率
- **自动重连**: 连接断开后自动尝试重新连接
- **多线程安全**: 使用锁机制保证线程安全
- **错误处理**: 完善的错误处理和恢复机制
- **状态监控**: 实时监控串口状态和通信统计
- **数据回显**: 可选的数据回显功能，便于调试

## 串口设备

### Jetson Nano可用串口

#### THS串口（板载）
- `/dev/ttyTHS1` - 主串口（默认调试串口）
- `/dev/ttyTHS2` - 次串口（可用于应用）

#### USB转串口
- `/dev/ttyUSB0` - USB转串口设备0
- `/dev/ttyUSB1` - USB转串口设备1

#### ACM串口
- `/dev/ttyACM0` - CDC ACM设备0
- `/dev/ttyACM1` - CDC ACM设备1

### 串口选择建议

1. **优先使用THS串口**: 性能稳定，无需额外硬件
2. **需要多串口时**: 使用USB转串口模块
3. **调试时**: 使用`/dev/ttyTHS1`

## ROS话题接口

### 发送话题

#### `/serial/tx`
- **类型**: `std_msgs/String`
- **描述**: 发送数据到串口
- **示例**:
```bash
rostopic pub /serial/tx std_msgs/String "data: 'Hello Serial!'"
```

### 接收话题

#### `/serial/rx`
- **类型**: `std_msgs/String`
- **描述**: 从串口接收数据
- **示例**:
```bash
rostopic echo /serial/rx
```

### 状态话题

#### `/serial/status`
- **类型**: `std_msgs/String`
- **描述**: 串口状态信息
- **内容**: JSON格式的状态数据
- **示例**:
```bash
rostopic echo /serial/status
```

状态数据格式:
```json
{
  "connected": true,
  "port": "/dev/ttyTHS1",
  "baud_rate": 115200,
  "tx_count": 100,
  "rx_count": 50,
  "error_count": 0
}
```

## 配置参数

### Launch文件参数

#### `serial_port`
- **类型**: 字符串
- **默认值**: `auto`
- **描述**: 串口设备路径
- **示例**: `/dev/ttyTHS1`, `/dev/ttyUSB0`

#### `baud_rate`
- **类型**: 整数
- **默认值**: `115200`
- **描述**: 串口波特率
- **可选值**: 9600, 19200, 38400, 57600, 115200

#### `timeout`
- **类型**: 浮点数
- **默认值**: `1.0`
- **描述**: 串口读取超时时间（秒）

#### `auto_reconnect`
- **类型**: 布尔值
- **默认值**: `true`
- **描述**: 是否启用自动重连

#### `reconnect_interval`
- **类型**: 浮点数
- **默认值**: `2.0`
- **描述**: 重连间隔时间（秒）

#### `enable_echo`
- **类型**: 布尔值
- **默认值**: `false`
- **描述**: 是否启用数据回显

## 使用方法

### 1. 环境准备

#### 安装依赖
```bash
pip3 install pyserial
```

#### 配置权限
```bash
# 添加用户到dialout组
sudo usermod -a -G dialout jetson

# 登出后重新登录使权限生效
```

#### 验证权限
```bash
# 检查用户组
groups jetson

# 查看串口权限
ls -l /dev/ttyTHS*
```

### 2. 启动串口节点

#### 使用默认配置
```bash
source devel/setup.bash
roslaunch communication serial_comm.launch
```

#### 使用自定义配置
```bash
roslaunch communication serial_comm_launch \
  serial_port:=/dev/ttyTHS1 \
  baud_rate:=115200 \
  enable_echo:=true
```

#### 自动检测串口
```bash
roslaunch communication serial_comm.launch serial_port:=auto
```

### 3. 发送数据

#### 使用话题发布
```bash
# 发送单个消息
rostopic pub -1 /serial/tx std_msgs/String "data: 'Hello Serial!'"

# 发送多条消息
for i in {1..10}; do
  rostopic pub -1 /serial/tx std_msgs/String "data: 'Message $i'"
  sleep 0.5
done
```

#### 使用测试工具
```bash
# 自动测试模式
python3 src/communication/scripts/serial_comm_tester.py test

# 交互模式
python3 src/communication/scripts/serial_comm_tester.py interactive
```

### 4. 接收数据

#### 监听接收话题
```bash
rostopic echo /serial/rx
```

#### 监听状态话题
```bash
rostopic echo /serial/status
```

### 5. 测试串口通信

#### 使用Shell测试脚本
```bash
# 完整测试
bash scripts/test_serial.sh all

# 快速测试
bash scripts/test_serial.sh quick
```

#### 使用硬件测试工具
```bash
python3 scripts/test_serial_hardware.py
```

## 常见应用场景

### 场景1: 与Arduino通信

#### Arduino端代码
```cpp
void setup() {
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    char data = Serial.read();
    Serial.print("Received: ");
    Serial.println(data);
  }
}
```

#### Jetson端控制
```bash
# 启动串口节点
roslaunch communication serial_comm.launch serial_port:=/dev/ttyUSB0 baud_rate:=115200

# 发送数据
rostopic pub /serial/tx std_msgs/String "data: 'A'"

# 接收数据
rostopic echo /serial/rx
```

### 场景2: 传感器数据采集

#### 启动节点
```bash
roslaunch communication serial_comm.launch serial_port:=/dev/ttyTHS2 baud_rate:=9600
```

#### 持续接收数据
```bash
rostopic echo /serial/rx --noarr > sensor_data.txt
```

### 场景3: 设备控制

#### 发送控制命令
```bash
# 开启设备
rostopic pub -1 /serial/tx std_msgs/String "data: 'ON'"

# 关闭设备
rostopic pub -1 /serial/tx std_msgs/String "data: 'OFF'"
```

#### 检查设备状态
```bash
rostopic echo /serial/status
```

## 测试方法

### 1. 回环测试

需要硬件支持：将TX和RX引脚短接

```bash
# 启动节点
roslaunch communication serial_comm.launch

# 运行回环测试
python3 src/communication/scripts/serial_comm_tester.py loop
```

### 2. 双机通信测试

#### 机器A（发送端）
```bash
roslaunch communication serial_comm.launch serial_port:=/dev/ttyTHS1
rostopic pub /serial/tx std_msgs/String "data: 'Hello from Machine A'"
```

#### 机器B（接收端）
```bash
roslaunch communication serial_comm.launch serial_port:=/dev/ttyTHS2
rostopic echo /serial/rx
```

### 3. 性能测试

```bash
# 启动节点
roslaunch communication serial_comm.launch

# 发送大量数据
for i in {1..1000}; do
  rostopic pub -1 /serial/tx std_msgs/String "data: 'Test message $i'"
done

# 检查状态
rostopic echo /serial/status | grep tx_count
```

## 故障排除

### 问题1: 权限被拒绝

**错误信息**:
```
[Errno 13] Permission denied: '/dev/ttyTHS1'
```

**解决方案**:
```bash
# 添加用户到dialout组
sudo usermod -a -G dialout jetson

# 重新登录
```

### 问题2: 串口未找到

**错误信息**:
```
未检测到可用的串口
```

**解决方案**:
```bash
# 检查可用串口
ls -l /dev/tty*

# 查看串口详细信息
dmesg | grep tty
```

### 问题3: 连接失败

**错误信息**:
```
串口连接异常: could not open port
```

**解决方案**:
1. 检查串口是否被其他程序占用
2. 检查波特率是否正确
3. 检查硬件连接是否正常

### 问题4: 接收不到数据

**可能原因**:
1. 对端设备未发送数据
2. 波特率不匹配
3. 硬件连接问题

**解决方案**:
1. 确认对端设备正常工作
2. 检查波特率配置
3. 检查TX/RX连接
4. 使用示波器或逻辑分析仪调试

## 性能优化

### 1. 波特率选择

| 波特率 | 适用场景 | 说明 |
|--------|----------|------|
| 9600 | 低速设备 | 兼容性最好 |
| 115200 | 高速设备 | 最常用 |
| 921600 | 超高速 | 需要硬件支持 |

### 2. 缓冲区优化

```python
# 在代码中调整缓冲区大小
ser = serial.Serial(
    port=serial_port,
    baudrate=baud_rate,
    timeout=1.0,
    write_timeout=1.0,
    xonxoff=False,
    rtscts=False,
    dsrdtr=False
)
```

### 3. 批量发送

```bash
# 批量发送数据（减少ROS话题开销）
for msg in "Message1 Message2 Message3"; do
  rostopic pub /serial/tx std_msgs/String "data: '$msg'"
done
```

## 扩展功能

### 1. 二进制数据传输

```python
# 发送二进制数据
import struct
data = struct.pack('I', 12345)  # 打包为4字节整数
ser.write(data)
```

### 2. 协议解析

```python
# 自定义协议解析
def parse_protocol(data):
    if data.startswith(b'\xAA\x55'):
        # 提取数据
        return data[2:]
    return None
```

### 3. 多串口管理

```bash
# 启动多个串口节点
roslaunch communication serial_comm.launch serial_port:=/dev/ttyTHS1 name:=serial1
roslaunch communication serial_comm.launch serial_port:=/dev/ttyTHS2 name:=serial2
```

## 最佳实践

### 1. 错误处理

```python
try:
    ser.write(data)
except serial.SerialException as e:
    rospy.logerr(f'串口写入错误: {e}')
    # 尝试重新连接
```

### 2. 资源清理

```python
def cleanup():
    if ser and ser.is_open:
        ser.close()
```

### 3. 状态监控

```python
# 定期检查串口状态
rospy.Timer(rospy.Duration(1.0), check_serial_status)
```

## 参考资源

- [pyserial文档](https://pyserial.readthedocs.io/)
- [ROS串口通信教程](http://wiki.ros.org/rosserial)
- [Jetson Nano串口配置](https://developer.nvidia.com/embedded/learn/tutorials/serial-console-nugetson-xavier-nx-devkit)
- [串口通信协议](https://en.wikipedia.org/wiki/Serial_communication)

## 示例代码

### Python示例：自定义串口节点

```python
#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import serial

class CustomSerialNode:
    def __init__(self):
        rospy.init_node('custom_serial_node')
        
        self.ser = serial.Serial('/dev/ttyTHS1', 115200, timeout=1)
        
        rospy.Subscriber('custom/tx', String, self.tx_callback)
        self.rx_pub = rospy.Publisher('custom/rx', String, queue_size=10)
        
        rospy.Timer(rospy.Duration(0.01), self.rx_read)
    
    def tx_callback(self, msg):
        if self.ser.is_open:
            self.ser.write(msg.data.encode())
    
    def rx_read(self, event):
        if self.ser.in_waiting > 0:
            data = self.ser.read(self.ser.in_waiting)
            self.rx_pub.publish(String(data=data.decode()))
    
    def cleanup(self):
        if self.ser.is_open:
            self.ser.close()

if __name__ == '__main__':
    node = CustomSerialNode()
    rospy.spin()
    node.cleanup()
```

## 总结

串口通信模块提供了完整的串口通信解决方案，支持多种配置和使用场景。通过ROS话题接口，可以轻松集成到更大的系统中。遵循本文档的使用方法和最佳实践，可以高效、稳定地使用串口通信功能。