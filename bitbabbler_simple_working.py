#!/usr/bin/env python3
"""
BitBabbler Simple Working Module - Windows Compatible

This version works with the libusb-1.0.dll in the same directory.
"""

import os
import sys
from pathlib import Path

# Setup USB environment BEFORE importing usb modules
current_dir = Path(__file__).parent.absolute()
current_path = str(current_dir)
os.environ['PATH'] = current_path + os.pathsep + os.environ.get('PATH', '')

# Now import usb modules
import usb.core
import usb.util
import usb.backend.libusb1

def test_usb_backend():
    """Test if USB backend is working."""
    try:
        backend = usb.backend.libusb1.get_backend()
        return backend is not None
    except:
        return False

def list_usb_devices():
    """List all USB devices."""
    try:
        devices = []
        for device in usb.core.find(find_all=True):
            try:
                device_info = {
                    'vendor_id': f"0x{device.idVendor:04x}",
                    'product_id': f"0x{device.idProduct:04x}",
                    'manufacturer': get_string_safe(device, device.iManufacturer),
                    'product': get_string_safe(device, device.iProduct),
                    'serial_number': get_string_safe(device, device.iSerialNumber),
                }
                devices.append(device_info)
            except Exception as e:
                print(f"Warning: Could not get info for device {device.idVendor:04x}:{device.idProduct:04x}: {e}")
        return devices
    except Exception as e:
        print(f"Error scanning USB devices: {e}")
        return []

def get_string_safe(device, index, default="Unknown"):
    """Safely get USB string descriptor."""
    try:
        if index > 0:
            return usb.util.get_string(device, index)
    except:
        pass
    return default

def main():
    print("BitBabbler Simple Working Module")
    print("=" * 40)
    
    # Test USB backend
    if not test_usb_backend():
        print("✗ USB backend not available")
        print("Make sure libusb-1.0.dll is in the same directory")
        return 1
    
    print("✓ USB backend is working!")
    
    # List USB devices
    print("\nScanning for USB devices...")
    devices = list_usb_devices()
    
    print(f"\nFound {len(devices)} USB devices:")
    for i, device in enumerate(devices):
        print(f"{i+1:2d}. VID:{device['vendor_id']} PID:{device['product_id']} - {device['manufacturer']} {device['product']}")
    
    # Look for potential BitBabbler devices
    print("\nLooking for potential BitBabbler devices...")
    bitbabbler_candidates = []
    
    for device in devices:
        # Look for devices that might be BitBabbler based on common patterns
        vid = int(device['vendor_id'], 16)
        pid = int(device['product_id'], 16)
        
        # Common patterns for hardware random number generators
        if (vid == 0x1234 and pid == 0x5678) or \
           'random' in device['product'].lower() or \
           'entropy' in device['product'].lower() or \
           'trng' in device['product'].lower():
            bitbabbler_candidates.append(device)
    
    if bitbabbler_candidates:
        print(f"Found {len(bitbabbler_candidates)} potential BitBabbler device(s):")
        for device in bitbabbler_candidates:
            print(f"  - VID:{device['vendor_id']} PID:{device['product_id']} - {device['manufacturer']} {device['product']}")
    else:
        print("No BitBabbler devices found.")
        print("\nTo use this module with a BitBabbler device:")
        print("1. Connect your BitBabbler device")
        print("2. Install the WinUSB driver using Zadig (http://zadig.akeo.ie/)")
        print("3. Update the vendor_id and product_id in the code")
        print("4. Run this script again")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
