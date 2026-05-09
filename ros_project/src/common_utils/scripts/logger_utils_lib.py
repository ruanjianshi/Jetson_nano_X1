#!/usr/bin/env python3
import rospy
import os
from datetime import datetime

class LoggerUtils:
    def __init__(self, node_name, log_dir='logs/daily'):
        self.node_name = node_name
        self.log_dir = os.path.expanduser(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.log_file = os.path.join(
            self.log_dir,
            f'{datetime.now().strftime("%Y%m%d")}_{node_name}.log'
        )
    
    def log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f'[{timestamp}] [{level}] [{self.node_name}] {message}\n'
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        if level == 'INFO':
            rospy.loginfo(message)
        elif level == 'WARNING':
            rospy.logwarn(message)
        elif level == 'ERROR':
            rospy.logerr(message)
    
    def info(self, message):
        self.log('INFO', message)
    
    def warning(self, message):
        self.log('WARNING', message)
    
    def error(self, message):
        self.log('ERROR', message)

if __name__ == '__main__':
    import rospy
    rospy.init_node('test_logger')
    logger = LoggerUtils('test_logger')
    logger.info('Logger utilities test')
    logger.warning('Warning test')
    logger.error('Error test')