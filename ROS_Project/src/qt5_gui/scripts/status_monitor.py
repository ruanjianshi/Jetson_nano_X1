#!/usr/bin/env python3
import rospy
from std_msgs.msg import String, Int32
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

class StatusMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ros()
        self.setup_ui()
    
    def init_ros(self):
        rospy.init_node('status_monitor', anonymous=True)
        
        rospy.Subscriber('gpio/read', Int32, self.gpio_callback)
        rospy.Subscriber('serial/rx', String, self.serial_callback)
        rospy.Subscriber('rl/reward', Int32, self.rl_callback)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.setLayout(layout)
        self.add_log('Status Monitor Started')
    
    def gpio_callback(self, msg):
        self.add_log(f'GPIO Status: {msg.data}')
    
    def serial_callback(self, msg):
        self.add_log(f'Serial RX: {msg.data}')
    
    def rl_callback(self, msg):
        self.add_log(f'RL Reward: {msg.data}')
    
    def add_log(self, message):
        self.log_text.append(f'[{rospy.get_time():.2f}] {message}')

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    monitor = StatusMonitor()
    monitor.show()
    sys.exit(app.exec_())