#!/usr/bin/env python3
import rospy
from std_msgs.msg import Int32, Bool
import time
from gpio_control.srv import GPIOControl, GPIOControlResponse

class GPIOControlServiceClient:
    def __init__(self):
        rospy.init_node('gpio_service_client_example')
        
        rospy.loginfo('GPIO Service Client Example Node started')
        
        # 等待服务可用
        rospy.wait_for_service('gpio_control')
        
        # 创建服务客户端
        self.control_service = rospy.ServiceProxy('gpio_control', GPIOControl)
        
        # 执行服务调用测试
        self.test_gpio_control_service()
    
    def test_gpio_control_service(self):
        """测试GPIO控制服务"""
        gpio_pins = [21, 22, 23, 24]
        
        rospy.loginfo('Testing GPIO control service...')
        
        for pin in gpio_pins:
            # 测试设置为高电平
            try:
                response = self.control_service(pin, True)
                if response.success:
                    rospy.loginfo(f'GPIO {pin} set to HIGH: {response.message}')
                else:
                    rospy.logwarn(f'Failed to set GPIO {pin}: {response.message}')
            except rospy.ServiceException as e:
                rospy.logerr(f'Service call failed: {e}')
            
            time.sleep(0.5)
            
            # 测试设置为低电平
            try:
                response = self.control_service(pin, False)
                if response.success:
                    rospy.loginfo(f'GPIO {pin} set to LOW: {response.message}')
                else:
                    rospy.logwarn(f'Failed to set GPIO {pin}: {response.message}')
            except rospy.ServiceException as e:
                rospy.logerr(f'Service call failed: {e}')
            
            time.sleep(0.5)
        
        rospy.loginfo('GPIO control service test completed')

if __name__ == '__main__':
    try:
        client = GPIOControlServiceClient()
    except rospy.ROSInterruptException:
        pass