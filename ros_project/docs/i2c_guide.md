# I2C通信使用指南

## 概述

I2C（Inter-Integrated Circuit）是一种双线制（SDA、SCL）的串行通信协议，适用于连接低速外设。Jetson Nano提供两个I2C总线（I2C-1和I2C-2），支持连接多种I2C设备。

## 功能特性

- **多设备支持**: 支持连接多个I2C设备
- **自动扫描**: 可自动扫描I2C总线上的设备
- **动态地址设置**: 运行时更改I2C设备地址
- **多线程安全**: 使用锁机制保证线程安全
- **错误处理**: 完善的错误处理和重试机制
- **状态监控**: 实时监控I2C通信状态和统计

## I2C引脚映射

### I2C-1 (主要I2C总线)
| 物理引脚 | GPIO (BCM) | 功能 | 说明 |
|---------|-----------|------|------|
| **3** | GPIO2 | SDA_1 | I2C数据线 |
| **5** | GPIO3 | SCL_1 | I2C时钟线 |

### I2C-2 (辅助I2C总线)
| 物理引脚 | GPIO (BCM) | 功能 | 说明 |
|---------|-----------|------|------|
| **27** | GPIO18 | SDA_2 | I2C数据线 |
| **28** | GPIO19 | SCL_2 | I2C时钟线 |

## ROS话题接口

### 发送话题

#### `/i2c/write_byte`
- **类型**: `std_msgs/Int32`
- **描述**: 写入单个字节到I2C设备
- **示例**:
```bash
rostopic pub /i2c/write_byte std_msgs/Int32 "data: 72"  # 十进制72 (字符'H')
rostopic pub /i2c/write_byte std_msgs/Int32 "data: 0x48"  # 十六进制0x48 (字符'H')
```

#### `/i2c/write_bytes`
- **类型**: `std_msgs/String`
- **描述**: 写入多个字节到I2C设备
- **示例**:
```bash
rostopic pub /i2c/write_bytes std_msgs/String "data: '48 49 4A'"  # 发送'H','I','J'
```

### 接收话题

#### `/i2c/rx_byte`
- **类型**: `std_msgs/Int32`
- **描述**: 从I2C设备接收单个字节
- **示例**:
```bash
rostopic echo /i2c/rx_byte
```

#### `/i2c/rx_bytes`
- **类型**: `std_msgs/String`
- **描述**: 从I2C设备接收多个字节
- **示例**:
```bash
rostopic echo /i2c/rx_bytes
```

### 控制话题

#### `/i2c/read_byte`
- **类型**: `std_msgs/Int32`
- **描述**: 从指定寄存器读取字节
- **示例**:
```bash
rostopic pub /i2c/read_byte std_msgs/Int32 "data: 0"  # 从寄存器0读取
```

#### `/i2c/set_address`
- **类型**: `std_msgs/Int32`
- **描述**: 设置I2C设备地址
- **示例**:
```bash
rostopic pub /i2c/set_address std_msgs/Int32 "data: 72"     # 0x48
```

### 状态话题

#### `/i2c/status`
- **类型**: `std_msgs/String`
- **描述**: I2C状态信息
- **内容**: JSON格式的状态数据
- **示例**:
```bash
rostopic echo /i2c/status
```

状态数据格式:
```json
{
  "connected": true,
  "bus": 1,
  "device_address": "0x48",
  "tx_count": 10,
  "rx_count": 5,
  "error_count": 0
}
```

## 配置参数

### Launch文件参数

#### `i2c_bus`
- **类型**: 整数
- **默认值**: `1`
- **描述**: I2C总线号（1或2）
- **示例**: `1`, `2`

#### `device_address`
- **类型**: 整数
- **默认值**: `0x48`
- **描述**: I2C设备地址（十六进制）
- **示例**: `0x48`, `0x50`, `0x68`

#### `auto_scan`
- **类型**: 布尔值
- **默认值**: `false`
- **描述**: 是否自动扫描I2C设备
- **示例**: `true`, `false`

#### `enable_echo`
- **类型**: 布尔值
- **默认值**: `false`
- **描述**: 是否启用数据回显
- **示例**: `true`, `false`

## 使用方法

### 1. 环境准备

#### 安装依赖
```bash
pip3 install smbus2
```

