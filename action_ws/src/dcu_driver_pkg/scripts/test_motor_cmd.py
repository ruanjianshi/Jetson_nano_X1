#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from dcu_driver_pkg.msg import MotorCommand


def send_cmd(motor_id, cmd, mode=0, pos=0.0, vel=0.0, tau=0.0, kp=0.0, kd=0.0):
    pub = rospy.Publisher('/motor/command', MotorCommand, queue_size=1)
    msg = MotorCommand()
    msg.motor_id = motor_id
    msg.cmd = cmd
    msg.mode = mode
    msg.pos = pos
    msg.vel = vel
    msg.tau = tau
    msg.kp = kp
    msg.kd = kd
    pub.publish(msg)


if __name__ == '__main__':
    import sys
    rospy.init_node('motor_cmd', anonymous=True)
    
    if len(sys.argv) < 3:
        print("Usage: python3 test_motor_cmd.py <motor_id> <cmd> [mode] [pos] [vel] [tau] [kp] [kd]")
        print("cmd: 1=enable, 2=disable, 3=set_mode, 4=MIT")
        sys.exit(1)
    
    motor_id = int(sys.argv[1])
    cmd = int(sys.argv[2])
    mode = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    pos = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    vel = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    tau = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
    kp = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0
    kd = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0
    
    send_cmd(motor_id, cmd, mode, pos, vel, tau, kp, kd)
