#!/usr/bin/env python3
"""
Test LAN Office initialization without GUI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock tkinter to avoid GUI
class MockTk:
    def __init__(self):
        self.title_calls = []
        self.geometry_calls = []
        self.configure_calls = []
        self.protocol_calls = []

    def title(self, title):
        self.title_calls.append(title)
        print(f"Mock: title('{title}')")

    def geometry(self, geom):
        self.geometry_calls.append(geom)
        print(f"Mock: geometry('{geom}')")

    def configure(self, **kwargs):
        self.configure_calls.append(kwargs)
        print(f"Mock: configure({kwargs})")

    def protocol(self, protocol, callback):
        self.protocol_calls.append((protocol, callback.__name__))
        print(f"Mock: protocol('{protocol}', {callback.__name__})")

    def winfo_exists(self):
        return True

    def after(self, delay, func, *args):
        print(f"Mock: after({delay}, {func.__name__}, {args})")

    def destroy(self):
        print("Mock: destroy()")

# Import and test
try:
    import tkinter as tk
    print("SUCCESS: tkinter import successful")

    # Test basic initialization
    root = MockTk()
    print("SUCCESS: Mock root created")

    # Try importing our app using importlib
    import importlib.util
    spec = importlib.util.spec_from_file_location("lan_office", "lan_office-1.py")
    lan_office = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lan_office)
    print("SUCCESS: lan_office module loaded")

    # Get the class
    LANOfficeApp = lan_office.LANOfficeApp
    print("SUCCESS: LANOfficeApp class found")

    # Try creating app instance (without starting networking)
    app = LANOfficeApp(root)
    print("SUCCESS: LANOfficeApp instance created")

    print("\n=== Initialization Test PASSED ===")
    print("The application initializes correctly without hanging.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()