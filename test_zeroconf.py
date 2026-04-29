#!/usr/bin/env python3
"""
Test ZeroConf discovery for LAN Office
"""

import socket
import time
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser

class TestDiscovery:
    def __init__(self):
        self.services = {}
        self.zc = Zeroconf()

    def register_test_service(self, name, port):
        """Register a test service"""
        local_ip = socket.gethostbyname(socket.gethostname())
        info = ServiceInfo(
            "_lanoffice._tcp.local.",
            f"{name}._lanoffice._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port
        )
        self.zc.register_service(info)
        print(f"Registered test service: {name} at {local_ip}:{port}")
        return info

    def add_service(self, zc, type, name):
        """Called when service discovered"""
        info = zc.get_service_info(type, name)
        if info and info.addresses:
            ip = socket.inet_ntoa(info.addresses[0])
            service_name = name.split('.')[0]
            self.services[ip] = service_name
            print(f"Discovered service: {service_name} at {ip}:{info.port}")

    def update_service(self, zc, type, name):
        """Called when service updated"""
        # Re-discover the service
        self.add_service(zc, type, name)

    def remove_service(self, zc, type, name):
        """Called when service removed"""
        service_name = name.split('.')[0]
        for ip, name in self.services.items():
            if name == service_name:
                del self.services[ip]
                print(f"Service removed: {service_name}")
                break

    def test_discovery(self):
        """Test discovery"""
        print("Starting ZeroConf discovery test...")
        print("Press Ctrl+C to stop")

        # Start browser
        browser = ServiceBrowser(self.zc, "_lanoffice._tcp.local.", self)

        try:
            # Register a test service
            test_info = self.register_test_service("TestUser", 55001)

            # Wait for discovery
            time.sleep(10)

            print(f"\nDiscovered services: {len(self.services)}")
            for ip, name in self.services.items():
                print(f"  {name} -> {ip}")

            # Cleanup
            self.zc.unregister_service(test_info)

        except KeyboardInterrupt:
            pass
        finally:
            self.zc.close()

if __name__ == "__main__":
    test = TestDiscovery()
    test.test_discovery()