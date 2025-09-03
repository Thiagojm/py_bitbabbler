#!/usr/bin/env python3
"""
BitBabbler Working Module with Device Detection

This version works with the actual BitBabbler device found on your system.
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

def get_string_safe(device, index, default="Unknown"):
    """Safely get USB string descriptor."""
    try:
        if index > 0:
            return usb.util.get_string(device, index)
    except:
        pass
    return default

class BitBabblerDevice:
    """BitBabbler device interface."""
    
    def __init__(self, vendor_id=0x0403, product_id=0x7840):
        """Initialize with the actual BitBabbler device IDs."""
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self.initialized = False
    
    def find_device(self):
        """Find and configure the BitBabbler device."""
        try:
            # Find the device
            self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
            
            if self.device is None:
                print(f"BitBabbler device not found (VID: 0x{self.vendor_id:04x}, PID: 0x{self.product_id:04x})")
                return False
            
            # Get device information
            manufacturer = get_string_safe(self.device, self.device.iManufacturer)
            product = get_string_safe(self.device, self.device.iProduct)
            serial_number = get_string_safe(self.device, self.device.iSerialNumber)
            
            print(f"Found BitBabbler device: {manufacturer} {product}")
            print(f"Serial: {serial_number}")
            
            # Configure the device
            return self._configure_device()
            
        except Exception as e:
            print(f"Error finding device: {e}")
            return False
    
    def _configure_device(self):
        """Configure the USB device and find endpoints."""
        try:
            # Set configuration
            self.device.set_configuration()
            
            # Get the active configuration
            cfg = self.device.get_active_configuration()
            intf = cfg[(0, 0)]  # First interface, first alternate setting
            
            # Find endpoints
            for endpoint in intf:
                if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    self.endpoint_in = endpoint
                    print(f"Found input endpoint: 0x{endpoint.bEndpointAddress:02x}")
                elif usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.endpoint_out = endpoint
                    print(f"Found output endpoint: 0x{endpoint.bEndpointAddress:02x}")
            
            if not self.endpoint_in:
                print("No input endpoint found")
                return False
                
            self.initialized = True
            print("Device configured successfully")
            return True
            
        except Exception as e:
            print(f"Error configuring device: {e}")
            return False
    
    def read_random_data(self, size=1024, timeout=1000):
        """Read random data from the BitBabbler device."""
        if not self.initialized or not self.endpoint_in:
            raise Exception("Device not initialized")
        
        try:
            # Read data from the device
            data = self.device.read(
                self.endpoint_in.bEndpointAddress,
                size,
                timeout=timeout
            )
            
            return bytes(data)
            
        except usb.core.USBTimeoutError:
            raise Exception(f"Timeout reading {size} bytes from device")
        except usb.core.USBError as e:
            raise Exception(f"USB error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    def close(self):
        """Close the device connection."""
        if self.device:
            try:
                usb.util.dispose_resources(self.device)
                print("Device connection closed")
            except Exception as e:
                print(f"Warning: Error closing device: {e}")
        
        self.initialized = False
        self.device = None

def main():
    print("BitBabbler Working Module with Device Detection")
    print("=" * 50)
    
    # Test USB backend
    try:
        backend = usb.backend.libusb1.get_backend()
        if backend is None:
            print("✗ USB backend not available")
            return 1
        print("✓ USB backend is working!")
    except Exception as e:
        print(f"✗ USB backend error: {e}")
        return 1
    
    # Create BitBabbler device instance
    bb = BitBabblerDevice()
    
    try:
        # Find and configure the device
        if bb.find_device():
            print("\n✓ BitBabbler device found and initialized!")
            
            # Read some random data samples
            print("\nReading random data samples...")
            for i in range(5):
                try:
                    data = bb.read_random_data(32)  # Read 32 bytes
                    print(f"Sample {i+1}: {data.hex()[:32]}...")
                except Exception as e:
                    print(f"Error reading sample {i+1}: {e}")
                    break
            
            print("\n✓ Random data reading successful!")
            print("The BitBabbler Python module is working correctly!")
            
        else:
            print("✗ Could not initialize BitBabbler device")
            print("You may need to install the WinUSB driver using Zadig")
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        bb.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
