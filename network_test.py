#!/usr/bin/env python3
"""
LAN Office Network Test Script
Tests network connectivity and interface information
"""

import socket
import subprocess
import platform
import json

def get_all_interfaces():
    """Get information about all network interfaces"""
    interfaces = {}
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp1252')
            output = result.stdout
            current_interface = None
            for line in output.split('\n'):
                line = line.strip()
                if line and not line.startswith(' '):
                    current_interface = line.split(':')[0].strip()
                    interfaces[current_interface] = {}
                elif line.startswith('IPv4 Address') and current_interface:
                    ip = line.split(':')[1].strip()
                    interfaces[current_interface]['ipv4'] = ip
                elif line.startswith('Subnet Mask') and current_interface:
                    mask = line.split(':')[1].strip()
                    interfaces[current_interface]['mask'] = mask
        else:
            # For non-Windows systems
            import netifaces
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        if 'addr' in addr and not addr['addr'].startswith('127.'):
                            interfaces[iface] = {
                                'ipv4': addr['addr'],
                                'mask': addr.get('netmask', 'Unknown')
                            }
    except Exception as e:
        print(f"Error getting interfaces: {e}")
    return interfaces

def test_connectivity(target_ip, port):
    """Test if we can connect to a specific IP and port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((target_ip, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print("=== LAN Office Network Test ===\n")

    # Get current IP detection
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        detected_ip = s.getsockname()[0]
        s.close()
        print(f"Detected IP (via 8.8.8.8): {detected_ip}")
    except Exception as e:
        print(f"Error detecting IP: {e}")
        detected_ip = "127.0.0.1"

    # Get all interfaces
    print("\nNetwork Interfaces:")
    interfaces = get_all_interfaces()
    for name, info in interfaces.items():
        print(f"  {name}: {info.get('ipv4', 'No IP')} / {info.get('mask', 'Unknown')}")

    # Test local connectivity
    print("\nConnectivity Tests:")
    test_ports = [55000, 55001, 55002]  # Broadcast, Chat, File ports
    for port in test_ports:
        local_test = test_connectivity("127.0.0.1", port)
        print(f"  Localhost port {port}: {'OK' if local_test else 'FAIL'}")

    print("\nLAN Office Configuration:")
    print("  Broadcast Port: 55000")
    print("  Chat Port: 55001")
    print("  File Port: 55002")
    print(f"  Broadcast Address: {detected_ip.rsplit('.', 1)[0]}.255")

    print("\nRecommendations:")
    print("• Make sure both instances are on the same subnet")
    print("• Check firewall settings for ports 55000-55002")
    print("• Try different network interfaces if available")

if __name__ == "__main__":
    main()