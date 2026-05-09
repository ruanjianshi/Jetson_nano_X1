# SPI通信使用指南

## 概述

SPI（Serial Peripheral Interface）是一种高速同步串行通信协议，适用于连接高速外设。Jetson Nano提供两个SPI接口（SPI0和SPI1），支持全双工高速通信。

## 功能特性

- **高速通信**: 支持多种时钟速度（最高可达数MHz）
- **全双工**: 支持同时发送和接收数据
- **灵活配置**: 支持多种SPI模式和时钟极性
- **数据传输**: 支持8位、16位、32位数据宽度
- **错误处理**: 完善的错误处理和状态监控
- **实时统计**: 发送/接收字节统计

## SPI引脚映射

### SPI0 (主要SPI接口)
| 物理引脚 | GPIO (BCM) | 功能 | 说明 |
|---------|-----------|------|------|
| **19** | GPIO10 | MOSI | 主出从入数据线 |
| **21** | GPIO9 | MISO | 主入从出数据线 |
| **23** | GPIO11 | SCLK | 串行时钟 |
| **24** | GPIO8 | CS0_N | 片选信号0 |
| **26** | GPIO7 | CS1_N | 片选信号1 |

### SPI1 (辅助SPI接口)
| 物理引脚 | GPIO ( BCM) | 功能 | 说明 |
|---------|-----------|------|------|
| **38** | GPIO20 | MOSI | 主出从入数据线 |
| **40** | GPIO19 | MISO | 主入从出数据线 |
| -- | -- | SCLK | 需要额外配置 |
| -- | -- | CS_N | 需要额外配置 |

## SPI模式

| 模式 | CPOL | CPHA | 说明 |
|------|------|------|------|
| 0 | 0 | 0 | 时钟空闲低电平，数据在上升沿采样 |
| 1 | 0 | 1 | 时钟空闲低电平，数据在下降沿采样 |
| 2 | 1 | 0 | 时钟空闲高电平，数据在上升沿采样 |
| 3 | 1 | 1 | 时钟高电平，数据在下降沿采样 |

## ROS话题接口

### 传输话题

#### `/spi/transfer`
- **类型**: `std_msgs/String`
- **描述**: SPI数据传输（同时发送和接收）
- **示例**:
```bash
rostopic pub /spi/transfer std_msgs/String "data: '0x01 0x02 0x03'"
```

#### `/spi/write`
- **类型**: `std_msgs/String`
- **描述**: SPI写入数据（只发不收）
- **示例**:
```bash
rostopic pub /spi/write std_msgs/String "data: '0xAA 0xBB 0xCC'"
```

#### `/spi/read`
- **类型**: `std_msgs/Int32`
- **描述**: SPI读取数据（只收不发）
- **参数**: 读取的字节数
- **示例**:
```bash
rostopic pub /spi/read std_msgs/Int32 "data: 10"
```

### 接收话题

#### `/spi/rx`
- **类型**: `std_msgs/String`
- **描述**: SPI接收的数据
- **格式**: 十六进制字节序列
- **示例**:
```bash
rostopic echo /spi/rx
```

### 状态话题

#### `/spi/status`
- **类型**: `std_msgs/String`
- **描述**: SPI状态信息
- **内容**: JSON格式的状态数据
- **示例**:
```bash
rostopic echo /spi/status
```

状态数据格式:
```json
{
  "connected": true,
  "device": "/dev/spidev0.0",
  "mode": 0,
  "max_speed": 1000000,
  "bits_per_word": 8,
  "tx_count": 100,
  "rx_count": 50,
  "error_count": 0
}
```

## 配置参数

### Launch文件参数

#### `spi_device`
- **类型**: 字符串
- **默认值**: `/dev/spidev0.0`
- **描述**: SPI设备路径
- **示例**: `/dev/spidev0.0`, `/dev/spidev1.0`

#### `spi_mode`
- **类型**: 整数
- **默认值**: `0`
- **描述**: SPI模式 (0-3)
- **示例**: `0`, `1`, `2`, `3`

#### `max_speed`
- **类型**: 整数
- **默认值**: `1000000`
- **描述**: 最大时钟速度（Hz）
- **示例**: `500000`, `1000000`, `2000000`

#### `bits_per_word`
- **类型**: 整数
- **默认值**: `8`
- **描述**: 每字位数
- **示例**: `8`, `16`, `32`

#### `enable_echo`
- **类型**: 布尔值
- **默认值**: `false`
- **描述**: 是否启用数据回显

## 使用方法

### 1. 环境准备

#### 安装依赖
```bash
pip3 install spidev
```

#### 配置权限
```bash
# 添加用户到spi组
sudo usermod -a -G spi jetson

# 登出后重新登录使权限生效
```

#### 验证权限
```bash
# 检查用户组
groups jetson

# 检查SPI设备
ls -l /dev/spidev*
```

### 2. 启用SPI

#### 检查内核模块
```bash
# 检查spidev模块
lsmod | grep spidev

# 如果未加载，加载内核模块
sudo modprobe spidev
```

