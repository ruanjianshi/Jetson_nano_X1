#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSlider

class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ros()
        self.setup_ui()
    
    def init_ros(self):
        rospy.init_node('control_panel', anonymous=True)
        self.gpio_pub = rospy.Publisher('gpio/write', Int32, queue_size=10)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.title = QLabel('GPIO Control Panel')
        layout.addWidget(self.title)
        
        self.slider = QSlider()
        self.slider.setMinimum(0)
        self.slider.setMaximum(3)
        self.slider.valueChanged.connect(self.on_slider_change)
        layout.addWidget(self.slider)
        
        self.button = QPushButton('Send GPIO Command')
        self.button.clicked.connect(self.send_gpio_command)
        layout.addWidget(self.button)
        
        self.setLayout(layout)
    
    def on_slider_change(self, value):
        pass
    
    def send_gpio_command(self):
        pin = self.slider.value()
        self.gpio_pub.publish(Int32(data=pin))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    panel = ControlPanel()
    panel.show()
    sys.exit(app.exec_())