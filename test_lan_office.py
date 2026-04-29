#!/usr/bin/env python3
"""Quick test of LAN Office ZeroConf implementation"""

import importlib.util
import sys

def test_lan_office():
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("lan_office", "lan_office-1.py")
        lan_office = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lan_office)

        # Test that classes exist
        assert hasattr(lan_office, 'DiscoveryWorker'), "DiscoveryWorker class missing"
        assert hasattr(lan_office, 'LANOfficeApp'), "LANOfficeApp class missing"

        # Test ZeroConf import
        assert hasattr(lan_office, 'ServiceInfo'), "ZeroConf ServiceInfo not imported"
        assert hasattr(lan_office, 'Zeroconf'), "ZeroConf Zeroconf not imported"

        print("SUCCESS: LAN Office ZeroConf implementation loaded successfully")
        print("SUCCESS: DiscoveryWorker class available")
        print("SUCCESS: LANOfficeApp class available")
        print("SUCCESS: ZeroConf dependencies imported")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_lan_office()
    sys.exit(0 if success else 1)