#### 检查SPI设备
```bash
# 查看可用SPI设备
ls -l /dev/spidev*
```

### 3. 启动SPI节点

#### 使用默认配置
```bash
source devel/setup.bash
roslaunch communication spi_comm.launch
```

#### 使用自定义配置
```bash
roslaunch communication spi_comm.launch \
  spi_device:=/dev/spidev0.0 \
  spi_mode:=0 \
  max_speed:=1000000 \
  bits_per_word:=8 \
  enable_echo:=true
```

#### 使用SPI1
```bash
roslaunch communication spi_comm.launch spi_device:=/dev/spidev1.0
```

### 4. SPI通信操作

#### 数据传输（发送和接收）
```bash
# 发送3个字节，同时接收3个字节
rostopic pub /spi/transfer std_msgs/String "data: '0x01 0x02 0x03'"
```

#### 只写入数据
```bash
# 写入3个字节
rostopic pub /spi/write std_msgs/String "data: '0xAA 0xBB 0xCC'"
```

#### 只读取数据
```bash
# 读取10个字节
rostopic pub -1 /spi/read std_msgs/Int32 "data: 10"

# 监听接收数据
rostopic echo /spi/rx
```

### 5. 测试SPI通信

#### 回环测试（需要硬件支持）

**硬件连接**:
- 短接19号引脚（MOSI）和21号引脚（MISO）

**测试代码**:
```bash
# 启动节点
roslaunch communication spi_comm.launch enable_echo:=true

# 发送测试数据
rostopic pub -1 /spi/transfer std_msgs/String "data: '0x41 0x42 0x43'"

# 监听接收数据
rostopic echo /spi/rx
```

### 6. 与SPI设备通信

#### 连接ADC模块（如ADS1115）

```bash
# 启动节点
roslaunch communication spi_comm_launch max_speed:=1000000

# 配置ADC寄存器
# 写入配置寄存器
rostopic pub /spi/transfer std_msgs/String "data: '0x01 0x83 0xC3'"

# 读取ADC数据
rostopic pub -1 /spi/read std_msgs/Int32 "data: 2"

# 监听ADC数据
rostopic echo /spi/rx
```

#### 连接显示屏（如OLED）

```bash
# 初始化OLED
rostopic pub /spi/write std_msgs/String "data: '0xAE 0xA8 0xD3 0x00 0x8F'"

# 显示数据
rostopic pub /spi/transfer std_msgs/String "data: '0x40 0x41 0x42'"
```

## 常用SPI设备

| 设备类型 | 说明 | 典型速度 | 应用场景 |
|----------|------|----------|----------|
| ADC模数转换器 | 模拟量采集 | 10-500kHz | 传感器数据采集 |
| DAC数模转换器 | 模拟量输出 | 1-10MHz | 音频输出、信号生成 |
| 显示屏 | OLED/LCD | 1-10MHz | 用户界面、信息显示 |
| 存储器 | Flash/SD卡 | 1-20MHz | 数据存储 |
| 传感器 | 加速度计、陀螺仪 | 1-10MHz | 运动检测、姿态控制 |
| 无线模块 | NRF24L01, ESP8266 | 1-10MHz | 无线通信 |

## SPI时序图

### 模式0 (CPOL=0, CPHA=0)
```
SCLK: _/‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
MOSI:  D₀ D₁ D₂ D₃ ... Dₙ
CS#:   ────────────────────
MISO:  D₀ D₁ D₂ D₃ ... Dₙ
```

### 模式3 (CPOL=1, CPHA=1)
```
SCLK: ‾\__/‾\__/‾\__/‾\__/‾\__/‾\__/‾\__/‾
MOSI:  D₀ D₁ D₂ D₃ ... Dₙ
CS#:   ────────────────────
MISO:  D₀ D₁ D₂ D₃ ... Dₙ
```

## 性能优化

### 1. 时钟速度选择

| 速度范围 | 适用设备 | 说明 |
|----------|----------|------|
| 低速 (<100kHz) | EEPROM, RTC | 需要低速的设备 |
| 中速 (100-1MHz) | 传感器, ADC | 大多数传感器 |
| 高速 (1-10MHz) | 显示屏, Flash | 高速设备 |
| 超高速 (>10MHz) | 特殊应用 | 需要硬件支持 |

### 2. 数据块传输

```bash
# 批量发送数据
for i in {0..255}; do
  hex_value=$(printf "0x%02X" $i)
  rostopic pub -1 /spi/transfer std_msgs/String "data: '$hex_value'"
  sleep 0.001
done
```

### 3. DMA传输（如果支持）
部分SPI控制器支持DMA，可以显著提高性能。

## 故障排除

### 问题1: SPI设备未找到

**错误信息**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/dev/spidev0.0'
```

**解决方案**:
```bash
# 检查SPI设备
ls -l /dev/spi*

# 加载内核模块
sudo modprobe spidev

