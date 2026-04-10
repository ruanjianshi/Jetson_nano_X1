#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
串口通信 Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，接收客户端发送的数据
  - 通过串口 (/dev/ttyTHS1) 发送数据
  - 接收串口回环数据并返回给客户端
  - 支持参数配置（串口、波特率等）
  
使用方法:
  source install/setup.bash
  sudo roslaunch my_action_pkg serial_comm.launch
  
作者: Jetson Nano
日期: 2026-03-30
"""

# ==================== 导入模块 ====================
import rospy                      # ROS Python 客户端库
import actionlib                  # ROS Action 客户端/服务器库
import serial                     # Python 串口通信库
import serial.tools.list_ports    # 串口工具（端口列表）
from my_action_pkg.msg import SerialCommAction, SerialCommFeedback, SerialCommResult  # 自定义 Action 消息类型
from std_msgs.msg import String   # ROS 标准字符串消息类型


# ==================== SerialCommServer 类定义 ====================
class SerialCommServer:
    """
    串口通信 Action Server 类
    
    职责:
      1. 初始化 ROS 节点和串口连接
      2. 创建 Action Server 接收客户端请求
      3. 执行串口发送和接收操作
      4. 返回操作结果给客户端
    """
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        
        功能:
          1. 初始化 ROS 节点
          2. 从参数服务器读取配置参数
          3. 连接串口设备
          4. 创建并启动 Action Server
        """
        
        # ==================== 1. 初始化 ROS 节点 ====================
        # init_node() 创建一个 ROS 节点
        rospy.init_node('serial_comm_server')
        rospy.loginfo("正在初始化串口通信 Action Server...")
        
        # ==================== 2. 从参数服务器读取配置 ====================
        # rospy.get_param('~param_name', default_value)
        # '~' 表示私有命名空间，例如: /serial_comm_server/serial_port
        self.serial_port = rospy.get_param('~serial_port', '/dev/ttyTHS1')  # 串口设备路径，默认 /dev/ttyTHS1
        self.baud_rate = rospy.get_param('~baud_rate', 115200)              # 波特率，默认 115200 bps
        self.timeout = rospy.get_param('~timeout', 1.0)                      # 超时时间（秒），默认 1.0 秒
        self.enable_echo = rospy.get_param('~enable_echo', True)             # 是否启用日志回显，默认 True
        
        # 串口对象和状态标志
        self.ser = None        # 串口对象，初始为 None
        self.connected = False # 连接状态标志，初始为 False
        
        # ==================== 3. 连接串口设备 ====================
        # 调用连接函数建立串口连接
        self.connect_serial()
        
        # ==================== 4. 创建并启动 Action Server ====================
        # SimpleActionServer 是 ROS 提供的简化 Action Server 实现
        # 参数说明:
        #   - 'serial_comm': Action 名称，客户端需要使用相同名称连接
        #   - SerialCommAction: Action 类型（由 .action 文件生成）
        #   - self.execute: 执行回调函数，当收到 goal 时调用
        #   - False: 不自动启动，需要手动 start()
        self.server = actionlib.SimpleActionServer(
            'serial_comm', 
            SerialCommAction, 
            self.execute, 
            False
        )
        
        # 启动服务器
        self.server.start()
        
        # 打印启动成功信息
        rospy.loginfo(f"✅ 串口通信 Action Server 已启动")
        rospy.loginfo(f"   串口配置: {self.serial_port}@{self.baud_rate}bps")
        rospy.loginfo(f"   Action 名称: serial_comm")
    
    # ==================== 串口连接函数 ====================
    def connect_serial(self):
        """
        连接串口设备
        
        功能:
          1. 创建串口连接对象
          2. 设置串口参数（波特率、数据位、校验位、停止位）
          3. 清空输入/输出缓冲区
          4. 更新连接状态标志
          
        异常处理:
          - 捕获串口连接异常并记录错误日志
        """
        try:
            # 创建串口连接
            # serial.Serial() 参数说明:
            #   - port: 串口设备路径，例如 '/dev/ttyTHS1'
            #   - baudrate: 波特率，例如 115200
            #   - timeout: 读取超时时间（秒）
            #   - bytesize: 数据位数，serial.EIGHTBITS 表示 8 位
            #   - parity: 校验位，serial.PARITY_NONE 表示无校验
            #   - stopbits: 停止位，serial.STOPBITS_ONE 表示 1 位停止位
            self.ser = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,      # 8 位数据位
                parity=serial.PARITY_NONE,      # 无校验位
                stopbits=serial.STOPBITS_ONE    # 1 位停止位
            )
            
            # 检查串口是否成功打开
            if self.ser.is_open:
                # 更新连接状态
                self.connected = True
                
                # 清空输入和输出缓冲区
                # reset_input_buffer(): 丢弃接收缓冲区中的所有数据
                # reset_output_buffer(): 丢弃发送缓冲区中的所有数据
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                
                # 记录连接成功日志
                rospy.loginfo(f"✅ 串口已成功连接: {self.serial_port}")
                rospy.loginfo(f"   波特率: {self.baud_rate} bps")
            else:
                # 串口未成功打开
                rospy.logerr('❌ 串口连接失败: is_open = False')
                
        except serial.SerialException as e:
            # 捕获串口专用异常（权限错误、设备不存在等）
            self.connected = False
            rospy.logerr(f'❌ 串口连接异常: {e}')
            rospy.logerr('   提示: 请确保使用 sudo 运行，或检查 /dev/ttyTHS1 权限')
        except Exception as e:
            # 捕获其他未知异常
            self.connected = False
            rospy.logerr(f'❌ 未知错误: {e}')
    
    # ==================== Action 执行回调函数 ====================
    def execute(self, goal):
        """
        执行 Goal 的回调函数
        
        当客户端发送一个 Goal 时，Action Server 会自动调用此函数
        
        参数:
          goal: 客户端发送的目标，包含要通过串口发送的数据
                goal.data.data 是实际的字符串数据
        
        执行流程:
          1. 检查串口连接状态，未连接则尝试重连
          2. 从 goal 中获取要发送的数据
          3. 发送 Feedback 给客户端（告知正在发送的数据）
          4. 通过串口发送数据
          5. 等待并接收回环数据
          6. 返回 Result 给客户端（接收的数据 + 成功标志）
        """
        
        # ==================== 1. 检查串口连接状态 ====================
        if not self.connected:
            # 串口未连接，尝试重新连接
            rospy.logwarn('⚠️  串口未连接，正在尝试重连...')
            self.connect_serial()
        
        # 如果仍未连接，终止 Goal 并返回失败
        if not self.connected:
            rospy.logerr('❌ 串口连接失败，无法执行任务')
            
            # 创建失败结果
            result = SerialCommResult()
            result.received_data = String(data="")  # 未接收到数据
            result.success = False                  # 操作失败
            
            # set_aborted() 终止 Goal 并返回结果
            self.server.set_aborted(result)
            return  # 结束函数执行
        
        # ==================== 2. 获取要发送的数据 ====================
        # goal 是 SerialCommGoal 类型
        # goal.data 是 String 类型
        # goal.data.data 是实际的字符串数据
        data_to_send = goal.data.data
        
        rospy.loginfo(f"📥 收到 Goal: 发送数据 '{data_to_send}'")
        
        # ==================== 3. 发送 Feedback 给客户端 ====================
        # Feedback 用于向客户端报告任务执行进度
        feedback = SerialCommFeedback()
        feedback.partial_data = String(data=data_to_send)  # 正在发送的数据
        
        # publish_feedback() 发送反馈信息给客户端
        self.server.publish_feedback(feedback)
        
        if self.enable_echo:
            rospy.loginfo(f"📤 正在发送数据: '{data_to_send}'")
        
        # ==================== 4. 通过串口发送数据 ====================
        try:
            # ser.write() 发送字节数据
            # encode() 将字符串编码为字节数组（UTF-8）
            self.ser.write(data_to_send.encode('utf-8'))
            
            # ==================== 5. 等待并接收回环数据 ====================
            # rospy.sleep() 暂停执行，等待串口数据传输
            # 由于 8 号和 10 号引脚已短接，发送的数据会被接收回来
            rospy.sleep(0.3)  # 等待 300ms，确保数据传输完成
            
            # 检查串口接收缓冲区是否有数据
            # ser.in_waiting 返回接收缓冲区中等待读取的字节数
            if self.ser.in_waiting > 0:
                # ser.read() 读取指定数量的字节数据
                # 读取缓冲区中的所有数据
                received = self.ser.read(self.ser.in_waiting)
                
                # decode() 将字节数组解码为字符串
                # errors='ignore' 忽略无法解码的字节
                # strip() 去除首尾空白字符
                decoded_data = received.decode('utf-8', errors='ignore').strip()
                
                # 记录接收到的数据
                if self.enable_echo:
                    rospy.loginfo(f"📥 接收到数据: '{decoded_data}'")
                
                # ==================== 6. 返回成功结果 ====================
                result = SerialCommResult()
                result.received_data = String(data=decoded_data)  # 接收到的数据
                result.success = True                              # 操作成功
                
                # set_succeeded() 完成 Goal 并返回结果
                self.server.set_succeeded(result)
                rospy.loginfo("✅ Goal 执行成功")
                
            else:
                # 未接收到数据（回环未工作）
                rospy.logwarn('⚠️  未接收到回环数据')
                
                result = SerialCommResult()
                result.received_data = String(data="")  # 未接收到数据
                result.success = False                  # 操作失败
                
                # set_aborted() 终止 Goal 并返回失败结果
                self.server.set_aborted(result)
                
        except serial.SerialException as e:
            # 捕获串口通信异常
            rospy.logerr(f'❌ 串口通信错误: {e}')
            
            result = SerialCommResult()
            result.received_data = String(data="")
            result.success = False
            
            self.server.set_aborted(result)


# ==================== 主函数 ====================
if __name__ == '__main__':
    """
    主函数 - 程序入口
    
    功能:
      1. 创建 SerialCommServer 实例
      2. 保持节点运行，等待 Goal 请求
      3. 处理异常并优雅退出
    """
    try:
        # 创建服务器实例
        # 构造函数中会初始化 ROS 节点和串口连接
        server = SerialCommServer()
        
        # rospy.spin() 保持节点运行
        # 这是一个阻塞调用，直到节点被关闭（Ctrl+C）
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
        
    except rospy.ROSInterruptException:
        # 捕获 ROS 中断异常（Ctrl+C）
        rospy.loginfo('📛 收到中断信号，正在关闭...')
        
    except Exception as e:
        # 捕获其他异常
        rospy.logerr(f'❌ 节点运行错误: {e}')