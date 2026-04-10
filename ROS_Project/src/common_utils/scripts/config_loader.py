#!/usr/bin/env python3
import rospy
from common_utils.config_loader import ConfigLoader

rospy.init_node('test_config_loader')
loader = ConfigLoader()
print('Available configs:', list(loader.configs.keys()))