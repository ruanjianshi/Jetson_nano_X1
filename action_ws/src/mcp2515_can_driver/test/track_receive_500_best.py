#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import spidev
import time

# SPI 指令
CMD_RESET = 0xC0
CMD_READ = 0x03
CMD_WRITE = 0x02

# 寄存器地址
REG = {
    'CANSTAT': 0x0E,
    'CANCTRL': 0x0F,
    'CNF3': 0x28,
    'CNF2': 0x29,
    'CNF1': 0x2A,
    'CANINTE': 0x2B,
    'CANINTF': 0x2C,
    'EFLG': 0x2D,
    'RXB0CTRL': 0x60,
    'RXB0SIDH': 0x61,
    'RXB0SIDL': 0x62,
    'RXB0EID8': 0x63,
    'RXB0EID0': 0x64,
    'RXB0DLC': 0x65,
    'RXB0D0': 0x66,
    'RXB1CTRL': 0x70,
    'RXB1SIDH': 0x71,
    'RXB1SIDL': 0x72,
    'RXB1EID8': 0x73,
    'RXB1EID0': 0x74,
    'RXB1DLC': 0x75,
    'RXB1D0': 0x76,
}

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

    def decode_std_id(self, sidh, sidl):
        return ((sidl >> 5) & 0x07) | (sidh << 3)

    def init_500k_75pct(self):
        """500kbps，采样点75% (8MHz晶振)"""
        self.spi.xfer2([CMD_RESET])
        time.sleep(0.5)

        # 进入配置模式
        self.write_reg(REG['CANCTRL'], 0x80)
        time.sleep(0.1)

        # 配置位定时
        self.write_reg(REG['CNF1'], 0x00)   # BRP=0, TQ=250ns
        self.write_reg(REG['CNF2'], 0x98)   # BTLMODE=1, SAM=0, PHSEG1=3 (4TQ), PRSEG=0 (1TQ)
        self.write_reg(REG['CNF3'], 0x01)   # PHSEG2=1 (2TQ)

        # # 验证写入
        # cnf2 = self.read_reg(REG['CNF2'])
        # if cnf2 != 0x90:
        #     print(f"错误: CNF2 写入失败，期望 0x98，实际 0x{cnf2:02X}")
        #     return False
        # cnf3 = self.read_reg(REG['CNF3'])
        # if cnf3 != 0x02:
        #     print(f"错误: CNF3 写入失败，期望 0x02，实际 0x{cnf3:02X}")
        #     return False

        # 接收所有报文（不滤波）
        self.write_reg(REG['RXB0CTRL'], 0x60)
        self.write_reg(REG['RXB1CTRL'], 0x60)

        # 清中断，使能接收
        self.write_reg(REG['CANINTF'], 0x00)
        self.write_reg(REG['CANINTE'], 0x03)

        # 切换到正常模式
        self.write_reg(REG['CANCTRL'], 0x00)
        time.sleep(0.1)

        print("初始化完成: 500kbps, 采样点75%")
        return True

    def receive_frame(self):
        intf = self.read_reg(REG['CANINTF'])
        if intf is None:
            return None
        if intf & 0x01:
            base = REG['RXB0SIDH']
            dlc_addr = REG['RXB0DLC']
            data_base = REG['RXB0D0']
            buf = 0
        elif intf & 0x02:
            base = REG['RXB1SIDH']
            dlc_addr = REG['RXB1DLC']
            data_base = REG['RXB1D0']
            buf = 1
        else:
            return None

        sidh = self.read_reg(base)
        sidl = self.read_reg(base + 1)
        dlc_reg = self.read_reg(dlc_addr)
        if None in (sidh, sidl, dlc_reg):
            return None

        dlc = dlc_reg & 0x0F
        extended = (sidl & 0x08) != 0
        remote = (dlc_reg & 0x40) != 0

        if extended:
            eid8 = self.read_reg(base + 2)
            eid0 = self.read_reg(base + 3)
            if eid8 is None or eid0 is None:
                return None
            can_id = ((sidl >> 5) & 0x07) | (sidh << 3)
            can_id = (can_id << 18) | ((sidl & 0x03) << 16) | (eid8 << 8) | eid0
        else:
            can_id = self.decode_std_id(sidh, sidl)

        data = []
        for i in range(dlc):
            b = self.read_reg(data_base + i)
            if b is None:
                break
            data.append(b)

        # 清除对应的接收中断标志
        self.write_reg(REG['CANINTF'], intf & ~(1 << buf))
        return {
            'id': can_id,
            'dlc': dlc,
            'data': data,
            'extended': extended,
            'remote': remote
        }

    def run(self):
        if not self.init_500k_75pct():
            return
        print("开始监听 CAN 总线 (500kbps, 采样点75%)，按 Ctrl+C 退出...")
        try:
            while True:
                frame = self.receive_frame()
                if frame:
                    data_str = ' '.join(f"{b:02X}" for b in frame['data'])
                    id_type = "EXT" if frame['extended'] else "STD"
                    frame_type = "RTR" if frame['remote'] else "DATA"
                    print(f"📥 {id_type} ID=0x{frame['id']:X} {frame_type} DLC={frame['dlc']} Data={data_str}")
                ##可选：打印错误标志
                eflg = self.read_reg(REG['EFLG'])
                if eflg != 0:
                    print(f"⚠️ EFLG=0x{eflg:02X}")
                time.sleep(0.001)
        except KeyboardInterrupt:
            print("\n退出")
        finally:
            self.spi.close()

if __name__ == '__main__':
    tester = MCP2515RecvTest(spi_bus=0, spi_device=0, spi_speed=1000000)
    tester.run()