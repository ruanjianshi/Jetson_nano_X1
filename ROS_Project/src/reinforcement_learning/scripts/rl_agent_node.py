#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float32
from std_msgs.msg import Bool
import numpy as np

class RLAgentNode:
    def __init__(self):
        rospy.init_node('rl_agent_node')
        
        self.state_size = rospy.get_param('~state_size', 4)
        self.action_size = rospy.get_param('~action_size', 2)
        self.learning_rate = rospy.get_param('~learning_rate', 0.01)
        self.gamma = rospy.get_param('~gamma', 0.99)
        self.epsilon = rospy.get_param('~epsilon', 0.1)
        
        self.q_table = np.zeros((self.state_size, self.action_size))
        
        rospy.Subscriber('rl/state', Float32, self.state_callback)
        rospy.Subscriber('rl/reward', Float32, self.reward_callback)
        rospy.Subscriber('rl/done', Bool, self.done_callback)
        
        self.action_pub = rospy.Publisher('rl/action', Float32, queue_size=10)
        
        self.current_state = None
        self.current_action = None
        self.current_reward = 0
        
        rospy.loginfo('RL Agent Node started')
    
    def state_callback(self, msg):
        self.current_state = int(msg.data)
        action = self.select_action(self.current_state)
        self.current_action = action
        self.action_pub.publish(Float32(data=action))
    
    def reward_callback(self, msg):
        self.current_reward = msg.data
    
    def done_callback(self, msg):
        if msg.data and self.current_state is not None:
            self.update_q_table(self.current_state, self.current_action, self.current_reward, self.current_state, True)
    
    def select_action(self, state):
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_size)
        else:
            return np.argmax(self.q_table[state, :])
    
    def update_q_table(self, state, action, reward, next_state, done):
        if done:
            target = reward
        else:
            target = reward + self.gamma * np.max(self.q_table[next_state, :])
        
        self.q_table[state, action] += self.learning_rate * (target - self.q_table[state, action])

if __name__ == '__main__':
    node = RLAgentNode()
    rospy.spin()