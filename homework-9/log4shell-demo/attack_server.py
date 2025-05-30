#!/usr/bin/env python3
"""
Simple LDAP Attack Server for Log4Shell Demo
Shows when vulnerable Log4j makes JNDI connections
"""

import socket
import threading
import time
from datetime import datetime

class SimpleLDAPServer:
    def __init__(self, port=1389):
        self.port = port
        self.connections = 0
        self.running = True
        
    def start(self):
        """Start the LDAP server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(('0.0.0.0', self.port))
            self.sock.listen(5)
            
            print(f"LDAP Attack Server started on port {self.port}")
            print("Waiting for Log4Shell connections...")
            print("-" * 40)
            
            while self.running:
                try:
                    client, addr = self.sock.accept()
                    self.connections += 1
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] CONNECTION #{self.connections}")
                    print(f"Source: {addr[0]}:{addr[1]}")
                    print(f"EXPLOIT SUCCESS! Log4j made JNDI connection")
                    print("-" * 40)
                    
                    # Close connection quickly
                    client.close()
                    
                except socket.error:
                    if self.running:
                        print("Socket error")
                    break
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            try:
                self.sock.close()
            except:
                pass
                
    def stop(self):
        """Stop the server"""
        self.running = False
        try:
            self.sock.close()
        except:
            pass

if __name__ == "__main__":
    server = SimpleLDAPServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        print(f"Total connections received: {server.connections}")
        print("Server stopped.")