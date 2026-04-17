#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import time
from std_msgs.msg import Bool, Float32

class DCUCANTestServer:
    def __init__(self):
        rospy.init_node('dcu_can_test', anonymous=True)
        
        self.ifname = rospy.get_param('~ethercat_if', 'eth0')
        self.motor_name = rospy.get_param('~motor_name', 'joint3')
        self.can_id = rospy.get_param('~can_id', 3)
        
        # Import the xyber controller
        try:
            from xyber_controller import XyberController
            self.xyber_ctrl = XyberController.GetInstance()
            rospy.loginfo("XyberController instance created")
        except Exception as e:
            rospy.logerr("Failed to create XyberController: %s", str(e))
            return
        
        self.initialized = False
        self.running = False
        
    def init_dcu(self):
        try:
            # Create DCU
            if not self.xyber_ctrl.CreateDcu("dcu1", 1):
                rospy.logerr("Failed to create DCU")
                return False
            rospy.loginfo("DCU created successfully")
            
            # Attach actuator
            from xyber_controller import ActuatorType, CtrlChannel
            if not self.xyber_ctrl.AttachActuator("dcu1", CtrlChannel.CTRL_CH1, 
                                                   ActuatorType.POWER_FLOW_R86,
                                                   self.motor_name, self.can_id):
                rospy.logerr("Failed to attach actuator")
                return False
            rospy.loginfo("Actuator attached: %s (CAN ID=%d)", self.motor_name, self.can_id)
            
            # Start EtherCAT
            if not self.xyber_ctrl.Start(self.ifname, 1000000, True):
                rospy.logerr("Failed to start EtherCAT")
                return False
            rospy.loginfo("EtherCAT started successfully")
            
            # Wait for initialization
            time.sleep(2.0)
            
            self.initialized = True
            rospy.loginfo("DCU initialization complete")
            return True
            
        except Exception as e:
            rospy.logerr("Initialization error: %s", str(e))
            return False
    
    def test_can_communication(self):
        if not self.initialized:
            rospy.logerr("DCU not initialized")
            return
        
        rospy.loginfo("=" * 50)
        rospy.loginfo("CAN Communication Test")
        rospy.loginfo("Motor: %s, CAN ID: %d", self.motor_name, self.can_id)
        rospy.loginfo("=" * 50)
        
        # Test 1: Read initial position
        rospy.loginfo("[TEST 1] Reading initial motor state...")
        pos = self.xyber_ctrl.GetPosition(self.motor_name)
        vel = self.xyber_ctrl.GetVelocity(self.motor_name)
        effort = self.xyber_ctrl.GetEffort(self.motor_name)
        state = self.xyber_ctrl.GetPowerState(self.motor_name)
        mode = self.xyber_ctrl.GetMode(self.motor_name)
        rospy.loginfo("  Position: %.3f rad", pos)
        rospy.loginfo("  Velocity: %.3f rad/s", vel)
        rospy.loginfo("  Effort: %.3f Nm", effort)
        rospy.loginfo("  State: %d, Mode: %d", state, mode)
        
        # Test 2: Set MIT Mode
        rospy.loginfo("[TEST 2] Setting MIT mode (0x0B, 0x06)...")
        if self.xyber_ctrl.SetMode(self.motor_name, 6):  # MODE_MIT = 6
            rospy.loginfo("  SetMode SUCCESS")
        else:
            rospy.logerr("  SetMode FAILED")
        time.sleep(0.5)
        
        mode = self.xyber_ctrl.GetMode(self.motor_name)
        rospy.loginfo("  Current mode after SetMode: %d", mode)
        
        # Test 3: Enable Actuator
        rospy.loginfo("[TEST 3] Sending Enable command (0x01, 0x01)...")
        for i in range(5):
            self.xyber_ctrl.EnableActuator(self.motor_name)
            rospy.loginfo("  Enable attempt %d sent", i + 1)
            time.sleep(0.1)
        time.sleep(0.5)
        
        state = self.xyber_ctrl.GetPowerState(self.motor_name)
        rospy.loginfo("  State after enable: %d", state)
        
        # Test 4: Send MIT Commands
        rospy.loginfo("[TEST 4] Sending MIT position commands...")
        rospy.loginfo("  Watch CAN analyzer for outgoing messages!")
        
        for i in range(10):
            target_pos = 0.0 if i % 2 == 0 else 3.14
            self.xyber_ctrl.SetMitCmd(self.motor_name, target_pos, 0.0, 0.0, 10.0, 1.0)
            pos = self.xyber_ctrl.GetPosition(self.motor_name)
            rospy.loginfo("  Step %d: sent pos=%.2f, read pos=%.3f", i, target_pos, pos)
            time.sleep(0.5)
        
        rospy.loginfo("=" * 50)
        rospy.loginfo("Test complete - check CAN analyzer for messages")
        rospy.loginfo("=" * 50)
    
    def run(self):
        if not self.init_dcu():
            rospy.logerr("Failed to initialize DCU")
            return
        
        self.running = True
        self.test_can_communication()
        
        # Keep running to allow continued CAN monitoring
        rate = rospy.Rate(10)
        while not rospy.is_shutdown() and self.running:
            rate.sleep()

if __name__ == '__main__':
    try:
        server = DCUCANTestServer()
        server.run()
    except rospy.ROSInterruptException:
        pass