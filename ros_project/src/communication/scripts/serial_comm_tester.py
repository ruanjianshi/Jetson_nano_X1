#!/usr/bin/env python3
"""
串口通信测试脚本
用于测试串口通信节点的发送和接收功能
"""

import rospy
from std_msgs.msg import String
import sys
import time

class SerialCommTester:
    """串口通信测试类"""
    
    def __init__(self):
        rospy.init_node('serial_comm_tester')
        
        self.rx_count = 0
        self.tx_count = 0
        self.running = True
        
        # 订阅接收话题
        rospy.Subscriber('serial/rx', String, self.rx_callback)
        
        # 发布发送话题
        self.tx_pub = rospy.Publisher('serial/tx', String, queue_size=10)
        
        # 订阅状态话题
        rospy.Subscriber('serial/status', String, self.status_callback)
        
        rospy.loginfo('串口通信测试节点已启动')
    
    def rx_callback(self, msg):
        """接收回调函数"""
        self.rx_count += 1
        print(f"[接收 {self.rx_count}] {msg.data}")
    
    def status_callback(self, msg):
        """状态回调函数"""
        print(f"[状态] {msg.data}")
    
    def send_test_messages(self):
        """发送测试消息"""
        test_messages = [
            "Hello, Serial!",
            "Test message 1",
            "Test message 2",
            "Test message 3",
            "Ping",
            "Pong",
            "Check connection",
            "Serial communication test",
            "Data transmission",
            "End of test"
        ]
        
        rospy.loginfo(f'准备发送 {len(test_messages)} 条测试消息...')
        
        for i, msg in enumerate(test_messages, 1):
            self.tx_pub.publish(String(data=msg))
            self.tx_count += 1
            print(f"[发送 {i}/{len(test_messages)}] {msg}")
            time.sleep(0.5)
    
    def interactive_mode(self):
        """交互模式"""
        rospy.loginfo('进入交互模式 (输入 "exit" 退出)')
        
        while self.running and not rospy.is_shutdown():
            try:
                user_input = input('> ')
                
                if user_input.lower() == 'exit':
                    self.running = False
                    break
                
                if user_input:
                    self.tx_pub.publish(String(data=user_input))
                    self.tx_count += 1
                    print(f"[发送] {user_input}")
                    
            except EOFError:
                self.running = False
                break
            except KeyboardInterrupt:
                self.running = False
                break
    
    def loopback_test(self):
        """回环测试（需要硬件支持）"""
        rospy.loginfo('开始回环测试...')
        
        for i in range(10):
            test_msg = f"Loopback test {i+1}"
            self.tx_pub.publish(String(data=test_msg))
            self.tx_count += 1
            print(f"[发送] {test_msg}")
            time.sleep(0.2)
        
        rospy.loginfo('回环测试完成')
    
    def print_summary(self):
        """打印测试摘要"""
        print('\n' + '='*50)
        print('测试摘要')
        print('='*50)
        print(f'发送消息数: {self.tx_count}')
        print(f'接收消息数: {self.rx_count}')
        print('='*50)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print('用法: python3 serial_comm_tester.py [模式]')
        print('模式:')
        print('  test   - 自动测试模式')
        print('  loop   - 回环测试模式')
        print('  interactive - 交互模式')
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    tester = SerialCommTester()
    
    rospy.sleep(1)  # 等待连接
    
    try:
        if mode == 'test':
            tester.send_test_messages()
            rospy.sleep(2)  # 等待接收
        elif mode == 'loop':
            tester.loopback_test()
            rospy.sleep(2)  # 等待接收
        elif mode == 'interactive':
            tester.interactive_mode()
        else:
            rospy.logerr(f'未知的模式: {mode}')
            sys.exit(1)
        
        tester.print_summary()
        
    except rospy.ROSInterruptException:
        rospy.loginfo('收到中断信号')
    finally:
        tester.running = False

if __name__ == '__main__':
    main()