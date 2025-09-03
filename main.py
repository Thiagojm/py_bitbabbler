#!/usr/bin/env python3
"""
BitBabbler Multi-Device Module - Windows Compatible

This version can detect and work with multiple BitBabbler devices,
allowing you to choose which one to use.
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

def find_all_bitbabbler_devices():
    """Find all BitBabbler devices connected to the system."""
    bitbabbler_devices = []
    
    try:
        for device in usb.core.find(find_all=True):
            try:
                manufacturer = get_string_safe(device, device.iManufacturer)
                product = get_string_safe(device, device.iProduct)
                
                # Look for BitBabbler devices by checking product name
                if 'bitbabbler' in product.lower() or 'bitbabbler' in manufacturer.lower():
                    device_info = {
                        'device': device,
                        'vendor_id': device.idVendor,
                        'product_id': device.idProduct,
                        'manufacturer': manufacturer,
                        'product': product,
                        'serial_number': get_string_safe(device, device.iSerialNumber)
                    }
                    bitbabbler_devices.append(device_info)
                    
            except Exception as e:
                # Skip devices we can't read
                continue
                
    except Exception as e:
        print(f"Error scanning for BitBabbler devices: {e}")
    
    return bitbabbler_devices

class BitBabblerDevice:
    """BitBabbler device interface with multi-device support."""
    
    def __init__(self, device_info=None):
        """
        Initialize BitBabbler device.
        
        Args:
            device_info: Dictionary with device information (if None, will auto-detect)
        """
        self.device_info = device_info
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self.initialized = False
    
    @classmethod
    def from_device_info(cls, device_info):
        """Create BitBabblerDevice from device info dictionary."""
        return cls(device_info)
    
    @classmethod
    def auto_detect(cls):
        """Auto-detect and return the first available BitBabbler device."""
        devices = find_all_bitbabbler_devices()
        if devices:
            return cls(devices[0])
        return None
    
    @classmethod
    def list_available_devices(cls):
        """List all available BitBabbler devices."""
        return find_all_bitbabbler_devices()
    
    def find_device(self, auto_configure=True):
        """Find and configure the BitBabbler device."""
        try:
            if self.device_info is None:
                print("No device info provided")
                return False
            
            self.device = self.device_info['device']
            
            print(f"Using BitBabbler device: {self.device_info['manufacturer']} {self.device_info['product']}")
            print(f"Serial: {self.device_info['serial_number']}")
            print(f"VID: 0x{self.device_info['vendor_id']:04x}, PID: 0x{self.device_info['product_id']:04x}")
            
            if auto_configure:
                return self._configure_device()
            
            return True
            
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
    
    def get_device_info(self):
        """Get information about the connected device."""
        if not self.device_info:
            return None
            
        return {
            'vendor_id': f"0x{self.device_info['vendor_id']:04x}",
            'product_id': f"0x{self.device_info['product_id']:04x}",
            'manufacturer': self.device_info['manufacturer'],
            'product': self.device_info['product'],
            'serial_number': self.device_info['serial_number'],
            'initialized': self.initialized
        }
    
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
    print("BitBabbler Multi-Device Module")
    print("=" * 35)
    
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
    
    # Find all BitBabbler devices
    print("\nScanning for BitBabbler devices...")
    devices = BitBabblerDevice.list_available_devices()
    
    if not devices:
        print("No BitBabbler devices found")
        print("\nTo help with detection, here are all USB devices:")
        try:
            all_devices = []
            for device in usb.core.find(find_all=True):
                try:
                    device_info = {
                        'vendor_id': f"0x{device.idVendor:04x}",
                        'product_id': f"0x{device.idProduct:04x}",
                        'manufacturer': get_string_safe(device, device.iManufacturer),
                        'product': get_string_safe(device, device.iProduct),
                    }
                    all_devices.append(device_info)
                except:
                    continue
            
            print(f"\nAll USB devices ({len(all_devices)} found):")
            for i, device in enumerate(all_devices):
                print(f"  {i+1:2d}. VID:{device['vendor_id']} PID:{device['product_id']} - {device['manufacturer']} {device['product']}")
                
        except Exception as e:
            print(f"Error listing devices: {e}")
        
        return 1
    
    print(f"\nFound {len(devices)} BitBabbler device(s):")
    for i, device_info in enumerate(devices):
        print(f"  {i+1}. {device_info['manufacturer']} {device_info['product']}")
        print(f"     Serial: {device_info['serial_number']}")
        print(f"     VID: 0x{device_info['vendor_id']:04x}, PID: 0x{device_info['product_id']:04x}")
    
    # Use the first device (you could modify this to let user choose)
    selected_device = devices[0]
    print(f"\nUsing device: {selected_device['manufacturer']} {selected_device['product']}")
    
    # Create BitBabbler device instance
    bb = BitBabblerDevice.from_device_info(selected_device)
    
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
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        bb.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

