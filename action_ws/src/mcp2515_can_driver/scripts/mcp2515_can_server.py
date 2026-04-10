#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
import spidev
import threading
import time
try:
    import Jetson.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    try:
        import RPi.GPIO as GPIO
        HAS_GPIO = True
    except ImportError:
        HAS_GPIO = False
        rospy.logwarn("无法导入 GPIO 库，将使用轮询模式")
from mcp2515_can_driver.msg import (
    MCP2515CANCommAction,
    MCP2515CANCommFeedback,
    MCP2515CANCommResult
)

# SPI 指令
MCP2515_SPI_INST = {
    'RESET': 0xC0,
    'READ': 0x03,
    'WRITE': 0x02,
    'RTS_0': 0x81,
    'READ_STATUS': 0xA0,
    'RX_STATUS': 0xB0,
    'BIT_MODIFY': 0x05,
}

# 寄存器地址
MCP2515_REG = {
    'CANSTAT': 0x0E,
    'CANCTRL': 0x0F,
    'CNF3': 0x28,
    'CNF2': 0x29,
    'CNF1': 0x2A,
    'CANINTE': 0x2B,
    'CANINTF': 0x2C,
    'EFLG': 0x2D,
    'TXB0CTRL': 0x30,
    'TXB0SIDH': 0x31,
    'TXB0SIDL': 0x32,
    'TXB0EID8': 0x33,
    'TXB0EID0': 0x34,
    'TXB0DLC': 0x35,
    'TXB0D0': 0x36,
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

# 8MHz 晶振，正确波特率配置
BAUD_RATE_CONFIG = {
    125000: (0x03, 0x90, 0x02),
    250000: (0x01, 0x90, 0x02),
    500000: (0x00, 0x90, 0x02),
    1000000: (0x00, 0x80, 0x01),
}

class MCP2515CANDriver:
    MCP2515_INT_PIN = 5

    def __init__(self, spi_bus=0, spi_device=0, bitrate=500000):
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.bitrate = bitrate
        self.spi = None
        self.connected = False
        self.lock = threading.Lock()
        self.int_pin = self.MCP2515_INT_PIN
        self.gpio_initialized = False

        if HAS_GPIO:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.int_pin, GPIO.IN)
                self.gpio_initialized = True
                rospy.loginfo(f"✅ GPIO {self.int_pin} 已配置为中断输入")
            except Exception as e:
                rospy.logwarn(f"GPIO 配置失败: {e}")
                self.gpio_initialized = False
        else:
            rospy.logwarn("GPIO 库不可用，使用轮询模式")

    def connect(self):
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.spi_bus, self.spi_device)
            self.spi.max_speed_hz = 1000000   # 1MHz 足够稳定
            self.spi.mode = 0b00
            self.spi.bits_per_word = 8
            self.connected = True
            rospy.loginfo(f"SPI 连接成功: /dev/spidev{self.spi_bus}.{self.spi_device} @ 1MHz")
            return True
        except Exception as e:
            rospy.logerr(f"SPI 连接失败: {e}")
            return False

    def disconnect(self):
        if self.spi:
            self.spi.close()
            self.spi = None
        self.connected = False

    def spi_transfer(self, data):
        if not self.connected:
            return None
        with self.lock:
            try:
                return self.spi.xfer2(data)
            except Exception as e:
                rospy.logerr(f"SPI 传输错误: {e}")
                return None

    def reset(self):
        self.spi_transfer([0xC0])
        time.sleep(0.5)

    def read_register(self, addr):
        cmd = [0x03, addr, 0x00]
        res = self.spi_transfer(cmd)
        return res[2] if res and len(res) >= 3 else None

    def write_register(self, addr, value):
        self.spi_transfer([0x02, addr, value])

    def bit_modify(self, addr, mask, value):
        self.spi_transfer([0x05, addr, mask, value])

    def set_mode(self, mode):
        # mode: 0x00 normal, 0x04 config, 0x02 loopback, etc.
        self.write_register(MCP2515_REG['CANCTRL'], mode)
        time.sleep(0.01)
        stat = self.read_register(MCP2515_REG['CANSTAT'])
        if stat is not None:
            current_mode = (stat >> 5) & 0x07
            return current_mode == (mode >> 5)
        return False

    def initialize(self):
        if not self.connected:
            return False
        rospy.loginfo("初始化 MCP2515 (8MHz晶振)...")
        self.reset()
        time.sleep(0.5)

        # 进入配置模式
        self.write_register(MCP2515_REG['CANCTRL'], 0x80)
        time.sleep(0.1)
        if self.read_register(MCP2515_REG['CANCTRL']) != 0x80:
            rospy.logerr("进入配置模式失败")
            return False

        # 配置波特率
        cfg = BAUD_RATE_CONFIG.get(self.bitrate, BAUD_RATE_CONFIG[500000])
        self.write_register(MCP2515_REG['CNF1'], cfg[0])
        self.write_register(MCP2515_REG['CNF2'], cfg[1])
        self.write_register(MCP2515_REG['CNF3'], cfg[2])
        # 验证写入
        v1 = self.read_register(MCP2515_REG['CNF1'])
        v2 = self.read_register(MCP2515_REG['CNF2'])
        v3 = self.read_register(MCP2515_REG['CNF3'])
        if v2 != cfg[1]:
            rospy.logerr(f"CNF2 写入失败: 期望 0x{cfg[1]:02X}, 实际 0x{v2:02X}")
            return False
        rospy.loginfo(f"波特率 {self.bitrate} bps 配置成功")

        # 接收所有报文（不滤波）
        self.write_register(MCP2515_REG['RXB0CTRL'], 0x60)
        self.write_register(MCP2515_REG['RXB1CTRL'], 0x60)

        # 清中断
        self.write_register(MCP2515_REG['CANINTF'], 0x00)
        # 使能接收中断（RX0IE, RX1IE）
        self.write_register(MCP2515_REG['CANINTE'], 0x03)

        # 切换到正常模式
        self.write_register(MCP2515_REG['CANCTRL'], 0x00)
        time.sleep(0.1)

        stat = self.read_register(MCP2515_REG['CANSTAT'])
        mode = (stat >> 5) & 0x07 if stat else None
        rospy.loginfo(f"初始化完成，CANSTAT=0x{stat:02X}, 模式={mode}")
        return True

    def send_can_frame(self, can_id, data, dlc, extended=False, remote=False):
        if not self.connected:
            return False, "未连接"
        if dlc > 8:
            return False, "DLC>8"

        # 只清除发送中断标志 (TX0IF)，保留接收标志
        intf = self.read_register(MCP2515_REG['CANINTF'])
        if intf is not None and (intf & 0x04):
            self.bit_modify(MCP2515_REG['CANINTF'], 0x04, 0x00)

        # 等待 TXB0 空闲
        timeout = 50
        while timeout > 0:
            ctrl = self.read_register(MCP2515_REG['TXB0CTRL'])
            if ctrl is not None and (ctrl & 0x08) == 0:
                break
            self.bit_modify(MCP2515_REG['TXB0CTRL'], 0x08, 0x00)
            time.sleep(0.001)
            timeout -= 1
        else:
            return False, "TXB0 忙碌"

        # 编码 ID
        if extended:
            if can_id > 0x1FFFFFFF:
                return False, "扩展ID超范围"
            sidh = (can_id >> 21) & 0xFF
            sidl = (((can_id >> 18) & 0x07) << 5) | 0x08 | ((can_id >> 16) & 0x03)
            eid8 = (can_id >> 8) & 0xFF
            eid0 = can_id & 0xFF
            self.write_register(MCP2515_REG['TXB0EID8'], eid8)
            self.write_register(MCP2515_REG['TXB0EID0'], eid0)
        else:
            if can_id > 0x7FF:
                return False, "标准ID超范围"
            sidh = (can_id >> 3) & 0xFF
            sidl = ((can_id & 0x07) << 5) & 0xE0
            # 扩展ID寄存器写0
            self.write_register(MCP2515_REG['TXB0EID8'], 0)
            self.write_register(MCP2515_REG['TXB0EID0'], 0)

        self.write_register(MCP2515_REG['TXB0SIDH'], sidh)
        self.write_register(MCP2515_REG['TXB0SIDL'], sidl)

        dlc_byte = dlc & 0x0F
        if remote:
            dlc_byte |= 0x40
        self.write_register(MCP2515_REG['TXB0DLC'], dlc_byte)

        for i in range(dlc):
            self.write_register(MCP2515_REG['TXB0D0'] + i, data[i])
        for i in range(dlc, 8):
            self.write_register(MCP2515_REG['TXB0D0'] + i, 0)

        # 请求发送
        self.spi_transfer([0x81])  # RTS TXB0

        # 等待发送完成 (TX0IF)
        timeout = 200  # 200ms
        while timeout > 0:
            intf = self.read_register(MCP2515_REG['CANINTF'])
            if intf is not None and (intf & 0x04):
                self.bit_modify(MCP2515_REG['CANINTF'], 0x04, 0x00)
                return True, "发送成功"
            time.sleep(0.001)
            timeout -= 1

        return False, "发送超时"

    def receive_can_frame(self):
        """从 RXB0 或 RXB1 读取一帧，仅支持标准帧（扩展帧类似可扩展）"""
        if not self.connected:
            return None

        intf = self.read_register(MCP2515_REG['CANINTF'])
        if intf is None:
            return None

        # 检查 RX0IF 和 RX1IF
        if intf & 0x01:
            buf = 0
            base = MCP2515_REG['RXB0SIDH']
            dlc_addr = MCP2515_REG['RXB0DLC']
            data_base = MCP2515_REG['RXB0D0']
        elif intf & 0x02:
            buf = 1
            base = MCP2515_REG['RXB1SIDH']
            dlc_addr = MCP2515_REG['RXB1DLC']
            data_base = MCP2515_REG['RXB1D0']
        else:
            return None

        sidh = self.read_register(base)
        sidl = self.read_register(base + 1)
        dlc_reg = self.read_register(dlc_addr)
        if None in (sidh, sidl, dlc_reg):
            return None

        dlc = dlc_reg & 0x0F
        extended = (sidl & 0x08) != 0
        remote = (dlc_reg & 0x40) != 0

        if extended:
            eid8 = self.read_register(base + 2)
            eid0 = self.read_register(base + 3)
            if eid8 is None or eid0 is None:
                return None
            # 扩展ID解码
            can_id = (sidh << 21) | (((sidl >> 5) & 0x07) << 18) | ((sidl & 0x03) << 16) | (eid8 << 8) | eid0
        else:
            can_id = ((sidl >> 5) & 0x07) | (sidh << 3)

        data = []
        for i in range(dlc):
            b = self.read_register(data_base + i)
            if b is None:
                break
            data.append(b)

        # 清除对应的接收中断标志
        self.bit_modify(MCP2515_REG['CANINTF'], 1 << buf, 0x00)
        return {
            'id': can_id,
            'dlc': dlc,
            'data': data,
            'extended': extended,
            'remote': remote
        }

    def loopback_test(self, can_id=0x123, data=[0x11,0x22,0x33,0x44], dlc=4):
        rospy.loginfo("=== 环回测试开始 ===")
        # 复位并重新初始化
        self.reset()
        time.sleep(0.1)
        self.write_register(MCP2515_REG['CANCTRL'], 0x80)
        time.sleep(0.1)
        cfg = BAUD_RATE_CONFIG.get(self.bitrate, BAUD_RATE_CONFIG[500000])
        self.write_register(MCP2515_REG['CNF1'], cfg[0])
        self.write_register(MCP2515_REG['CNF2'], cfg[1])
        self.write_register(MCP2515_REG['CNF3'], cfg[2])
        self.write_register(MCP2515_REG['RXB0CTRL'], 0x60)
        self.write_register(MCP2515_REG['CANINTF'], 0x00)
        # 进入环回模式
        self.write_register(MCP2515_REG['CANCTRL'], 0x40)
        time.sleep(0.1)
        stat = self.read_register(MCP2515_REG['CANSTAT'])
        mode = (stat >> 5) & 0x07 if stat else None
        if mode != 0x02:
            rospy.logerr(f"环回模式设置失败，模式={mode}")
            return False, "环回模式失败"

        # 清空残留帧
        while self.read_register(MCP2515_REG['CANINTF']) & 0x03:
            self.receive_can_frame()

        # 发送
        rospy.loginfo(f"发送: ID=0x{can_id:X} DLC={dlc} Data={[hex(b) for b in data]}")
        success, msg = self.send_can_frame(can_id, data, dlc, extended=False, remote=False)
        if not success:
            self.write_register(MCP2515_REG['CANCTRL'], 0x00)
            return False, msg

        # 等待接收
        for _ in range(200):
            rx = self.receive_can_frame()
            if rx:
                rospy.loginfo(f"收到: ID=0x{rx['id']:X} DLC={rx['dlc']} Data={[hex(b) for b in rx['data']]}")
                if (rx['id'] == can_id and rx['dlc'] == dlc and
                    rx['data'][:dlc] == data[:dlc]):
                    self.write_register(MCP2515_REG['CANCTRL'], 0x00)
                    return True, "环回测试成功"
                else:
                    rospy.logwarn("收到不匹配帧，继续等待")
            time.sleep(0.001)

        self.write_register(MCP2515_REG['CANCTRL'], 0x00)
        return False, "超时未收到匹配帧"

