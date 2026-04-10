#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import socket
import threading

class NetworkCommNodePython:
    def __init__(self):
        rospy.init_node('network_comm_node_python')
        
        self.server_ip = rospy.get_param('~server_ip', '0.0.0.0')
        self.server_port = rospy.get_param('~server_port', 5000)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.server_ip, self.server_port))
        self.socket.listen(5)
        rospy.loginfo(f'Server started on {self.server_ip}:{self.server_port}')
        
        rospy.Subscriber('network/tx', String, self.tx_callback)
        self.rx_pub = rospy.Publisher('network/rx', String, queue_size=10)
        
        self.connections = []
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
    
    def accept_connections(self):
        while not rospy.is_shutdown():
            try:
                conn, addr = self.socket.accept()
                rospy.loginfo(f'Connection from {addr}')
                self.connections.append(conn)
                threading.Thread(target=self.handle_client, args=(conn,)).start()
            except:
                break
    
    def handle_client(self, conn):
        while not rospy.is_shutdown():
            try:
                data = conn.recv(1024)
                if data:
                    self.rx_pub.publish(String(data=data.decode()))
            except:
                break
    
    def tx_callback(self, msg):
        for conn in self.connections[:]:
            try:
                conn.send(msg.data.encode())
            except:
                self.connections.remove(conn)
    
    def cleanup(self):
        for conn in self.connections:
            conn.close()
        self.socket.close()

if __name__ == '__main__':
    node = NetworkCommNodePython()
    rospy.spin()
    node.cleanup()