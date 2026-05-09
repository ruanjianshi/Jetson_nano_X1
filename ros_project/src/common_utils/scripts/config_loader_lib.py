#!/usr/bin/env python3
import rospy
import yaml
import os

class ConfigLoader:
    def __init__(self, config_dir='config'):
        self.config_dir = os.path.expanduser(config_dir)
        self.configs = {}
        self.load_configs()
    
    def load_configs(self):
        if os.path.exists(self.config_dir):
            for file in os.listdir(self.config_dir):
                if file.endswith('.yaml') or file.endswith('.yml'):
                    config_name = os.path.splitext(file)[0]
                    config_path = os.path.join(self.config_dir, file)
                    try:
                        with open(config_path, 'r') as f:
                            self.configs[config_name] = yaml.safe_load(f)
                            rospy.loginfo(f'Loaded config: {config_name}')
                    except Exception as e:
                        rospy.logerr(f'Error loading config {config_name}: {e}')
    
    def get_config(self, name, default=None):
        return self.configs.get(name, default)
    
    def get_param(self, config_name, param_name, default=None):
        config = self.get_config(config_name)
        if config:
            return config.get(param_name, default)
        return default

if __name__ == '__main__':
    rospy.init_node('test_config_loader')
    loader = ConfigLoader()
    print('Available configs:', list(loader.configs.keys()))