#### 配置权限
```bash
# 添加用户到i2c组
sudo usermod -a -G i2c jetson

# 登出后重新登录使权限生效
```

#### 验证权限
```bash
# 检查用户组
groups jetson

# 应该包含i2c组
```

### 2. 启动I2C节点

#### 使用默认配置
```bash
source devel/setup.bash
roslaunch communication i2c_comm.launch
```

#### 使用自定义配置
```bash
roslaunch communication i2c_comm_launch \
  i2c_bus:=1 \
  device_address:=0x48 \
  auto_scan:=true \
  enable_echo:=true
```

#### 启用I2C-2
```bash
roslaunch communication i2c_comm_launch i2c_bus:=2 device_address:=0x50
```

### 3. I2C通信操作

#### 写入单个字节
```bash
# 十进制方式
rostopic pub -1 /i2c/write_byte std_msgs/Int32 "data: 72"

# 十六进制方式
rostopic pub -1 /i2c/write_byte std_msgs/Int32 "data: 0x48"
```

#### 写入多个字节
```bash
# 方式1: 空格分隔的十六进制
rostopic pub -1 /i2c/write_bytes std_msgs/String "data: '0x48 0x49 0x4A'"

# 方式2: 纯ASCII字符
rostopic pub -1 /i2c/write_bytes std_msgs/String "data: '72 73 74'"
```

#### 读取字节
```bash
# 读取当前字节
rostopic pub -1 /i2c/read_byte std_msgs/Int32 "data: 0"

# 监听接收
rostopic echo /i2c/rx_byte
```

#### 更改I2C设备地址
```bash
# 改为0x68 (MPU6050)
rostopic pub -1 /i2c/set_address std_msgs/Int32 "data: 104"  # 0x68

# 改为0x50 (EEPROM)
rostopic pub -1 /i2c/set_address std_msgs/Int32 "data: 80"   # 0x50
```

### 4. 自动扫描I2C设备

启动时启用自动扫描：
```bash
roslaunch communication i2c_comm_launch auto_scan:=true
```

输出示例：
```
扫描I2C设备...
  发现设备: 0x48
  发现设备: 0x50
  发现设备: 0x68
总共发现 3 个I2C设备
```

### 5. 手动扫描I2C设备

```python3 << 'EOF'
import smbus2

# 扫描I2C-1总线
bus = smbus2.SMBus(1)
print("扫描I2C-1设备...")

for addr in range(0x03, 0x78):
    try:
        bus.write_byte(addr, 0)
        print(f"发现设备: 0x{addr:02X}")
    except:
        pass

bus.close()
EOF
```

## 常见应用场景

### 场景1: 连接RTC模块 (PCF8574)

#### 连接
```
VCC → 3.3V
GND → GND
SDA → 3号引脚
SCL → 5号引脚
```

#### 使用
```bash
# 启动节点
roslaunch communication i2c_comm_launch device_address:=0x68

# 写入寄存器
rostopic pub /i2c/write_byte std_msgs/Int32 "data: 0"  # 写入0到寄存器0

# 读取时间
rostopic pub -1 /i2c/read_byte std_msgs/Int32 "data: 0"  # 读取寄存器0

# 监听数据
rostopic echo /i2c/rx_byte
```

### 场景2: 连接EEPROM (24LC64)

#### 使用
```bash
# 启动节点
roslaunch communication i2c_comm_launch device_address:=0x50

# 写入数据
rostopic pub -1 /i2c/write_bytes std_msgs/String "data: '0x48 0x49 0x4A'"

# 读取数据
rostopic pub -1 /i2c/read_byte std_msgs/Int32 "data: 0"
```

### 场景3: 连接IMU (MPU6050)

#### 使用
```bash
# 启动节点
roslaunch communication i2c_comm_launch device_address:=0x68 enable_echo:=true

# 写入到寄存器
rostopic pub /i2c/write_byte std_msgs/Int32 "data: 0x6B"  # 0x6B: MPU6050 PWR_MGMT_1

# 读取寄存器
rostopic pub -1 /i2c/read_byte std_msgs/Int32 "data: 0x6B"  # 0x6B: MPU6050 PWR_MGMT_1

# 监听数据
rostopic echo /i2c/rx_byte
```

## 常用I2C设备地址

