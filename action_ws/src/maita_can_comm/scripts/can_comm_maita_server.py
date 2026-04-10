#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 通信 Action Server (脉塔智能 USBCAN-II)
========================================
功能说明:
  - 基于 libusbcan.so 实现 CAN 通信
  - 支持 USBCAN-I/I+ 和 USBCAN-II/II+
  - 支持 ROS Action 接口
  - 支持标准帧和扩展帧
  - 支持双通道 CAN
  
硬件:
  脉塔智能 USBCAN-II
  - Vendor ID: 0471
  - Product ID: 1200
  - 设备类型: USBCAN_II (4)
  
使用方法:
  source install/setup.bash
  sudo python3 scripts/can_comm_maita_server.py
  
作者: Jetson Nano
日期: 2026-04-02
"""

import rospy
import actionlib
import threading
import time
import os
from ctypes import *
from maita_can_comm.msg import CANCommAction, CANCommFeedback, CANCommResult

# ==================== 设备类型定义 ====================
USBCAN_I = 3   # USBCAN-I/I+
USBCAN_II = 4  # USBCAN-II/II+
MAX_CHANNELS = 2  # 最大通道数

# ==================== 波特率定义 ====================
# 波特率值可通过 "zcanpro 波特率计算器" 计算
BAUD_RATE_125K = 0x1c03  # 125K (87.5%)
BAUD_RATE_250K = 0x1c01  # 250K (87.5%)
BAUD_RATE_500K = 0x1c00  # 500K (87.5%)
BAUD_RATE_1000K = 0x1400  # 1M (75%)

BAUD_RATE_MAP = {
    125000: BAUD_RATE_125K,
    250000: BAUD_RATE_250K,
    500000: BAUD_RATE_500K,
    1000000: BAUD_RATE_1000K
}

# ==================== 数据结构定义 ====================
class ZCAN_CAN_BOARD_INFO(Structure):
    """设备信息结构体"""
    _fields_ = [
        ("hw_Version", c_ushort),
        ("fw_Version", c_ushort),
        ("dr_Version", c_ushort),
        ("in_Version", c_ushort),
        ("irq_Num", c_ushort),
        ("can_Num", c_ubyte),
        ("str_Serial_Num", c_ubyte*20),
        ("str_hw_Type", c_ubyte*40),
        ("Reserved", c_ubyte*4)
    ]

class ZCAN_CAN_INIT_CONFIG(Structure):
    """CAN 初始化配置结构体"""
    _fields_ = [
        ("AccCode", c_uint),
        ("AccMask", c_uint),
        ("Reserved", c_uint),
        ("Filter", c_ubyte),
        ("Timing0", c_ubyte),
        ("Timing1", c_ubyte),
        ("Mode", c_ubyte)
    ]

class ZCAN_CAN_OBJ(Structure):
    """CAN 帧结构体"""
    _fields_ = [
        ("ID", c_uint),
        ("TimeStamp", c_uint),
        ("TimeFlag", c_uint8),
        ("SendType", c_byte),
        ("RemoteFlag", c_byte),
        ("ExternFlag", c_byte),
        ("DataLen", c_byte),
        ("Data", c_ubyte*8),
        ("Reserved", c_ubyte*3)
    ]


class MaitaCANServer:
    """
    脉塔智能 CAN 通信 Action Server 类
    
    使用 libusbcan.so 库实现 CAN 通信
    """
    
    def __init__(self):
        """构造函数 - 初始化服务器"""
        rospy.init_node('can_comm_maita_server')
        rospy.loginfo("正在初始化脉塔智能 CAN 通信 Action Server...")
        
        # 从参数服务器读取配置
        self.device_type = rospy.get_param('~device_type', USBCAN_II)
        self.device_index = rospy.get_param('~device_index', 0)
        self.baudrate = rospy.get_param('~baudrate', 500000)
        self.enable_rx_thread = rospy.get_param('~enable_rx_thread', True)
        
        # 库路径
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.lib_path = os.path.join(pkg_dir, 'usbcan_ii_libusb_aarch64', 'libusbcan.so')
        
        # 加载库
        self.lib = None
        self.connected = False
        
        # 加载驱动库
        self.load_library()
        
        # 打开设备
        self.open_device()
        
        # 初始化 CAN 通道
        self.init_can_channels()
        
        # 创建并启动 Action Server
        self.server = actionlib.SimpleActionServer(
            'can_comm',
            CANCommAction,
            self.execute,
            False
        )
        
        self.server.start()
        
        # 启动接收线程
        self.rx_thread = None
        self.rx_thread_running = False
        if self.enable_rx_thread:
            self.start_rx_thread()
        
        rospy.loginfo("✅ 脉塔智能 CAN 通信 Action Server 已启动")
        rospy.loginfo(f"   设备类型: {self.device_type}")
        rospy.loginfo(f"   波特率: {self.baudrate} bps")
        rospy.loginfo(f"   库路径: {self.lib_path}")
        rospy.loginfo(f"   Action 名称: can_comm")
        
        # 注册清理函数
        rospy.on_shutdown(self.cleanup)
    
    def load_library(self):
        """加载 libusbcan.so 库"""
        try:
            if not os.path.exists(self.lib_path):
                rospy.logerr(f'❌ 库文件不存在: {self.lib_path}')
                return
            
            self.lib = CDLL(self.lib_path)
            rospy.loginfo(f"✅ 库加载成功: {self.lib_path}")
            
        except Exception as e:
            rospy.logerr(f'❌ 库加载失败: {e}')
    
    def open_device(self):
        """打开设备"""
        if self.lib is None:
            rospy.logerr('❌ 库未加载，无法打开设备')
            return
        
        try:
            # VCI_OpenDevice(DeviceType, DeviceInd, Reserved)
            ret = self.lib.VCI_OpenDevice(self.device_type, self.device_index, 0)
            
            if ret == 0:
                rospy.logerr('❌ 打开设备失败')
                self.connected = False
            else:
                self.connected = True
                rospy.loginfo("✅ 设备打开成功")
                
                # 读取设备信息
                self.read_device_info()
                
        except Exception as e:
            rospy.logerr(f'❌ 打开设备异常: {e}')
            self.connected = False
    
    def read_device_info(self):
        """读取设备信息"""
        try:
            info = ZCAN_CAN_BOARD_INFO()
            ret = self.lib.VCI_ReadBoardInfo(self.device_type, self.device_index, byref(info))
            
            if ret == 1:
                serial = ''.join([chr(c) for c in info.str_Serial_Num if c > 0])
                hw_type = ''.join([chr(c) for c in info.str_hw_Type if c > 0])
                
                rospy.loginfo("   设备信息:")
                rospy.loginfo(f"     序列号: {serial}")
                rospy.loginfo(f"     硬件类型: {hw_type}")
                rospy.loginfo(f"     硬件版本: {info.hw_Version}")
                rospy.loginfo(f"     固件版本: {info.fw_Version}")
                rospy.loginfo(f"     驱动版本: {info.dr_Version}")
                
        except Exception as e:
            rospy.logwarn(f'读取设备信息失败: {e}')
    
    def init_can_channels(self):
        """初始化 CAN 通道"""
        if not self.connected:
            rospy.logwarn('⚠️  设备未连接，跳过初始化')
            return
        
        # 获取波特率配置
        baud_config = BAUD_RATE_MAP.get(self.baudrate, BAUD_RATE_500K)
        
        # 初始化所有通道
        for i in range(MAX_CHANNELS):
            try:
                init_config = ZCAN_CAN_INIT_CONFIG()
                init_config.AccCode = 0
                init_config.AccMask = 0xFFFFFFFF
                init_config.Reserved = 0
                init_config.Filter = 1
                init_config.Timing0 = baud_config & 0xff
                init_config.Timing1 = baud_config >> 8
                init_config.Mode = 0
                
                # VCI_InitCAN(DeviceType, DeviceInd, CANInd, pInitConfig)
                ret = self.lib.VCI_InitCAN(self.device_type, self.device_index, i, byref(init_config))
                
                if ret == 0:
                    rospy.logerr(f'❌ 初始化 CAN {i} 失败')
                else:
                    rospy.loginfo(f"✅ 初始化 CAN {i} 成功")
                    
                    # 启动 CAN
                    ret = self.lib.VCI_StartCAN(self.device_type, self.device_index, i)
                    
                    if ret == 0:
                        rospy.logerr(f'❌ 启动 CAN {i} 失败')
                    else:
                        rospy.loginfo(f"✅ 启动 CAN {i} 成功")
                        
            except Exception as e:
                rospy.logerr(f'初始化 CAN {i} 异常: {e}')
    
    def start_rx_thread(self):
        """启动接收线程"""
        self.rx_thread_running = True
        self.rx_thread = threading.Thread(target=self.rx_thread_func, daemon=True)
        self.rx_thread.start()
        rospy.loginfo("✅ 接收线程已启动")
    
    def rx_thread_func(self):
        """接收线程函数"""
        while self.rx_thread_running and not rospy.is_shutdown():
            try:
                # 检查所有通道的接收缓冲区
                for i in range(MAX_CHANNELS):
                    count = self.lib.VCI_GetReceiveNum(self.device_type, self.device_index, i)
                    
                    if count > 0:
                        # 读取 CAN 帧
                        can_objs = (ZCAN_CAN_OBJ * count)()
                        rcount = self.lib.VCI_Receive(
                            self.device_type, 
                            self.device_index, 
                            i, 
                            byref(can_objs), 
                            count, 
                            100
                        )
                        
                        # 处理接收到的帧
                        for j in range(rcount):
                            self.process_received_frame(can_objs[j], i)
                
                time.sleep(0.01)  # 10ms 间隔
                
            except Exception as e:
                rospy.logerr(f'接收线程异常: {e}')
                time.sleep(0.1)
    
    def process_received_frame(self, can_obj, channel):
        """处理接收到的 CAN 帧"""
        try:
            # 发布到 ROS Topic（可选）
            # 这里可以添加代码将接收到的帧发布到 ROS Topic
            
            # 打印接收到的帧
            if can_obj.RemoteFlag == 0:
                data_str = ' '.join([f'{can_obj.Data[k]:02x}' for k in range(can_obj.DataLen)])
                rospy.loginfo(f"📥 CAN{channel} 接收: ID=0x{can_obj.ID:03X} Data={data_str}")
            else:
                rospy.loginfo(f"📥 CAN{channel} 接收: ID=0x{can_obj.ID:03X} Remote")
                
        except Exception as e:
            rospy.logerr(f'处理帧异常: {e}')
    
    def execute(self, goal):
        """执行 Goal 的回调函数"""
        # 检查设备连接状态
        if not self.connected:
            rospy.logerr('❌ 设备未连接，无法执行任务')
            
            result = CANCommResult()
            result.success = False
            result.message = "设备未连接"
            
            self.server.set_aborted(result)
            return
        
        # 获取 CAN 帧参数
        can_id = goal.can_id
        data = list(goal.data)
        dlc = goal.dlc
        extended = goal.extended
        channel = goal.channel
        
        # 验证通道
        if channel >= MAX_CHANNELS:
            rospy.logerr(f'❌ 无效的通道号: {channel}')
            result = CANCommResult()
            result.success = False
            result.message = f"无效的通道号: {channel}"
            self.server.set_aborted(result)
            return
        
        # 验证数据长度
        if dlc < 0 or dlc > 8:
            rospy.logerr(f'❌ 无效的数据长度: {dlc}')
            result = CANCommResult()
            result.success = False
            result.message = f"数据长度必须在 0-8 范围内"
            self.server.set_aborted(result)
            return
        
        rospy.loginfo(f"📥 收到 Goal:")
        rospy.loginfo(f"   CAN ID: {hex(can_id)}")
        rospy.loginfo(f"   数据长度: {dlc}")
        rospy.loginfo(f"   数据: {[hex(b) for b in data]}")
        rospy.loginfo(f"   扩展帧: {extended}")
        rospy.loginfo(f"   通道: {channel}")
        
        # 发送反馈
        feedback = CANCommFeedback()
        feedback.status = f"正在发送 CAN 帧 ID={hex(can_id)}"
        self.server.publish_feedback(feedback)
        
        # 构造 CAN 帧
        can_obj = ZCAN_CAN_OBJ()
        can_obj.ID = can_id
        can_obj.SendType = 0  # 正常发送
        can_obj.RemoteFlag = 0  # 数据帧
        can_obj.ExternFlag = 1 if extended else 0  # 扩展帧标志
        can_obj.DataLen = dlc
        
        # 填充数据
        for i in range(dlc):
            can_obj.Data[i] = data[i] if i < len(data) else 0
        
        # 发送 CAN 帧
        try:
            # VCI_Transmit(DeviceType, DeviceInd, CANInd, pSend, Len)
            ret = self.lib.VCI_Transmit(
                self.device_type,
                self.device_index,
                channel,
                byref(can_obj),
                1
            )
            
            if ret == 1:
                rospy.loginfo(f"📤 CAN 帧已发送: ID={hex(can_id)}, DLC={dlc}")
                
                result = CANCommResult()
                result.success = True
                result.message = f"CAN 帧发送成功: ID={hex(can_id)}"
                
                self.server.set_succeeded(result)
                rospy.loginfo("✅ Goal 执行成功")
            else:
                rospy.logerr(f'❌ CAN 帧发送失败')
                
                result = CANCommResult()
                result.success = False
                result.message = "CAN 帧发送失败"
                
                self.server.set_aborted(result)
                
        except Exception as e:
            rospy.logerr(f'❌ CAN 发送异常: {e}')
            
            result = CANCommResult()
            result.success = False
            result.message = f"CAN 发送异常: {str(e)}"
            
            self.server.set_aborted(result)
    
    def cleanup(self):
        """清理资源"""
        rospy.loginfo("正在清理资源...")
        
        # 停止接收线程
        self.rx_thread_running = False
        if self.rx_thread:
            self.rx_thread.join(timeout=2)
        
        # 复位 CAN 通道
        if self.connected:
            try:
                for i in range(MAX_CHANNELS):
                    self.lib.VCI_ResetCAN(self.device_type, self.device_index, i)
            except:
                pass
        
        # 关闭设备
        if self.connected:
            try:
                ret = self.lib.VCI_CloseDevice(self.device_type, self.device_index)
                if ret == 1:
                    rospy.loginfo("✅ 设备已关闭")
                else:
                    rospy.logwarn("⚠️  关闭设备失败")
            except Exception as e:
                rospy.logerr(f'关闭设备异常: {e}')
        
        rospy.loginfo("资源清理完成")


if __name__ == '__main__':
    try:
        server = MaitaCANServer()
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
        
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        rospy.logerr(f'❌ 节点运行错误: {e}')