#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

test_commands.py - 测试脚本：发送控制命令到 Jetson

模拟 PC QT UI 发送 JSON 命令到 /pc/command topic。
不依赖 QT，可在 PC 或 Jetson 上运行，用于调试和自动化测试。

Usage:
    rosrun distributed_comm test_commands.py
    rosrun distributed_comm test_commands.py _mode:=auto
"""
#  作者: Qi Xiao
#  邮箱: 2408128687@qq.com

import rospy
from std_msgs.msg import String
import time
import json


class CommandTester:
    def __init__(self):
        rospy.init_node('test_commands', anonymous=True)
        self.mode = rospy.get_param('~mode', 'auto')  # auto | interactive
        self.pub = rospy.Publisher('/pc/command', String, queue_size=10)

        # Subscribe to telemetry for feedback
        self.tele_callback_count = 0
        self.tele_sub = rospy.Subscriber('/jetson/telemetry', String, self.tele_cb)

    def tele_cb(self, msg):
        self.tele_callback_count += 1
        try:
            data = json.loads(msg.data)
            rospy.loginfo("Telemetry #{}: CPU={}C, LED={}, Motor={}, Servo={}".format(
                self.tele_callback_count,
                data.get('cpu_temp', '?'),
                'ON' if data.get('led') else 'OFF',
                data.get('motor', '?'),
                data.get('servo', '?')))
        except (json.JSONDecodeError, ValueError):
            rospy.logwarn("Invalid telemetry: %s", msg.data[:80])

    def send_dict(self, cmd_dict):
        msg = String()
        msg.data = json.dumps(cmd_dict)
        self.pub.publish(msg)
        rospy.loginfo("Sent: %s", msg.data)

    def auto_test(self):
        """自动测试序列"""
        rospy.loginfo("=== Auto test sequence ===")
        rospy.sleep(1)

        tests = [
            {"cmd": "led_on"},
            {"cmd": "motor", "speed": 50},
            {"cmd": "servo", "angle": 45},
            {"cmd": "status"},
            {"cmd": "servo", "angle": 135},
            {"cmd": "motor", "speed": 100},
            {"cmd": "led_off"},
            {"cmd": "status"},
        ]

        for i, cmd in enumerate(tests):
            rospy.loginfo("[%d/%d] %s", i + 1, len(tests), json.dumps(cmd))
            self.send_dict(cmd)
            rospy.sleep(1.5)

        rospy.loginfo("=== Auto test complete ===")

    def run(self):
        if self.mode == 'auto':
            self.auto_test()
        else:
            rospy.loginfo("Interactive mode: type commands (JSON) or 'q' to quit")
            rospy.loginfo("Examples: led_on / led_off / status")
            rospy.loginfo("         motor 80 / servo 45")

            r = rospy.Rate(1)
            while not rospy.is_shutdown():
                # Non-blocking; user types in terminal
                try:
                    cmd_str = raw_input("cmd> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if cmd_str == 'q':
                    break
                if not cmd_str:
                    continue

                # Shortcut commands
                if cmd_str == 'led_on':
                    self.send_dict({"cmd": "led_on"})
                elif cmd_str == 'led_off':
                    self.send_dict({"cmd": "led_off"})
                elif cmd_str == 'status':
                    self.send_dict({"cmd": "status"})
                elif cmd_str.startswith('motor '):
                    self.send_dict({"cmd": "motor", "speed": int(cmd_str.split()[1])})
                elif cmd_str.startswith('servo '):
                    self.send_dict({"cmd": "servo", "angle": int(cmd_str.split()[1])})
                else:
                    try:
                        self.send_dict(json.loads(cmd_str))
                    except (json.JSONDecodeError, ValueError):
                        rospy.logerr("Invalid input: %s", cmd_str)
                r.sleep()


if __name__ == '__main__':
    try:
        CommandTester().run()
    except rospy.ROSInterruptException:
        pass
