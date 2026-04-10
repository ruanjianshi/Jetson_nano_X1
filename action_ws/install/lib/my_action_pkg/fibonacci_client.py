#!/usr/bin/env python3

import rospy
import actionlib
from my_action_pkg.msg import FibonacciAction, FibonacciGoal

def feedback_cb(feedback):
    rospy.loginfo(f"Feedback: {feedback.partial_sequence}")

if __name__ == '__main__':
    rospy.init_node('fibonacci_client')
    rospy.loginfo(f"Node name: {rospy.get_name()}")
    # 从参数服务器读取 order（私有命名空间 ~，或全局参数）
    order = rospy.get_param('~order', 10)
    rospy.loginfo(f"Using order from param: {order}")

    client = actionlib.SimpleActionClient('fibonacci', FibonacciAction)
    rospy.loginfo("Waiting for action server...")
    client.wait_for_server()

    goal = FibonacciGoal()
    goal.order = order

    rospy.loginfo(f"Sending goal: order={goal.order}")
    client.send_goal(goal, feedback_cb=feedback_cb)

    client.wait_for_result(rospy.Duration(10.0))
    result = client.get_result()
    rospy.loginfo(f"Result: {result.sequence}")