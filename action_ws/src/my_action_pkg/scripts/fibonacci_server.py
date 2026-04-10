#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
from my_action_pkg.msg import FibonacciAction, FibonacciFeedback, FibonacciResult

class FibonacciServer:
    def __init__(self):
        # 从参数服务器读取配置（私有命名空间 ~）
        # 默认延迟为 1.0 秒，可以通过 rosparam set /fibonacci_server/delay 2.0 修改
        self.delay = rospy.get_param('~delay', 1.0)
        # 默认 order 值（当 goal 中 order <= 0 时使用）
        self.default_order = rospy.get_param('~default_order', 5)
        rospy.loginfo(f"Server config: delay={self.delay}, default_order={self.default_order}")

        self.server = actionlib.SimpleActionServer(
            'fibonacci', FibonacciAction, self.execute, False)
        self.server.start()
        rospy.loginfo(f"Node name: {rospy.get_name()}")
        rospy.loginfo("Fibonacci action server started")

    def execute(self, goal):
        order = goal.order
        if order <= 0:
            order = self.default_order
            rospy.logwarn(f"Goal order <= 0, using default order: {order}")

        rospy.loginfo(f"Received goal with order: {order}")

        fib_seq = [0, 1]
        r = FibonacciResult()
        f = FibonacciFeedback()

        for i in range(1, order):
            if self.server.is_preempt_requested():
                rospy.loginfo("Preempted")
                self.server.set_preempted()
                return

            fib_seq.append(fib_seq[i] + fib_seq[i-1])
            f.partial_sequence = fib_seq
            self.server.publish_feedback(f)

            # 使用从参数服务器读取的延迟
            rospy.sleep(self.delay)

        r.sequence = fib_seq
        self.server.set_succeeded(r)

if __name__ == '__main__':
    rospy.init_node('fibonacci_server')
    server = FibonacciServer()
    rospy.spin()