# 查看设备树
ls /sys/class/spi/
```

### 问题2: 权限被拒绝

**错误信息**:
```
PermissionError: [Errno 13] Permission denied: '/dev/spidev0.0'
```

**解决方案**:
```bash
# 添加用户到spi组
sudo usermod -a -G spi jetson

# 重新登录
```

### 问题3: 数据传输错误

**可能原因**:
1. 时钟速度过高
2. SPI模式不匹配
3. 设备配置错误
4. 连接问题

**解决方案**:
1. 降低时钟速度
2. 检查SPI模式
3. 检查设备配置寄存器
4. 检查硬件连接

### 问题4: 只能发送不能接收

**可能原因**:
1. MISO引脚未连接
2. SPI配置错误
3. 设备只写模式

**解决方案**:
1. 确认MISO引脚连接
2. 检查SPI配置参数
3. 检查设备寄存器

## 测试方法

### 1. SPI回环测试

**硬件连接**: 短接19号（MOSI）和21号（MISO）

```python
import spidev

spi = spidev.SpiDev()
spi.open('/dev/spidev0.0')
spi.max_speed_hz = 1000000
spi.mode = 0
spi.bits_per_word = 8

# 发送测试数据
test_data = [0x41, 0x42, 0x43]  # "ABC"
print(f"发送: {' '.join(f'0x{b:02X}' for b in test_data)}")

# 接收数据
response = spi.xfer2(test_data)
print(f"接收: {' '.join(f'0x{b:02X}' for b in response)}")

spi.close()
```

### 2. 测试特定设备

#### 连接ADC测试
```python
import spidev

spi = spidev.SpiDev()
spi.open('/dev/spidev0.0')
spi.max_speed_hz = 1000000
spi.mode = 0

# 读取ADC值
msg = [0x01, 0x83, 0xC3]  # 配置寄存器
spi.xfer2(msg)

msg = [0x01]  # 读取通道1
data = spi.xfer2(msg)
adc_value = (data[0] << 8) | data[1]
voltage = (adc_value * 3.3 / 65536)

print(f"ADC值: {adc_value}")
print(f"电压: {voltage:.3f}V")

spi.close()
```

### 3. 使用ROS测试

```bash
# 启动节点
roslaunch communication spi_comm_launch enable_echo:=true

# 发送测试数据
rostopic pub /spi/transfer std_msgs/String "data: '0x01 0x02 0x03 0x04'"

# 监听接收数据
rostopic echo /spi/rx
```

## 扩展功能

### 1. 多片选控制

```bash
# 选择CS0 (片选0)
rostopic pub /spi/transfer std_msgs/String "data: '0x01 0x02'"
```

### 2. 双向数据传输

```python
def spi_bidirectional_transfer(tx_data, length):
    """双向SPI传输"""
    spi.xfer2(tx_data + [0x00] * (length - len(tx_data)))
```

### 3. 设备驱动封装

```python
class SPIDevice:
    def __init__(self, device='/dev/spidev0.0'):
        self.spi = spidev.SpiDev()
        self.spi.open(device)
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0
        self.bits_per_word = 8
    
    def transfer(self, data):
        """传输数据"""
        return self.spi.xfer2(data)
    
    def write(self, data):
        """写入数据"""
        self.spi.writebytes(data)
    
    def read(self, length):
        """读取数据"""
        return self.spi.readbytes(length)
    
    def close(self):
        """关闭SPI"""
        self.spi.close()
```

## 常见应用场景

### 场景1: 连接OLED显示屏

```bash
# 初始化OLED
rostopic pub /spi/write std_msgs/String "data: '0xAE 0xA8 0xD3 0x00 0x8F'"

# 显示内容
rostopic pub /spi/transfer std_msgs/String "data: '0x40 0x41 0x42'"
```

### 场景2: 连接ADC读取传感器数据

```bash
# 配置ADC
rostopic pub /spi/write std_msgs/String "data: '0x01 0x83 0xC3'"

# 读取数据
rostopic pub -1 /spi/read std_msgs/32 "data: 2"

# 获取ADC值
rostopic echo /spi/rx
```

### 场景3: 高速数据采集

```bash
# 循环发送数据
for i in {0..999}; do
  hex_val=$(printf "0x%02X" $((i % 256))
  rostopic pub -1 /spi/transfer std_msgs/String "data: '$hex_val'"
  sleep 0.001
done
```

## 参考资源

- [spidev文档](https://pypi.org/project/spidev/)
- [SPI协议规范](https://www.nxp.com/docs/en/data-sheet/SPI/bus_spi.pdf)
- [Jetson Nano GPIO使用](https://developer.nvidia.com/embedded/learn/tutorials/jetson-gpio)

## 总结

SPI通信模块提供了高速、灵活的串口通信解决方案。通过ROS话题接口，可以轻松集成到更大的系统中。SPI支持高速全双工通信，适用于连接各种高速外设。遵循本文档的使用方法和最佳实践，可以高效、稳定地使用SPI通信功能。