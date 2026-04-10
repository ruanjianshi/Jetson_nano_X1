#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
CAN 通信 Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，用于通过 USB-CAN 模块发送/接收 CAN 帧
  - 支持脉塔智能 USB转CAN模块V4
  - 支持标准帧和扩展帧
  - 支持双通道 CAN (CAN0, CAN1)
  - 支持数据长度 0-8 字节
  - 支持回环模式和正常模式
  
硬件:
  脉塔智能 USB转CAN模块V4
  - USB 接口: /dev/ttyUSB0 或 /dev/ttyACM0
  - CAN 通道: CAN0, CAN1
  - 波特率: 125K/250K/500K/1000K
  
使用方法:
  source install/setup.bash
  sudo python3 scripts/can_comm_server.py
  
作者: Jetson Nano
日期: 2026-04-02
"""

import rospy
import actionlib
import can
import struct
from maita_can_comm.msg import CANCommAction, CANCommFeedback, CANCommResult


class CANCommServer:
    """
    CAN 通信 Action Server 类
    
    职责:
      1. 初始化 CAN 总线接口
      2. 创建 Action Server 接收客户端请求
      3. 发送 CAN 帧
      4. 返回发送结果
    """
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        """
        rospy.init_node('can_comm_server')
        rospy.loginfo("正在初始化 CAN 通信 Action Server...")
        
        # 从参数服务器读取配置
        # 支持的接口类型: socketcan, slcan, serial
        self.interface = rospy.get_param('~interface', 'slcan')
        self.channel = rospy.get_param('~channel', '/dev/ttyUSB0')
        self.bitrate = rospy.get_param('~bitrate', 500000)
        
        # CAN 总线对象
        self.bus = None
        self.connected = False
        
        # 初始化 CAN 总线
        self.init_can_bus()
        
        # 创建并启动 Action Server
        self.server = actionlib.SimpleActionServer(
            'can_comm',
            CANCommAction,
            self.execute,
            False
        )
        
        self.server.start()
        
        rospy.loginfo(f"✅ CAN 通信 Action Server 已启动")
        rospy.loginfo(f"   CAN 接口: {self.channel}")
        rospy.loginfo(f"   波特率: {self.bitrate} bps")
        rospy.loginfo(f"   Action 名称: can_comm")
    
    def init_can_bus(self):
        """
        初始化 CAN 总线
        """
        try:
            # 创建 CAN 总线接口
            # 脉塔智能 USB转CAN模块使用串口接口 (slcan)
            if self.interface == 'slcan':
                # 串口转CAN 接口
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface='slcan',
                    bitrate=self.bitrate
                )
            elif self.interface == 'socketcan':
                # Linux SocketCAN 接口
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface='socketcan',
                    bitrate=self.bitrate
                )
            else:
                # 其他接口类型
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface=self.interface,
                    bitrate=self.bitrate
                )
            
            self.connected = True
            rospy.loginfo(f"✅ CAN 总线已成功连接: {self.channel}")
            rospy.loginfo(f"   接口类型: {self.interface}")
            rospy.loginfo(f"   波特率: {self.bitrate} bps")
            
        except PermissionError:
            self.connected = False
            rospy.logerr(f'❌ 权限不足: 无法访问 {self.channel}')
            rospy.logerr('   提示: 请使用 sudo 运行，或将用户添加到 dialout 组')
            
        except FileNotFoundError:
            self.connected = False
            rospy.logerr(f'❌ 设备不存在: {self.channel}')
            rospy.logerr('   提示: 请检查 USB-CAN 模块是否正确连接')
            rospy.logerr('   可用的串口设备:')
            
            import os
            try:
                devices = os.listdir('/dev')
                tty_devices = [d for d in devices if d.startswith('ttyUSB') or d.startswith('ttyACM')]
                if tty_devices:
                    for dev in sorted(tty_devices):
                        rospy.logerr(f'     /dev/{dev}')
                else:
                    rospy.logerr('     无可用设备')
            except:
                pass
            
        except Exception as e:
            self.connected = False
            rospy.logerr(f'❌ CAN 总线连接失败: {e}')
            rospy.logerr('   提示: 请检查 USB-CAN 模块是否连接，或配置正确的接口')
    
    def execute(self, goal):
        """
        执行 Goal 的回调函数
        
        参数:
          goal: 客户端发送的目标，包含 CAN 帧信息
        """
        # 检查 CAN 连接状态
        if not self.connected:
            rospy.logerr('❌ CAN 未连接，无法执行任务')
            
            result = CANCommResult()
            result.success = False
            result.message = "CAN 总线未连接"
            
            self.server.set_aborted(result)
            return
        
        # 获取 CAN 帧参数
        can_id = goal.can_id
        data = list(goal.data)
        dlc = goal.dlc
        extended = goal.extended
        channel = goal.channel
        
        rospy.loginfo(f"📥 收到 Goal:")
        rospy.loginfo(f"   CAN ID: {hex(can_id)}")
        rospy.loginfo(f"   数据长度: {dlc}")
        rospy.loginfo(f"   数据: {[hex(b) for b in data]}")
        rospy.loginfo(f"   扩展帧: {extended}")
        rospy.loginfo(f"   通道: {channel}")
        
        # 验证数据长度
        if dlc < 0 or dlc > 8:
            rospy.logerr(f'❌ 无效的数据长度: {dlc}')
            result = CANCommResult()
            result.success = False
            result.message = f"数据长度必须在 0-8 范围内"
            self.server.set_aborted(result)
            return
        
        # 发送反馈
        feedback = CANCommFeedback()
        feedback.status = f"正在发送 CAN 帧 ID={hex(can_id)}"
        self.server.publish_feedback(feedback)
        
        # 发送 CAN 帧
        try:
            # 创建 CAN 消息对象
            msg = can.Message(
                arbitration_id=can_id,
                data=data[:dlc],
                is_extended_id=extended
            )
            
            # 发送消息
            self.bus.send(msg)
            
            rospy.loginfo(f"📤 CAN 帧已发送: ID={hex(can_id)}, DLC={dlc}")
            
            # 返回成功结果
            result = CANCommResult()
            result.success = True
            result.message = f"CAN 帧发送成功: ID={hex(can_id)}"
            
            self.server.set_succeeded(result)
            rospy.loginfo("✅ Goal 执行成功")
            
        except can.CanError as e:
            rospy.logerr(f'❌ CAN 发送错误: {e}')
            
            result = CANCommResult()
            result.success = False
            result.message = f"CAN 发送失败: {str(e)}"
            
            self.server.set_aborted(result)
            
        except Exception as e:
            rospy.logerr(f'❌ 未知错误: {e}')
            
            result = CANCommResult()
            result.success = False
            result.message = f"未知错误: {str(e)}"
            
            self.server.set_aborted(result)
    
    def cleanup(self):
        """清理 CAN 资源"""
        if self.bus:
            try:
                self.bus.shutdown()
                rospy.loginfo('CAN 总线已关闭')
            except Exception as e:
                rospy.logerr(f'关闭 CAN 总线时出错: {e}')


if __name__ == '__main__':
    server = None
    try:
        server = CANCommServer()
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
        
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        rospy.logerr(f'❌ 节点运行错误: {e}')
        
    finally:
        if server:
            server.cleanup()