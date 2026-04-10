# Jetson Nano串口引脚对应关系

## 确认的引脚映射（已测试验证）

| 物理引脚 | 设备 | GPIO (BCM) | 功能 | 说明 |
|---------|------|-----------|------|------|
| **8** | `/dev/ttyTHS1` | GPIO14 | TXD0 | 发送数据 |
| **10** | `/dev/ttyTHS1` | GPIO15 | RXD0 | 接收数据 |

## 回环测试方法

### 硬件连接
将8号引脚和10号引脚用跳线短接。

### 测试命令
```bash
sudo python3 -c "
import serial
import time

ser = serial.Serial('/dev/ttyTHS1', 115200, timeout=1.0)
print('✅ 串口已打开')
ser.reset_input_buffer()
ser.reset_output_buffer()

msg = b'TEST'
ser.write(msg)
time.sleep(0.3)

if ser.in_waiting > 0:
    data = ser.read(ser.in_waiting)
    print(f'接收: {data.decode()}')
    if data == msg:
        print('✅ 回环测试成功！')
    else:
        print(f'⚠️  数据: {data}')
else:
    print('❌ 未接收到数据')

ser.close()
"
```

## ROS串口通信使用

### 启动节点
```bash
roslaunch communication serial_comm.launch serial_port:=/dev/ttyTHS1
```

### 发送数据
```bash
rostopic pub /serial/tx std_msgs/String "data: Hello"
```

### 接收数据
```bash
rostopic echo /serial/rx
```

## 注意事项

1. **正确的串口**: 使用 `/dev/ttyTHS1` 而不是 `/dev/ttyTHS2`
2. **引脚位置**: 8号在左列第4个，10号在右列第5个
3. **波特率**: 默认使用115200
4. **权限**: 需要sudo权限或在dialout组中