| 地址 | 设备类型 | 说明 |
|------|----------|------|
| 0x48 | PCF8574 | RTC时钟模块 |
| 0x50 | 24LC64 | 64KB EEPROM |
| 0x68 | MPU6050 | IMU（加速度计/陀螺仪）|
| 0x76 | BNO055 | 9轴IMU |
| 0x77 | BNO055 | 9轴IMU |
| 0x57 | AT24C32 | 32KB EEPROM |
| 0x5A | DS1307 | RTC时钟模块 |

## Jetson Nano I2C限制

### I2C-1 (主要)
- 默认启用，通常连接板上RTC
- 脚本: 3号和5号引脚
- 最大速度: 100kHz
- 支持: 7位和10位地址

### I2C-2 (辅助)
- 需要设备树配置才能使用
- 脚本: 27号和28号引脚
- 最大速度: 400kHz

### 注意事项
1. 需要上拉电阻（通常4.7kΩ）
2. 地址冲突检测：连接前先扫描总线
3. 电平匹配：确保3.3V设备
4. 总线电容：设备过多时可能影响稳定性

## 故障排除

### 问题1: 权限被拒绝

**错误信息**:
```
Permission denied: '/dev/i2c-1'
```

**解决方案**:
```bash
# 添加用户到i2c组
sudo usermod -a -G i2c jetson

# 重新登录
```

### 问题2: I2C设备未检测到

**可能原因**:
1. 设备未正确连接
2. 电源未供电
3. 上拉电阻缺失
4. 地址冲突

**解决方案**:
1. 检查硬件连接
2. 确保设备供电正常
3. 添加上拉电阻
4. 扫描总线查找可用地址

### 问题3: 通信不稳定

**解决方案**:
1. 降低I2C时钟频率
2. 检查上拉电阻值
3. 检查总线电容
4. 使用更短的连接线

## 测试方法

### 1. 手动扫描I2C设备

```python3
import smbus2

# 扫描I2C-1
bus = smbus2.SMBus(1)
for addr in range(0x03, 0x78):
    try:
        bus.write_byte(addr, 0)
        print(f"发现设备: 0x{addr:02X}")
    except:
        pass
bus.close()
```

### 2. 测试I2C读写

```python3
import smbus2

bus = smbus2.SMBus(1)
addr = 0x48

# 写入
bus.write_byte(addr, 0x55)
print("写入: 0x55")

# 读取
data = bus.read_byte(addr)
print(f"读取: 0x{data:02X}")
```

### 3. 使用ROS测试

```bash
# 启动节点
roslaunch communication i2c_comm_launch

# 发送测试数据
rostopic pub -1 /i2c/write_byte std_msgs/Int32 "data: 0x48"

# 监听接收
rostopic echo /serial/rx
```

## 扩展功能

### 1. 批量操作

```bash
# 发送多个字节
for i in {0..255}; do
  rostopic pub -1 /i2c/write_byte std_msgs/Int32 "data: $i"
  sleep 0.01
done
```

### 2. 设备类封装

```python
class I2CDevice:
    def __init__(self, bus=1, addr=0x48):
        self.bus = smbus2.SMBus(bus)
        self.addr = addr
    
    def read_byte(self, reg):
        return self.bus.read_byte_data(self.addr, reg)
    
    def write_byte(self, reg, data):
        self.bus.write_byte_data(self.addr, reg, data)
    
    def read_bytes(self, reg, length):
        return self.bus.read_i2c_block_data(self.addr, reg, length)
```

### 3. 协议解析

```python
def parse_i2c_data(data):
    """解析I2C返回的数据"""
    if isinstance(data, bytes):
        return list(data)
    return []
```

## 参考资源

- [smbus2文档](https://pypi.org/project/smbus2/)
- [Jetson Nano I2C配置](https://developer.nvidia.com/embedded/learn/tutorials/jetson-gpio)
- [I2C协议规范](https://www.nxp.com/docs/en/data-sheet/IMU/MPU6050/MPU-6050-Data-Sheet.pdf)

## 总结

I2C通信模块提供了完整的I2C通信功能，支持多种设备和应用场景。通过ROS话题接口，可以轻松集成到更大的系统中。遵循本文档的使用方法和最佳实践，可以高效、稳定地使用I2C通信功能。