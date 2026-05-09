#!/usr/bin/env python3
"""
串口通信测试脚本（独立测试）
用于测试串口硬件和通信功能
"""

import sys
import time

def test_pyserial():
    """测试pyserial库"""
    print("="*50)
    print("测试pyserial库")
    print("="*50)
    
    try:
        import serial
        print(f"✅ pyserial版本: {serial.VERSION}")
        print(f"✅ pyserial已正确安装")
        return True
    except ImportError:
        print("❌ pyserial未安装")
        return False

def list_serial_ports():
    """列出可用串口"""
    print("\n" + "="*50)
    print("扫描可用串口")
    print("="*50)
    
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        
        if ports:
            print(f"✅ 找到 {len(ports)} 个串口设备:")
            for port in ports:
                print(f"  - {port.device}")
                print(f"    描述: {port.description}")
                print(f"    硬件ID: {port.hwid}")
        else:
            print("⚠️  未找到串口设备")
        
        return ports
    except Exception as e:
        print(f"❌ 扫描串口失败: {e}")
        return []

def test_serial_port(port_name):
    """测试指定串口"""
    print("\n" + "="*50)
    print(f"测试串口: {port_name}")
    print("="*50)
    
    import serial
    
    # 测试不同波特率
    baud_rates = [9600, 115200]
    
    for baud in baud_rates:
        try:
            print(f"\n测试波特率: {baud}")
            ser = serial.Serial(
                port=port_name,
                baudrate=baud,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            if ser.is_open:
                print(f"  ✅ 成功打开串口")
                
                # 清空缓冲区
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                
                # 发送测试数据
                test_data = "Hello Serial!"
                ser.write(test_data.encode())
                print(f"  ✅ 发送数据: {test_data}")
                
                time.sleep(0.1)
                
                # 读取数据（如果支持回环）
                if ser.in_waiting > 0:
                    received = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    print(f"  ✅ 接收数据: {received}")
                else:
                    print(f"  ℹ️  无接收数据（需要硬件支持）")
                
                # 关闭串口
                ser.close()
                print(f"  ✅ 关闭串口")
                
        except serial.SerialException as e:
            print(f"  ❌ 串口操作失败: {e}")
            return False
        except PermissionError:
            print(f"  ❌ 权限不足: 请将用户添加到dialout组")
            print(f"  运行: sudo usermod -a -G dialout $USER")
            return False
        except Exception as e:
            print(f"  ❌ 未知错误: {e}")
            return False
    
    return True

def test_ths_serial():
    """测试Jetson Nano THS串口"""
    print("\n" + "="*50)
    print("测试Jetson Nano THS串口")
    print("="*50)
    
    ths_ports = ['/dev/ttyTHS1', '/dev/ttyTHS2']
    
    for port in ths_ports:
        print(f"\n尝试访问 {port}...")
        if test_serial_port(port):
            print(f"✅ {port} 可正常使用")
        else:
            print(f"❌ {port} 无法使用")

def interactive_test():
    """交互式测试"""
    print("\n" + "="*50)
    print("交互式串口测试")
    print("="*50)
    
    port = input("请输入串口设备路径 (例如 /dev/ttyTHS1): ").strip()
    if not port:
        print("取消测试")
        return
    
    baud = input("请输入波特率 (默认115200): ").strip()
    if not baud:
        baud = 115200
    else:
        try:
            baud = int(baud)
        except ValueError:
            print("❌ 无效的波特率")
            return
    
    import serial
    
    try:
        print(f"\n打开串口: {port}@{baud}bps")
        ser = serial.Serial(port, baudrate=baud, timeout=1.0)
        
        if ser.is_open:
            print("✅ 串口已打开")
            print("输入要发送的消息 (输入 'exit' 退出):")
            
            while True:
                try:
                    msg = input("> ")
                    if msg.lower() == 'exit':
                        break
                    
                    ser.write(msg.encode() + b'\n')
                    print(f"已发送: {msg}")
                    
                    # 读取响应
                    time.sleep(0.1)
                    if ser.in_waiting > 0:
                        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        print(f"接收: {response}")
                        
                except KeyboardInterrupt:
                    print("\n中断输入")
                    break
            
            ser.close()
            print("✅ 串口已关闭")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    """主函数"""
    print("Jetson Nano 串口通信测试工具")
    print("="*50)
    
    # 测试pyserial
    if not test_pyserial():
        print("\n请先安装pyserial:")
        print("  pip3 install pyserial")
        sys.exit(1)
    
    # 列出可用串口
    ports = list_serial_ports()
    
    # 测试THS串口
    test_ths_serial()
    
    # 交互式测试
    print("\n是否进行交互式测试? (y/n): ")
    choice = input().strip().lower()
    if choice == 'y':
        interactive_test()
    
    print("\n" + "="*50)
    print("测试完成")
    print("="*50)
    print("\n使用说明:")
    print("1. 确保用户在dialout组中: sudo usermod -a -G dialout $USER")
    print("2. 登出后重新登录以使组权限生效")
    print("3. 连接串口设备（如USB转串口模块）")
    print("4. 使用串口测试工具进行通信测试")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(0)