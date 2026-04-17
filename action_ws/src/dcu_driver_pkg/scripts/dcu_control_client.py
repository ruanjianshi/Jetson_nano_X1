#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import actionlib
from dcu_driver_pkg.msg import DCUControlAction, DCUControlGoal

class DCUControlClient:
    def __init__(self):
        self.client = actionlib.SimpleActionClient('dcu_control', DCUControlAction)
        rospy.loginfo("等待DCU驱动服务...")
        if not self.client.wait_for_server(rospy.Duration(10.0)):
            rospy.logerr("等待DCU驱动服务超时!")
            return
        rospy.loginfo("已连接DCU驱动")
        
        self.joints = ["joint1", "joint2", "joint3", "joint4"]
        
    def enable_motors(self):
        rospy.loginfo("使能电机...")
        # 发送零力矩命令来使能电机
        result = self.send_command(
            joint_names=self.joints,
            positions=[0.0, 0.0, 0.0, 0.0],
            velocities=[0.0, 0.0, 0.0, 0.0],
            efforts=[0.0, 0.0, 0.0, 0.0],
            stiffness=[0.0, 0.0, 0.0, 0.0],
            damping=[0.0, 0.0, 0.0, 0.0]
        )
        return result

    def send_command(self, joint_names, positions, velocities=None, 
                     efforts=None, stiffness=None, damping=None, timeout=5.0):
        goal = DCUControlGoal()
        goal.joint_names = joint_names
        goal.positions = positions
        
        goal.velocities = velocities if velocities else [0.0] * len(positions)
        goal.efforts = efforts if efforts else [0.0] * len(positions)
        goal.stiffness = stiffness if stiffness else [0.0] * len(positions)
        goal.damping = damping if damping else [0.0] * len(positions)

        rospy.loginfo(f"发送控制命令: {len(joint_names)} 个关节")
        
        self.client.send_goal(goal)
        
        if not self.client.wait_for_result(rospy.Duration(timeout)):
            rospy.logwarn("控制命令执行超时!")
            return False
        
        result = self.client.get_result()
        if result:
            rospy.loginfo(f"执行结果: success={result.success}, message={result.message}")
        return result.success if result else False

def main():
    rospy.init_node("dcu_control_client")
    
    client = DCUControlClient()
    
    if not client.client.action_client.wait_for_server():
        rospy.logerr("无法连接到DCU驱动!")
        return
    
    # Step 1: 使能电机 (发送零力矩)
    rospy.loginfo("===== Step 1: 使能电机 =====")
    if client.enable_motors():
        rospy.loginfo("电机使能成功")
    else:
        rospy.logerr("电机使能失败")
        return
        
    rospy.sleep(1.0)
    
    # Step 2: 设置小刚度进入MIT模式
    rospy.loginfo("===== Step 2: 进入MIT模式 (低刚度) =====")
    client.send_command(
        joint_names=client.joints,
        positions=[0.0, 0.0, 0.0, 0.0],
        velocities=[0.0, 0.0, 0.0, 0.0],
        efforts=[0.0, 0.0, 0.0, 0.0],
        stiffness=[5.0, 5.0, 5.0, 5.0],  # 低刚度
        damping=[1.0, 1.0, 1.0, 1.0]
    )
    
    rospy.sleep(1.0)
    
    # Step 3: 发送位置控制命令
    rospy.loginfo("===== Step 3: 位置控制测试 =====")
    
    rospy.loginfo("移动到 0.5 rad")
    client.send_command(
        joint_names=client.joints,
        positions=[0.5, 0.5, 0.5, 0.5],
        stiffness=[50.0, 50.0, 50.0, 50.0],
        damping=[2.0, 2.0, 2.0, 2.0]
    )
    rospy.sleep(2.0)
    
    rospy.loginfo("移动到 -0.5 rad")
    client.send_command(
        joint_names=client.joints,
        positions=[-0.5, -0.5, -0.5, -0.5],
        stiffness=[50.0, 50.0, 50.0, 50.0],
        damping=[2.0, 2.0, 2.0, 2.0]
    )
    rospy.sleep(2.0)
    
    rospy.loginfo("回零")
    client.send_command(
        joint_names=client.joints,
        positions=[0.0, 0.0, 0.0, 0.0],
        stiffness=[50.0, 50.0, 50.0, 50.0],
        damping=[2.0, 2.0, 2.0, 2.0]
    )
    
    rospy.loginfo("===== 测试完成 =====")

if __name__ == "__main__":
    main()
