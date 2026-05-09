#!/usr/bin/env python3
"""
Jetson GPIO统一测试脚本
整合硬件GPIO测试和ROS GPIO测试功能
"""

import sys
import os
import time
import argparse

try:
    import Jetson.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("警告: Jetson.GPIO未安装，将跳过硬件测试")

try:
    import rospy
    from std_msgs.msg import Int32, String
    from gpio_control.srv import GPIOControl, GPIOControlResponse
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    print("警告: ROS未正确配置，将跳过ROS测试")


class GPIOHardwareTester:
    """GPIO硬件测试类"""
    
    def __init__(self):
        if not GPIO_AVAILABLE:
            return
            
        self.test_passed = 0
        self.test_failed = 0
        self.test_total = 0
        self.initialized_pins = []
        
        # 推荐的测试引脚（BOARD模式）
        self.recommended_pins = [
            18, 19, 31, 32, 33, 35, 36, 37, 38, 40
        ]
    
    def test_result(self, success, message):
        """记录测试结果"""
        self.test_total += 1
        if success:
            print(f"  ✅ {message}")
            self.test_passed += 1
        else:
            print(f"  ❌ {message}")
            self.test_failed += 1
    
    def test_gpio_mode_setup(self):
        """测试GPIO模式设置"""
        print("\n[测试 1] GPIO模式设置")
        try:
            GPIO.setmode(GPIO.BOARD)
            self.test_result(True, "BOARD模式设置成功")
        except Exception as e:
            self.test_result(False, f"模式设置失败: {e}")
    
    def test_gpio_initialization(self):
        """测试GPIO初始化"""
        print("\n[测试 2] GPIO引脚初始化")
        
        for pin in self.recommended_pins:
            try:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                self.initialized_pins.append(pin)
                self.test_result(True, f"GPIO {pin} 初始化成功")
            except Exception as e:
                self.test_result(False, f"GPIO {pin} 初始化失败: {e}")
    
    def test_gpio_output(self):
        """测试GPIO输出功能"""
        print("\n[测试 3] GPIO输出功能")
        
        if not self.initialized_pins:
            self.test_result(False, "没有可用的GPIO引脚")
            return
        
        test_pin = self.initialized_pins[0]
        try:
            GPIO.output(test_pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(test_pin, GPIO.LOW)
            self.test_result(True, f"GPIO {test_pin} 输出测试成功")
        except Exception as e:
            self.test_result(False, f"输出测试失败: {e}")
    
    def test_gpio_pulse(self):
        """测试GPIO脉冲功能"""
        print("\n[测试 4] GPIO脉冲功能")
        
        if not self.initialized_pins:
            self.test_result(False, "没有可用的GPIO引脚")
            return
        
        test_pin = self.initialized_pins[0]
        try:
            for i in range(5):
                GPIO.output(test_pin, GPIO.HIGH)
                time.sleep(0.05)
                GPIO.output(test_pin, GPIO.LOW)
                time.sleep(0.05)
            self.test_result(True, f"GPIO {test_pin} 脉冲测试成功 (5个脉冲)")
        except Exception as e:
            self.test_result(False, f"脉冲测试失败: {e}")
    
    def test_gpio_input(self):
        """测试GPIO输入功能"""
        print("\n[测试 5] GPIO输入功能")
        
        if not self.initialized_pins:
            self.test_result(False, "没有可用的GPIO引脚")
            return
        
        test_pin = self.initialized_pins[0]
        try:
            GPIO.setup(test_pin, GPIO.IN)
            time.sleep(0.1)
            state = GPIO.input(test_pin)
            self.test_result(True, f"GPIO {test_pin} 输入测试成功 (状态: {state})")
            
            # 恢复为输出模式
            GPIO.setup(test_pin, GPIO.OUT)
            GPIO.output(test_pin, GPIO.LOW)
        except Exception as e:
            self.test_result(False, f"输入测试失败: {e}")
    
    def test_gpio_pwm(self):
        """测试GPIO PWM功能"""
        print("\n[测试 6] GPIO PWM功能")
        
        # GPIO18和GPIO19支持PWM
        pwm_pins = [18, 19]
        available_pwm = [p for p in pwm_pins if p in self.initialized_pins]
        
        if not available_pwm:
            self.test_result(False, "没有可用的PWM引脚")
            return
        
        pwm_pin = available_pwm[0]
        try:
            GPIO.setup(pwm_pin, GPIO.OUT)
            pwm = GPIO.PWM(pwm_pin, 1000)  # 1kHz
            pwm.start(50)  # 50%占空比
            time.sleep(0.5)
            pwm.stop()
            self.test_result(True, f"GPIO {pwm_pin} PWM测试成功")
        except Exception as e:
            self.test_result(False, f"PWM测试失败: {e}")
    
    def test_gpio_multiple_pins(self):
        """测试多GPIO同时操作"""
        print("\n[测试 7] 多GPIO同时操作")
        
        if len(self.initialized_pins) < 3:
            self.test_result(False, "可用的GPIO引脚不足")
            return
        
        try:
            test_pins = self.initialized_pins[:3]
            for pin in test_pins:
                GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            for pin in test_pins:
                GPIO.output(pin, GPIO.LOW)
            self.test_result(True, f"多GPIO操作成功 (引脚: {test_pins})")
        except Exception as e:
            self.test_result(False, f"多GPIO操作失败: {e}")
    
    def cleanup(self):
        """清理GPIO资源"""
        if GPIO_AVAILABLE:
            GPIO.cleanup()
            print("\n✅ GPIO资源已清理")
    
    def run_all_tests(self):
        """运行所有硬件测试"""
        if not GPIO_AVAILABLE:
            print("\n❌ Jetson.GPIO未安装，跳过硬件测试")
            return False
        
        print("=" * 60)
        print("  Jetson GPIO 硬件测试")
        print("=" * 60)
        
        try:
            self.test_gpio_mode_setup()
            self.test_gpio_initialization()
            self.test_gpio_output()
            self.test_gpio_pulse()
            self.test_gpio_input()
            self.test_gpio_pwm()
            self.test_gpio_multiple_pins()
            
            return True
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {e}")
            return False
        finally:
            self.cleanup()
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("  硬件测试摘要")
        print("=" * 60)
        print(f"总计: {self.test_total}")
        print(f"通过: {self.test_passed}")
        print(f"失败: {self.test_failed}")
        print("=" * 60)


class ROSGPIOTester:
    """ROS GPIO测试类"""
    
    def __init__(self):
        if not ROS_AVAILABLE:
            return
            
        self.test_passed = 0
        self.test_failed = 0
        self.test_total = 0
    
    def test_result(self, success, message):
        """记录测试结果"""
        self.test_total += 1
        if success:
            print(f"  ✅ {message}")
            self.test_passed += 1
        else:
            print(f"  ❌ {message}")
            self.test_failed += 1
    
    def test_ros_topics(self):
        """测试ROS话题"""
        print("\n[测试 1] ROS话题测试")
        
        try:
            topics_to_test = [
                "/gpio/write",
                "/gpio/toggle",
                "/gpio/set_input",
                "/gpio/set_output",
                "/gpio/set_all_direction",
                "/gpio/state",
                "/gpio/status"
            ]
            
            available_topics = rospy.get_published_topics()
            topic_names = [topic[0] for topic in available_topics]
            
            for topic in topics_to_test:
                if topic in topic_names:
                    self.test_result(True, f"话题 {topic} 存在")
                else:
                    self.test_result(False, f"话题 {topic} 不存在")
            
        except Exception as e:
            self.test_result(False, f"话题测试失败: {e}")
    
    def test_topic_publish(self):
        """测试话题发布"""
        print("\n[测试 2] 话题发布测试")
        
        try:
            pub = rospy.Publisher('/gpio/write', Int32, queue_size=10)
            time.sleep(1)  # 等待发布者连接
            
            # 测试发布
            for i in range(3):
                pub.publish(Int32(data=i))
                time.sleep(0.2)
            
            self.test_result(True, "话题发布测试成功")
        except Exception as e:
            self.test_result(False, f"话题发布测试失败: {e}")
    
    def test_ros_services(self):
        """测试ROS服务"""
        print("\n[测试 3] ROS服务测试")
        
        try:
            # 等待服务
            rospy.wait_for_service('/gpio_control', timeout=5)
            self.test_result(True, "服务 /gpio_control 存在")
            
            # 测试服务调用
            try:
                gpio_service = rospy.ServiceProxy('/gpio_control', GPIOControl)
                response = gpio_service(18, True)
                
                if response.success:
                    self.test_result(True, "服务调用成功 (HIGH)")
                else:
                    self.test_result(False, f"服务调用失败: {response.message}")
                
                response = gpio_service(18, False)
                if response.success:
                    self.test_result(True, "服务调用成功 (LOW)")
                else:
                    self.test_result(False, f"服务调用失败: {response.message}")
                    
            except Exception as e:
                self.test_result(False, f"服务调用失败: {e}")
                
        except rospy.ROSException as e:
            self.test_result(False, f"服务测试失败: {e}")
    
    def run_all_tests(self):
        """运行所有ROS测试"""
        if not ROS_AVAILABLE:
            print("\n❌ ROS未正确配置，跳过ROS测试")
            return False
        
        print("\n" + "=" * 60)
        print("  ROS GPIO 测试")
        print("=" * 60)
        
        try:
            self.test_ros_topics()
            self.test_topic_publish()
            self.test_ros_services()
            return True
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {e}")
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("  ROS测试摘要")
        print("=" * 60)
        print(f"总计: {self.test_total}")
        print(f"通过: {self.test_passed}")
        print(f"失败: {self.test_failed}")
        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Jetson GPIO统一测试脚本')
    parser.add_argument('--mode', type=str, default='all',
                        choices=['all', 'hardware', 'ros'],
                        help='测试模式: all(全部), hardware(仅硬件), ros(仅ROS)')
    parser.add_argument('--timeout', type=int, default=30,
                        help='ROS测试超时时间（秒）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Jetson GPIO 统一测试套件")
    print("=" * 60)
    print(f"测试模式: {args.mode}")
    print(f"超时时间: {args.timeout}秒")
    print("=" * 60)
    
    overall_success = True
    
    # 硬件测试
    if args.mode in ['all', 'hardware']:
        hardware_tester = GPIOHardwareTester()
        hardware_tester.run_all_tests()
        hardware_tester.print_summary()
        
        if hardware_tester.test_failed > 0:
            overall_success = False
    
    # ROS测试
    if args.mode in ['all', 'ros']:
        if not ROS_AVAILABLE:
            print("\n❌ ROS未正确配置，跳过ROS测试")
        else:
            try:
                rospy.init_node('gpio_test_node', anonymous=True)
                
                # 设置超时
                start_time = time.time()
                ros_tester = ROSGPIOTester()
                ros_tester.run_all_tests()
                ros_tester.print_summary()
                
                if ros_tester.test_failed > 0:
                    overall_success = False
                    
            except rospy.ROSInterruptException:
                print("\n❌ ROS测试被中断")
                overall_success = False
            except Exception as e:
                print(f"\n❌ ROS测试失败: {e}")
                overall_success = False
    
    # 总体结果
    print("\n" + "=" * 60)
    if overall_success:
        print("🎉 所有测试通过！")
        print("=" * 60)
        return 0
    else:
        print("⚠️  部分测试失败")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())