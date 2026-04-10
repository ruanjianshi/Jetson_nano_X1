#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP2515 环回模式测试脚本
硬件：Jetson Nano SPI0 (CE0)，MCP2515 模块，8MHz 晶振
功能：发送 CAN 帧（ID=0x123, DLC=4, Data=11 22 33 44），
      在环回模式下应收到完全相同的帧。
"""

import spidev
import time

# SPI 指令
CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02
CMD_RTS = 0x81          # 仅发送 TXB0
CMD_READ_STATUS = 0xA0

# 寄存器地址
REG_CANSTAT = 0x0E
REG_CANCTRL = 0x0F
REG_CNF1 = 0x2A
REG_CNF2 = 0x29
REG_CNF3 = 0x28
REG_CANINTE = 0x2B
REG_CANINTF = 0x2C
REG_TXB0CTRL = 0x30
REG_TXB0SIDH = 0x31
REG_TXB0SIDL = 0x32
REG_TXB0DLC = 0x35
REG_TXB0D0 = 0x36
REG_RXB0CTRL = 0x60
REG_RXB0SIDH = 0x61
REG_RXB0SIDL = 0x62
REG_RXB0DLC = 0x65
REG_RXB0D0 = 0x66

# 环回模式配置 (8MHz 晶振, 500kbps)
CNF1_VAL = 0x00   # BRP=0
CNF2_VAL = 0x90   # BTLMODE=1, SAM=0, PHSEG1=2, PRSEG=0
CNF3_VAL = 0x02   # PHSEG2=2

def spi_init():
    """初始化 SPI (总线0, 设备0, 1MHz, 模式0)"""
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1000000   # 1MHz，稳定可靠
    spi.mode = 0b00
    spi.bits_per_word = 8
    return spi

def write_reg(spi, addr, value):
    """写入单个寄存器"""
    spi.xfer2([CMD_WRITE, addr, value])

def read_reg(spi, addr):
    """读取单个寄存器"""
    result = spi.xfer2([CMD_READ, addr, 0x00])
    return result[2]

def reset_chip(spi):
    """硬件复位 MCP2515"""
    spi.xfer2([CMD_RESET])
    time.sleep(0.5)
    # 验证是否响应
    canstat = read_reg(spi, REG_CANSTAT)
    print(f"复位后 CANSTAT = 0x{canstat:02X}")
    if canstat is None:
        print("错误: MCP2515 无响应")
        return False
    return True

def set_config_mode(spi):
    """进入配置模式"""
    write_reg(spi, REG_CANCTRL, 0x80)
    time.sleep(0.1)
    # 验证
    ctrl = read_reg(spi, REG_CANCTRL)
    if ctrl != 0x80:
        print(f"配置模式设置失败: CANCTRL=0x{ctrl:02X}")
        return False
    print("已进入配置模式")
    return True

def set_loopback_mode(spi):
    """设置为环回模式 (正常模式时写入0x40)"""
    write_reg(spi, REG_CANCTRL, 0x40)
    time.sleep(0.1)
    stat = read_reg(spi, REG_CANSTAT)
    mode = (stat >> 5) & 0x07
    if mode == 0x02:
        print("环回模式已启用")
        return True
    else:
        print(f"环回模式设置失败，当前模式={mode}")
        return False

def set_normal_mode(spi):
    """恢复普通模式"""
    write_reg(spi, REG_CANCTRL, 0x00)
    time.sleep(0.1)

def clear_interrupts(spi):
    """清除所有中断标志和错误标志"""
    write_reg(spi, REG_CANINTF, 0x00)
    # 错误标志寄存器也可清除 (写1清除)
    # 但为了简单，直接写0x00即可

def send_standard_frame(spi, can_id, data, dlc):
    """发送标准数据帧 (使用 TXB0)"""
    if dlc > 8:
        raise ValueError("DLC不能大于8")
    # 检查 TXB0 是否空闲 (TXREQ位)
    ctrl = read_reg(spi, REG_TXB0CTRL)
    if ctrl & 0x08:
        # 如果有未完成的发送请求，取消它
        write_reg(spi, REG_TXB0CTRL, 0x00)   # 清除TXREQ和其他位
        time.sleep(0.001)
    # 编码标准ID
    sidh = (can_id >> 3) & 0xFF
    sidl = ((can_id & 0x07) << 5) & 0xE0
    # 写寄存器
    write_reg(spi, REG_TXB0SIDH, sidh)
    write_reg(spi, REG_TXB0SIDL, sidl)
    write_reg(spi, REG_TXB0DLC, dlc & 0x0F)
    for i in range(dlc):
        write_reg(spi, REG_TXB0D0 + i, data[i])
    # 对于未使用的数据字节，可选写0（不必须）
    # 启动发送 (RTS命令)
    spi.xfer2([CMD_RTS])
    # 等待发送完成 (检查TX0IF)
    timeout = 100  # 100ms
    while timeout > 0:
        intf = read_reg(spi, REG_CANINTF)
        if intf & 0x04:   # TX0IF
            # 清除标志
            write_reg(spi, REG_CANINTF, intf & ~0x04)
            return True
        time.sleep(0.001)
        timeout -= 1
    print("发送超时")
    return False

def receive_frame(spi):
    """从 RXB0 读取一帧，返回 (id, dlc, data) 或 None"""
    intf = read_reg(spi, REG_CANINTF)
    if not (intf & 0x01):
        return None
    sidh = read_reg(spi, REG_RXB0SIDH)
    sidl = read_reg(spi, REG_RXB0SIDL)
    dlc_reg = read_reg(spi, REG_RXB0DLC)
    dlc = dlc_reg & 0x0F
    # 标准帧ID解码
    can_id = ((sidl >> 5) & 0x07) | (sidh << 3)
    data = []
    for i in range(dlc):
        data.append(read_reg(spi, REG_RXB0D0 + i))
    # 清除接收中断标志
    write_reg(spi, REG_CANINTF, intf & ~0x01)
    return (can_id, dlc, data)

def loopback_test():
    print("=== MCP2515 环回模式测试 ===")
    spi = spi_init()
    print("SPI 已初始化 (1MHz, Mode 0)")

    # 1. 复位芯片
    if not reset_chip(spi):
        spi.close()
        return False

    # 2. 进入配置模式
    if not set_config_mode(spi):
        spi.close()
        return False

    # 3. 配置位定时 (8MHz晶振, 500kbps)
    write_reg(spi, REG_CNF1, CNF1_VAL)
    write_reg(spi, REG_CNF2, CNF2_VAL)
    write_reg(spi, REG_CNF3, CNF3_VAL)
    # 验证写入
    cnf1 = read_reg(spi, REG_CNF1)
    cnf2 = read_reg(spi, REG_CNF2)
    cnf3 = read_reg(spi, REG_CNF3)
    print(f"CNF: 1=0x{cnf1:02X} 2=0x{cnf2:02X} 3=0x{cnf3:02X}")
    if cnf2 != CNF2_VAL:
        print("警告: CNF2 写入验证失败，请检查 SPI 通信")

    # 4. 设置接收缓冲区为接收所有报文 (不滤波)
    write_reg(spi, REG_RXB0CTRL, 0x60)   # 接收所有报文

    # 5. 清除中断
    clear_interrupts(spi)

    # 6. 启用环回模式
    if not set_loopback_mode(spi):
        spi.close()
        return False

    # 7. 清空可能存在的残留接收帧
    while read_reg(spi, REG_CANINTF) & 0x01:
        receive_frame(spi)

    # 8. 准备发送的帧
    test_id = 0x123
    test_data = [0x11, 0x22, 0x33, 0x44]
    test_dlc = 4
    print(f"发送测试帧: ID=0x{test_id:X} DLC={test_dlc} Data=" +
          ' '.join(f'{b:02X}' for b in test_data))

    # 9. 发送
    if not send_standard_frame(spi, test_id, test_data, test_dlc):
        print("发送失败")
        set_normal_mode(spi)
        spi.close()
        return False

    # 10. 等待接收
    print("等待接收...")
    timeout_ms = 200
    while timeout_ms > 0:
        rx = receive_frame(spi)
        if rx is not None:
            recv_id, recv_dlc, recv_data = rx
            print(f"收到帧: ID=0x{recv_id:X} DLC={recv_dlc} Data=" +
                  ' '.join(f'{b:02X}' for b in recv_data))
            if recv_id == test_id and recv_dlc == test_dlc and recv_data == test_data:
                print("✅ 回环测试成功！发送与接收匹配")
                set_normal_mode(spi)
                spi.close()
                return True
            else:
                print("收到不匹配的帧，继续等待...")
        time.sleep(0.001)
        timeout_ms -= 1

    print("❌ 超时未收到回环帧")
    set_normal_mode(spi)
    spi.close()
    return False

if __name__ == "__main__":
    success = loopback_test()
    if success:
        print("测试通过")
    else:
        print("测试失败")