#!/usr/bin/env python3
"""
Simple LAN Office Test - Send a test message
"""

import socket
import json
import time

def send_test_message(target_ip, port, message):
    """Send a test message to LAN Office instance"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(3)
        client.connect((target_ip, port))

        data = json.dumps({"type": "chat", "content": message}).encode()
        payload = json.dumps({"type": "chat", "content": message})
        client.sendall((payload + '\n').encode())
        client.close()
        return True
    except Exception as e:
        print(f"Failed to send: {e}")
        return False

def test_chat(target_ip="192.168.1.114", port=55001):
    """Test sending a chat message"""
    message = f"Test message from script at {time.strftime('%H:%M:%S')}"
    print(f"Sending test message to {target_ip}:{port}")
    success = send_test_message(target_ip, port, message)
    if success:
        print("SUCCESS: Message sent successfully")
    else:
        print("FAILED: Failed to send message")

if __name__ == "__main__":
    # Test with the detected IP
    test_chat("192.168.1.114", 55001)