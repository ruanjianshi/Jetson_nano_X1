#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
========================================
IMU Serial Action Server
========================================
功能说明:
  - 实现 ROS Action 接口，控制九轴IMU通过串口通信
  - 支持单次/连续读取传感器数据
  - 支持IMU校准（陀螺仪、加速度计、磁力计、温度）
  - 支持设置融合算法（六轴/九轴）
  - 支持设置采样频率
  - 输出加速度、陀螺仪、磁力计、四元数、欧拉角、气压计数据

硬件连接:
  串口设备: /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyTHS1, /dev/ttyAMA0
  波特率: 115200

依赖库:
  - YbImuLib: /home/jetson/Desktop/Jetson_Nano/action_ws/YbImuLib

使用方法:
  source devel/setup.bash
  rosrun yb_imu_driver imu_serial_server.py

作者: Jetson Nano
日期: 2026-04-03
"""

import rospy
import actionlib
import time
import threading
from YbImuLib import YbImuSerial
from yb_imu_driver.msg import IMUSerialAction, IMUSerialFeedback, IMUSerialResult
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3


class IMUSerialServer:
    """
    IMU Serial Action Server 类
    
    职责:
      1. 初始化 ROS 节点和 YbImuSerial
      2. 创建 Action Server 接收客户端请求
      3. 执行各种IMU操作（读取、校准、配置）
      4. 实时发布IMU数据到Topic
      5. 返回操作结果和传感器数据给客户端
    """
    
    def __init__(self):
        """
        构造函数 - 初始化服务器
        """
        rospy.init_node('imu_serial_server')
        rospy.loginfo("正在初始化 IMU Serial Action Server...")
        
        self.serial_port = rospy.get_param('~serial_port', '/dev/ttyUSB0')
        self.report_rate = rospy.get_param('~report_rate', 50)
        self.debug = rospy.get_param('~debug', False)
        self.publish_topic = rospy.get_param('~publish_topic', True)
        self.realtime_publish_rate = rospy.get_param('~realtime_publish_rate', 50.0)
        self.frame_id = rospy.get_param('~frame_id', 'imu_link')
        
        self.imu = None
        self.connected = False
        self.publishing_thread = None
        self.stop_publishing = False
        
        self.init_imu()
        self.init_publishers()
        
        self.server = actionlib.SimpleActionServer(
            'imu_serial',
            IMUSerialAction,
            self.execute,
            False
        )
        
        self.server.start()
        
        rospy.loginfo(f"✅ IMU Serial Action Server 已启动")
        rospy.loginfo(f"   串口: {self.serial_port}")
        rospy.loginfo(f"   采样频率: {self.report_rate} Hz")
        rospy.loginfo(f"   Action名称: imu_serial")
        rospy.loginfo(f"   实时Topic发布: {'启用' if self.publish_topic else '禁用'}")
        if self.publish_topic:
            rospy.loginfo(f"   Topic: /imu_serial/data, /imu_serial/mag, /imu_serial/temperature")
    
    def init_imu(self):
        """
        初始化IMU设备
        """
        try:
            self.imu = YbImuSerial(port=self.serial_port, debug=self.debug)
            
            self.imu.create_receive_threading()
            
            time.sleep(0.1)
            
            version = self.imu.get_version()
            if version:
                rospy.loginfo(f"✅ IMU固件版本: {version}")
                rospy.set_param('~imu_version', version)
            else:
                rospy.logwarn('⚠️  无法获取IMU固件版本')
            
            self.imu.set_report_rate(self.report_rate)
            rospy.loginfo(f"✅ 已设置采样频率为{self.report_rate} Hz")
            
            self.connected = True
            rospy.loginfo(f"✅ IMU已成功连接")
            
        except Exception as e:
            self.connected = False
            rospy.logerr(f'❌ IMU初始化失败: {e}')
            raise
    
    def init_publishers(self):
        """
        初始化Topic发布器
        """
        if self.publish_topic:
            self.imu_pub = rospy.Publisher('/imu_serial/data', Imu, queue_size=10)
            self.mag_pub = rospy.Publisher('/imu_serial/mag', Vector3, queue_size=10)
            self.temp_pub = rospy.Publisher('/imu_serial/temperature', Vector3, queue_size=10)
            self.publish_rate_obj = rospy.Rate(self.realtime_publish_rate)
            
            self.publishing_thread = threading.Thread(target=self.publish_imu_loop, daemon=True)
            self.publishing_thread.start()
            
            rospy.loginfo(f"✅ 实时Topic发布器已启动, 频率: {self.realtime_publish_rate} Hz")
    
    def publish_imu_loop(self):
        """
        实时发布IMU数据的线程函数
        """
        while not rospy.is_shutdown() and not self.stop_publishing:
            try:
                accel = self.imu.get_accelerometer_data()
                gyro = self.imu.get_gyroscope_data()
                mag = self.imu.get_magnetometer_data()
                quat = self.imu.get_imu_quaternion_data()
                euler = self.imu.get_imu_attitude_data(ToAngle=False)
                baro = self.imu.get_baro_data()
                
                imu_msg = Imu()
                imu_msg.header.stamp = rospy.Time.now()
                imu_msg.header.frame_id = self.frame_id
                
                imu_msg.orientation.w = quat[0]
                imu_msg.orientation.x = quat[1]
                imu_msg.orientation.y = quat[2]
                imu_msg.orientation.z = quat[3]
                
                imu_msg.angular_velocity.x = gyro[0]
                imu_msg.angular_velocity.y = gyro[1]
                imu_msg.angular_velocity.z = gyro[2]
                
                imu_msg.linear_acceleration.x = accel[0]
                imu_msg.linear_acceleration.y = accel[1]
                imu_msg.linear_acceleration.z = accel[2]
                
                self.imu_pub.publish(imu_msg)
                
                mag_msg = Vector3()
                mag_msg.x = mag[0]
                mag_msg.y = mag[1]
                mag_msg.z = mag[2]
                self.mag_pub.publish(mag_msg)
                
                temp_msg = Vector3()
                temp_msg.x = baro[0]
                temp_msg.y = baro[1]
                temp_msg.z = baro[2]
                self.temp_pub.publish(temp_msg)
                
            except Exception as e:
                rospy.logwarn(f'⚠️  实时发布数据失败: {e}')
            
            self.publish_rate_obj.sleep()
    
    def read_sensor_data(self):
        """
        读取所有传感器数据
        
        返回:
            dict: 包含所有传感器数据的字典
        """
        try:
            accel = self.imu.get_accelerometer_data()
            gyro = self.imu.get_gyroscope_data()
            mag = self.imu.get_magnetometer_data()
            quat = self.imu.get_imu_quaternion_data()
            euler = self.imu.get_imu_attitude_data(ToAngle=False)
            baro = self.imu.get_baro_data()
            
            return {
                'accel': accel,
                'gyro': gyro,
                'mag': mag,
                'quat': quat,
                'euler': euler,
                'baro': baro
            }
        except Exception as e:
            rospy.logerr(f'❌ 读取传感器数据失败: {e}')
            return None
    
    def execute(self, goal):
        """
        执行Goal的回调函数
        """
        if not self.connected:
            rospy.logerr('❌ IMU未连接，无法执行任务')
            result = IMUSerialResult()
            result.success = False
            result.message = "IMU未连接"
            self.server.set_aborted(result)
            return
        
        op_type = goal.operation_type
        
        rospy.loginfo(f"📥 收到Goal, 操作类型: {op_type}")
        
        if op_type == 0:
            self.execute_single_read()
        elif op_type == 1:
            self.execute_continuous_read(goal.duration)
        elif op_type == 2:
            self.execute_calibration(goal.calibration_type)
        elif op_type == 3:
            self.execute_mag_calibration()
        elif op_type == 4:
            self.execute_temperature_calibration(goal.calibration_temperature)
        elif op_type == 5:
            self.execute_set_algorithm(goal.algorithm_type)
        else:
            rospy.logerr(f'❌ 未知的操作类型: {op_type}')
            result = IMUSerialResult()
            result.success = False
            result.message = f"未知的操作类型: {op_type}"
            self.server.set_aborted(result)
    
    def execute_single_read(self):
        """
        执行单次读取
        """
        rospy.loginfo("📖 执行单次读取...")
        
        data = self.read_sensor_data()
        if data is None:
            result = IMUSerialResult()
            result.success = False
            result.message = "读取传感器数据失败"
            self.server.set_aborted(result)
            return
        
        result = IMUSerialResult()
        result.accel_x = data['accel'][0]
        result.accel_y = data['accel'][1]
        result.accel_z = data['accel'][2]
        result.gyro_x = data['gyro'][0]
        result.gyro_y = data['gyro'][1]
        result.gyro_z = data['gyro'][2]
        result.mag_x = data['mag'][0]
        result.mag_y = data['mag'][1]
        result.mag_z = data['mag'][2]
        result.quat_w = data['quat'][0]
        result.quat_x = data['quat'][1]
        result.quat_y = data['quat'][2]
        result.quat_z = data['quat'][3]
        result.roll = data['euler'][0]
        result.pitch = data['euler'][1]
        result.yaw = data['euler'][2]
        result.height = data['baro'][0]
        result.temperature = data['baro'][1]
        result.pressure = data['baro'][2]
        result.pressure_contrast = data['baro'][3]
        result.success = True
        result.message = "单次读取成功"
        
        self.server.set_succeeded(result)
        rospy.loginfo("✅ 单次读取成功")
    
    def execute_continuous_read(self, duration):
        """
        执行连续读取
        
        参数:
            duration: 连续读取时长(秒)
        """
        rospy.loginfo(f"📖 执行连续读取, 时长: {duration}秒")
        
        start_time = time.time()
        loop_rate = rospy.Rate(50)
        
        try:
            while not rospy.is_shutdown() and not self.server.is_preempt_requested():
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    break
                
                data = self.read_sensor_data()
                if data is not None:
                    feedback = IMUSerialFeedback()
                    feedback.accel_x = data['accel'][0]
                    feedback.accel_y = data['accel'][1]
                    feedback.accel_z = data['accel'][2]
                    feedback.gyro_x = data['gyro'][0]
                    feedback.gyro_y = data['gyro'][1]
                    feedback.gyro_z = data['gyro'][2]
                    feedback.mag_x = data['mag'][0]
                    feedback.mag_y = data['mag'][1]
                    feedback.mag_z = data['mag'][2]
                    feedback.quat_w = data['quat'][0]
                    feedback.quat_x = data['quat'][1]
                    feedback.quat_y = data['quat'][2]
                    feedback.quat_z = data['quat'][3]
                    feedback.roll = data['euler'][0]
                    feedback.pitch = data['euler'][1]
                    feedback.yaw = data['euler'][2]
                    feedback.progress = int((elapsed / duration) * 100)
                    feedback.status = f"正在读取... {feedback.progress}%"
                    
                    self.server.publish_feedback(feedback)
                
                loop_rate.sleep()
            
            data = self.read_sensor_data()
            if data is not None:
                result = IMUSerialResult()
                result.accel_x = data['accel'][0]
                result.accel_y = data['accel'][1]
                result.accel_z = data['accel'][2]
                result.gyro_x = data['gyro'][0]
                result.gyro_y = data['gyro'][1]
                result.gyro_z = data['gyro'][2]
                result.mag_x = data['mag'][0]
                result.mag_y = data['mag'][1]
                result.mag_z = data['mag'][2]
                result.quat_w = data['quat'][0]
                result.quat_x = data['quat'][1]
                result.quat_y = data['quat'][2]
                result.quat_z = data['quat'][3]
                result.roll = data['euler'][0]
                result.pitch = data['euler'][1]
                result.yaw = data['euler'][2]
                result.height = data['baro'][0]
                result.temperature = data['baro'][1]
                result.pressure = data['baro'][2]
                result.pressure_contrast = data['baro'][3]
                result.success = True
                result.message = "连续读取成功"
                
                self.server.set_succeeded(result)
                rospy.loginfo("✅ 连续读取成功")
            else:
                result = IMUSerialResult()
                result.success = False
                result.message = "读取传感器数据失败"
                self.server.set_aborted(result)
                
        except Exception as e:
            rospy.logerr(f'❌ 连续读取失败: {e}')
            result = IMUSerialResult()
            result.success = False
            result.message = str(e)
            self.server.set_aborted(result)
    
    def execute_calibration(self, calib_type):
        """
        执行IMU校准
        
        参数:
            calib_type: 0=自动(陀螺仪+加速度计), 1=陀螺仪, 2=加速度计
        """
        calib_names = {0: "自动(陀螺仪+加速度计)", 1: "陀螺仪", 2: "加速度计"}
        rospy.loginfo(f"🔧 执行IMU校准, 类型: {calib_names.get(calib_type, calib_type)}")
        
        feedback = IMUSerialFeedback()
        feedback.status = "正在校准IMU..."
        feedback.progress = 0
        self.server.publish_feedback(feedback)
        
        try:
            if calib_type == 0 or calib_type == 1 or calib_type == 2:
                self.imu.calibration_imu()
                feedback.status = "校准完成"
                feedback.progress = 100
                self.server.publish_feedback(feedback)
            else:
                raise ValueError(f"未知的校准类型: {calib_type}")
            
            result = IMUSerialResult()
            result.success = True
            result.message = f"IMU校准成功: {calib_names.get(calib_type, calib_type)}"
            self.server.set_succeeded(result)
            rospy.loginfo(f"✅ {result.message}")
            
        except Exception as e:
            rospy.logerr(f'❌ IMU校准失败: {e}')
            result = IMUSerialResult()
            result.success = False
            result.message = str(e)
            self.server.set_aborted(result)
    
    def execute_mag_calibration(self):
        """
        执行磁力计校准
        """
        rospy.loginfo("🔧 执行磁力计校准...")
        
        feedback = IMUSerialFeedback()
        feedback.status = "正在校准磁力计..."
        feedback.progress = 0
        self.server.publish_feedback(feedback)
        
        try:
            self.imu.calibration_mag()
            
            feedback.status = "校准完成"
            feedback.progress = 100
            self.server.publish_feedback(feedback)
            
            result = IMUSerialResult()
            result.success = True
            result.message = "磁力计校准成功"
            self.server.set_succeeded(result)
            rospy.loginfo("✅ 磁力计校准成功")
            
        except Exception as e:
            rospy.logerr(f'❌ 磁力计校准失败: {e}')
            result = IMUSerialResult()
            result.success = False
            result.message = str(e)
            self.server.set_aborted(result)
    
    def execute_temperature_calibration(self, temperature):
        """
        执行温度校准
        
        参数:
            temperature: 校准温度值
        """
        rospy.loginfo(f"🔧 执行温度校准, 温度: {temperature}°C")
        
        feedback = IMUSerialFeedback()
        feedback.status = "正在校准温度..."
        feedback.progress = 0
        self.server.publish_feedback(feedback)
        
        try:
            self.imu.calibration_temperature(temperature)
            
            feedback.status = "校准完成"
            feedback.progress = 100
            self.server.publish_feedback(feedback)
            
            result = IMUSerialResult()
            result.success = True
            result.message = f"温度校准成功: {temperature}°C"
            self.server.set_succeeded(result)
            rospy.loginfo(f"✅ 温度校准成功: {temperature}°C")
            
        except Exception as e:
            rospy.logerr(f'❌ 温度校准失败: {e}')
            result = IMUSerialResult()
            result.success = False
            result.message = str(e)
            self.server.set_aborted(result)
    
    def execute_set_algorithm(self, algo_type):
        """
        设置融合算法
        
        参数:
            algo_type: 6或9
        """
        algo_names = {6: "六轴", 9: "九轴"}
        rospy.loginfo(f"⚙️  设置融合算法为{algo_names.get(algo_type, algo_type)}算法")
        
        feedback = IMUSerialFeedback()
        feedback.status = "正在设置融合算法..."
        feedback.progress = 0
        self.server.publish_feedback(feedback)
        
        try:
            self.imu.set_algo_type(algo_type)
            
            feedback.status = "设置完成"
            feedback.progress = 100
            self.server.publish_feedback(feedback)
            
            result = IMUSerialResult()
            result.success = True
            result.message = f"融合算法已设置为{algo_names.get(algo_type, algo_type)}"
            self.server.set_succeeded(result)
            rospy.loginfo(f"✅ {result.message}")
            
        except Exception as e:
            rospy.logerr(f'❌ 设置融合算法失败: {e}')
            result = IMUSerialResult()
            result.success = False
            result.message = str(e)
            self.server.set_aborted(result)


if __name__ == '__main__':
    server = None
    try:
        server = IMUSerialServer()
        rospy.loginfo("🔄 Action Server 正在运行，等待 Goal 请求...")
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo('📛 收到中断信号，正在关闭...')
    except Exception as e:
        rospy.logerr(f'❌ 节点运行错误: {e}')
    finally:
        if server:
            server.stop_publishing = True