class MCP2515CANServer:
    def __init__(self):
        rospy.init_node('mp2515_can_server')
        self.spi_bus = rospy.get_param('~spi_bus', 0)
        self.spi_device = rospy.get_param('~spi_device', 0)
        self.bitrate = rospy.get_param('~bitrate', 500000)
        self.enable_rx_thread = rospy.get_param('~enable_rx_thread', True)
        self.enable_echo = rospy.get_param('~enable_echo', True)
        self.loopback_test = rospy.get_param('~loopback_test', False)

        self.driver = MCP2515CANDriver(self.spi_bus, self.spi_device, self.bitrate)
        if not self.driver.connect():
            rospy.logerr("连接失败")
            return
        if not self.driver.initialize():
            rospy.logerr("初始化失败")
            return

        self.server = actionlib.SimpleActionServer(
            'mp2515_can_comm',
            MCP2515CANCommAction,
            self.execute,
            False
        )
        self.server.start()

        self.rx_thread = None
        self.rx_thread_running = False
        if self.enable_rx_thread:
            self.start_rx_thread()

        rospy.loginfo("服务器已启动")
        if self.loopback_test:
            rospy.loginfo("运行环回测试...")
            if self.rx_thread_running:
                self.rx_thread_running = False
                self.rx_thread.join(timeout=0.5)
            success, msg = self.driver.loopback_test()
            if success:
                rospy.loginfo("✅ 环回测试通过")
            else:
                rospy.logerr(f"环回测试失败: {msg}")
            rospy.signal_shutdown("测试完成")
            return

        rospy.on_shutdown(self.cleanup)

    def start_rx_thread(self):
        self.rx_thread_running = True
        self.rx_thread = threading.Thread(target=self.rx_loop, daemon=True)
        self.rx_thread.start()
        rospy.loginfo("接收线程启动")

    def rx_loop(self):
        while self.rx_thread_running and not rospy.is_shutdown():
            frame = self.driver.receive_can_frame()
            if frame and self.enable_echo:
                data_str = ' '.join(f'{b:02X}' for b in frame['data'][:frame['dlc']])
                id_type = "EXT" if frame['extended'] else "STD"
                frame_type = "RTR" if frame['remote'] else "DATA"
                rospy.loginfo(f"📥 {id_type} ID=0x{frame['id']:X} {frame_type} DLC={frame['dlc']} Data={data_str}")
            time.sleep(0.001)

    def execute(self, goal):
        if not self.driver.connected:
            self.server.set_aborted(MCP2515CANCommResult(success=False, message="未连接"))
            return
        success, msg = self.driver.send_can_frame(
            goal.can_id, list(goal.data[:goal.dlc]), goal.dlc,
            goal.extended, goal.remote)
        result = MCP2515CANCommResult()
        result.success = success
        result.message = msg
        if success:
            self.server.set_succeeded(result)
        else:
            self.server.set_aborted(result)

    def cleanup(self):
        self.rx_thread_running = False
        if self.rx_thread:
            self.rx_thread.join(timeout=1)
        self.driver.disconnect()

if __name__ == '__main__':
    try:
        MCP2515CANServer()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass