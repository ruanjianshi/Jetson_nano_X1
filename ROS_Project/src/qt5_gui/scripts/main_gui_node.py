#!/usr/bin/env python3
import rospy
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer

class MainGUINode(QMainWindow):
    def __init__(self):
        super().__init__()
        rospy.init_node('main_gui_node')
        
        self.setWindowTitle('Jetson Nano ROS Control')
        self.setGeometry(100, 100, 800, 600)
        
        self.setup_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(100)
        
        rospy.loginfo('Main GUI Node started')
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel('System Status: Ready')
        self.gpio_label = QLabel('GPIO Status: Disconnected')
        self.camera_label = QLabel('Camera Status: Offline')
        self.rl_label = QLabel('RL Status: Not training')
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.gpio_label)
        layout.addWidget(self.camera_label)
        layout.addWidget(self.rl_label)
        
        central_widget.setLayout(layout)
    
    def update_status(self):
        if not rospy.is_shutdown():
            rospy.spin_once()
            self.status_label.setText(f'System Status: Running ({rospy.get_time():.2f}s)')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainGUINode()
    window.show()
    sys.exit(app.exec_())