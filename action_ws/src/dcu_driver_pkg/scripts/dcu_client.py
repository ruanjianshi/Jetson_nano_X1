#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
from dcu_driver_pkg.msg import DCUControlAction, DCUControlGoal, DCUControlResult, DCUControlFeedback

class DCUClient:
    def __init__(self):
        self.client = actionlib.SimpleActionClient('dcu_control', DCUControlAction)
        rospy.loginfo("等待DCU驱动服务...")
        if not self.client.wait_for_server(rospy.Duration(10.0)):
            rospy.logerr("等待DCU驱动服务超时!")
            return
        rospy.loginfo("已连接DCU驱动")

    def send_command(self, joint_names, positions, velocities=None, 
                     efforts=None, stiffness=None, damping=None, timeout=5.0):
        goal = DCUControlGoal()
        goal.joint_names = joint_names
        goal.positions = positions
        
        if velocities:
            goal.velocities = velocities
        else:
            goal.velocities = [0.0] * len(positions)
            
        if efforts:
            goal.efforts = efforts
        else:
            goal.efforts = [0.0] * len(positions)
            
        if stiffness:
            goal.stiffness = stiffness
        else:
            goal.stiffness = [0.0] * len(positions)
            
        if damping:
            goal.damping = damping
        else:
            goal.damping = [0.0] * len(positions)

        rospy.loginfo(f"发送控制命令: {len(joint_names)} 个关节")
        
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        if not self.client.wait_for_result(rospy.Duration(timeout)):
            rospy.logwarn("控制命令执行超时!")
            return False
        
        result = self.client.get_result()
        rospy.loginfo(f"执行结果: success={result.success}, message={result.message}")
        return result.success

    def feedback_cb(self, feedback):
        rospy.loginfo_throttle(1.0, f"当前位置: {[f'{p:.3f}' for p in feedback.current_positions]}")

    def cancel(self):
        self.client.cancel_all_goals()

def main():
    rospy.init_node("dcu_client_test")
    
    client = DCUClient()
    
    joints = ["joint1", "joint2", "joint3", "joint4"]
    
    rospy.loginfo("测试1: MIT模式控制")
    client.send_command(
        joint_names=joints,
        positions=[0.0, 0.0, 0.0, 0.0],
        velocities=[0.0, 0.0, 0.0, 0.0],
        efforts=[0.0, 0.0, 0.0, 0.0],
        stiffness=[50.0, 50.0, 50.0, 50.0],
        damping=[1.0, 1.0, 1.0, 1.0]
    )
    
    rospy.sleep(1.0)
    
    rospy.loginfo("测试2: 位置控制")
    client.send_command(
        joint_names=joints,
        positions=[1.0, 0.5, -0.5, 0.0],
        stiffness=[100.0, 100.0, 100.0, 100.0],
        damping=[2.0, 2.0, 2.0, 2.0]
    )
    
    rospy.sleep(1.0)
    
    rospy.loginfo("测试3: 回零")
    client.send_command(
        joint_names=joints,
        positions=[0.0, 0.0, 0.0, 0.0]
    )
    
    rospy.loginfo("测试完成")

if __name__ == "__main__":
    main()
