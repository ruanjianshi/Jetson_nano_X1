#!/usr/bin/env python3
import rospy
from common_utils.logger_utils import LoggerUtils

logger = LoggerUtils('test_logger')
logger.info('Logger utilities test')
logger.warning('Warning test')
logger.error('Error test')