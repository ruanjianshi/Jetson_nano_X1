#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float32
from std_msgs.msg import Bool
import numpy as np

class RLEnvironmentNode:
    def __init__(self):
        rospy.init_node('rl_environment_node')
        
        self.state_size = rospy.get_param('~state_size', 4)
        self.action_size = rospy.get_param('~action_size', 2)
        self.episode_length = rospy.get_param('~episode_length', 100)
        
        self.state_pub = rospy.Publisher('rl/state', Float32, queue_size=10)
        self.reward_pub = rospy.Publisher('rl/reward', Float32, queue_size=10)
        self.done_pub = rospy.Publisher('rl/done', Bool, queue_size=10)
        
        rospy.Subscriber('rl/action', Float32, self.action_callback)
        rospy.Subscriber('rl/reset', Bool, self.reset_callback)
        
        self.reset_environment()
        self.step_count = 0
        
        rospy.loginfo('RL Environment Node started')
    
    def reset_environment(self):
        self.state = np.random.randn(self.state_size)
        self.done = False
        self.episode_reward = 0
        self.step_count = 0
        rospy.loginfo('Environment reset')
    
    def action_callback(self, msg):
        if self.done:
            return
        
        action = msg.data
        self.step_environment(action)
        self.publish_state()
    
    def step_environment(self, action):
        self.state = np.clip(self.state + action, -10, 10)
        reward = -np.sum(np.abs(self.state)) + np.random.randn() * 0.1
        self.episode_reward += reward
        
        self.step_count += 1
        if self.step_count >= self.episode_length:
            self.done = True
        
        self.reward_pub.publish(Float32(data=reward))
        self.done_pub.publish(Bool(data=self.done))
    
    def reset_callback(self, msg):
        if msg.data:
            self.reset_environment()
    
    def publish_state(self):
        for i, s in enumerate(self.state):
            self.state_pub.publish(Float32(data=s))

if __name__ == '__main__':
    node = RLEnvironmentNode()
    rospy.spin()