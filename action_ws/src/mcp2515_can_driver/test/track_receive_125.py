#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import spidev
import time

# ---------- SPI 命令 ----------
CMD_RESET        = 0xC0
CMD_READ         = 0x03
CMD_WRITE        = 0x02
CMD_BIT_MODIFY   = 0x05
CMD_READ_RXB0    = 0x90   # 读 RXB0 缓冲器（自动清除 RX0IF）
CMD_READ_RXB1    = 0x94   # 读 RXB1 缓冲器（自动清除 RX1IF）
CMD_RTS_TXB0     = 0x81   # 请求发送 TXB0

# ---------- 寄存器地址 ----------
REG = {
    'CANSTAT':  0x0E,
    'CANCTRL':  0x0F,
    'CNF3':     0x28,
    'CNF2':     0x29,
    'CNF1':     0x2A,
    'CANINTE':  0x2B,
    'CANINTF':  0x2C,
    'EFLG':     0x2D,
    'RXB0CTRL': 0x60,
    'RXB0SIDH': 0x61,
    'RXB0SIDL': 0x62,
    'RXB0EID8': 0x63,
    'RXB0EID0': 0x64,
    'RXB0DLC':  0x65,
    'RXB0D0':   0x66,
    'RXB1CTRL': 0x70,
}

# ---------- 位掩码定义（参考 2515.h）----------
# CANCTRL
REQOP_NORMAL   = 0x00
REQOP_CONFIG   = 0x80
CLKOUT_ENABLED = 0x04
CLKOUT_PRE_8   = 0x03

# CNF1
SJW_1TQ = 0x00   # SJW=0 -> 1TQ
BRP_0   = 0x00   # BRP=0 -> TQ=2*(0+1)/8M=250ns

# CNF2
BTLMODE_CNF3    = 0x80
SAM_1X          = 0x00
PHSEG1_4TQ      = 0x18   # PS1=4TQ -> PHSEG1=3 -> 0x18
PRSEG_1TQ       = 0x00   # PropSeg=1TQ -> PRSEG=0

# CNF3
PHSEG2_2TQ      = 0x01   # PS2=2TQ -> PHSEG2=1

# RXB0CTRL
RXM_RCV_ALL     = 0x60   # 接收所有报文（不滤波）
BUKT_NO_ROLLOVER= 0x00

# CANINTE
RX0IE_ENABLED   = 0x01

# CANINTF
RX0IF_RESET     = 0x01   # 写1清零

class MCP2515RecvTest:
    def __init__(self, spi_bus=0, spi_device=0, spi_speed=1000000):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = spi_speed
        self.spi.mode = 0b00
        self.spi.bits_per_word = 8

    def write_reg(self, addr, value):
        self.spi.xfer2([CMD_WRITE, addr, value])

    def read_reg(self, addr):
        resp = self.spi.xfer2([CMD_READ, addr, 0x00])
        return resp[2]

    def init_can(self):
        """初始化 MCP2515：500kbps, 75% 采样点 (8MHz晶振)"""
        # 复位
        self.spi.xfer2([CMD_RESET])
        time.sleep(0.5)

        # 进入配置模式
        self.write_reg(REG['CANCTRL'], REQOP_CONFIG)
        time.sleep(0.1)

        # 配置位定时
        self.write_reg(REG['CNF1'], SJW_1TQ | BRP_0)                # CNF1 = 0x00
        self.write_reg(REG['CNF2'], BTLMODE_CNF3 | SAM_1X | PHSEG1_4TQ | PRSEG_1TQ)  # 0x98
        self.write_reg(REG['CNF3'], PHSEG2_2TQ)                    # 0x01

        # 设置接收缓冲器0：接收所有报文，不滚存
        self.write_reg(REG['RXB0CTRL'], RXM_RCV_ALL | BUKT_NO_ROLLOVER)  # 0x60

        # 清空所有中断标志（写1清零）
        self.write_reg(REG['CANINTF'], 0xFF)

        # 使能接收缓冲器0中断（仅用于轮询标志，不使用INT引脚）
        self.write_reg(REG['CANINTE'], RX0IE_ENABLED)   # 0x01

        # 切换到正常模式，使能CLKOUT（可选）
        self.write_reg(REG['CANCTRL'], REQOP_NORMAL | CLKOUT_ENABLED)
        time.sleep(0.1)

        # 验证是否进入正常模式
        canstat = self.read_reg(REG['CANSTAT'])
        if (canstat & 0xE0) != REQOP_NORMAL:
            print(f"警告：未进入正常模式，CANSTAT=0x{canstat:02X}")
        else:
            print("初始化完成: 500kbps, 采样点75%")
        return True

    def receive_frame(self):
        """检查 RXB0 是否有报文，使用读 RX 缓冲器指令自动清除标志"""
        intf = self.read_reg(REG['CANINTF'])
        if intf is None:
            return None

        # 只检查 RXB0 中断标志
        if not (intf & RX0IE_ENABLED):
            return None

        # 发送读 RXB0 缓冲器指令，读取 14 字节（标准帧）
        # 该指令会自动将 CANINTF.RX0IF 清零
        resp = self.spi.xfer2([CMD_READ_RXB0] + [0x00]*14)
        rx_data = resp[1:]   # 跳过命令回显字节

        # 解析标准帧
        sidh = rx_data[0]
        sidl = rx_data[1]
        dlc_reg = rx_data[5]
        dlc = dlc_reg & 0x0F
        remote = (dlc_reg & 0x40) != 0

        # 计算标准 ID
        can_id = ((sidl >> 5) & 0x07) | (sidh << 3)

        # 读取数据字节
        data = list(rx_data[6:6+dlc])

        return {
            'id': can_id,
            'dlc': dlc,
            'data': data,
            'remote': remote,
        }

    def run(self):
        if not self.init_can():
            return
        print("开始监听 CAN 总线 (500kbps, 采样点75%)，按 Ctrl+C 退出...")
        try:
            while True:
                frame = self.receive_frame()
                if frame:
                    data_str = ' '.join(f"{b:02X}" for b in frame['data'])
                    frame_type = "RTR" if frame['remote'] else "DATA"
                    print(f"📥 STD ID=0x{frame['id']:X} {frame_type} DLC={frame['dlc']} Data={data_str}")
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("\n退出")
        finally:
            self.spi.close()

if __name__ == '__main__':
    tester = MCP2515RecvTest(spi_bus=0, spi_device=0, spi_speed=1000000)
    tester.run()