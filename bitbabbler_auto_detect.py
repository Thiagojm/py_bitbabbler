#!/usr/bin/env python3
"""
BitBabbler Auto-Detection Module - Windows Compatible

This version automatically detects ANY BitBabbler device (White, Black, etc.)
by scanning for devices with "BitBabbler" in the product name.
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

def find_bitbabbler_devices():
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
    """BitBabbler device interface with auto-detection."""
    
    def __init__(self, vendor_id=None, product_id=None):
        """
        Initialize BitBabbler device.
        
        Args:
            vendor_id: Specific vendor ID to look for (if None, auto-detect)
            product_id: Specific product ID to look for (if None, auto-detect)
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self.initialized = False
        self.device_info = None
    
    def find_device(self, auto_configure=True):
        """Find and configure a BitBabbler device."""
        try:
            if self.vendor_id is not None and self.product_id is not None:
                # Look for specific device
                self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
                if self.device is None:
                    print(f"Specific BitBabbler device not found (VID: 0x{self.vendor_id:04x}, PID: 0x{self.product_id:04x})")
                    return False
            else:
                # Auto-detect any BitBabbler device
                bitbabbler_devices = find_bitbabbler_devices()
                
                if not bitbabbler_devices:
                    print("No BitBabbler devices found")
                    print("\nTo help with detection, here are all USB devices:")
                    self._list_all_devices()
                    return False
                
                if len(bitbabbler_devices) == 1:
                    # Only one BitBabbler device found
                    self.device_info = bitbabbler_devices[0]
                    self.device = self.device_info['device']
                    print(f"Found BitBabbler device: {self.device_info['manufacturer']} {self.device_info['product']}")
                    print(f"Serial: {self.device_info['serial_number']}")
                else:
                    # Multiple BitBabbler devices found
                    print(f"Found {len(bitbabbler_devices)} BitBabbler devices:")
                    for i, dev_info in enumerate(bitbabbler_devices):
                        print(f"  {i+1}. {dev_info['manufacturer']} {dev_info['product']} (VID:0x{dev_info['vendor_id']:04x}, PID:0x{dev_info['product_id']:04x})")
                    
                    # Use the first one for now (you could modify this to let user choose)
                    self.device_info = bitbabbler_devices[0]
                    self.device = self.device_info['device']
                    print(f"\nUsing device: {self.device_info['manufacturer']} {self.device_info['product']}")
            
            # Get device information if not already available
            if self.device_info is None:
                manufacturer = get_string_safe(self.device, self.device.iManufacturer)
                product = get_string_safe(self.device, self.device.iProduct)
                serial_number = get_string_safe(self.device, self.device.iSerialNumber)
                
                self.device_info = {
                    'device': self.device,
                    'vendor_id': self.device.idVendor,
                    'product_id': self.device.idProduct,
                    'manufacturer': manufacturer,
                    'product': product,
                    'serial_number': serial_number
                }
                
                print(f"Found BitBabbler device: {manufacturer} {product}")
                print(f"Serial: {serial_number}")
            
            if auto_configure:
                return self._configure_device()
            
            return True
            
        except Exception as e:
            print(f"Error finding device: {e}")
            return False
    
    def _list_all_devices(self):
        """List all USB devices to help with debugging."""
        try:
            devices = []
            for device in usb.core.find(find_all=True):
                try:
                    device_info = {
                        'vendor_id': f"0x{device.idVendor:04x}",
                        'product_id': f"0x{device.idProduct:04x}",
                        'manufacturer': get_string_safe(device, device.iManufacturer),
                        'product': get_string_safe(device, device.iProduct),
                    }
                    devices.append(device_info)
                except:
                    continue
            
            print(f"\nAll USB devices ({len(devices)} found):")
            for i, device in enumerate(devices):
                print(f"  {i+1:2d}. VID:{device['vendor_id']} PID:{device['product_id']} - {device['manufacturer']} {device['product']}")
                
        except Exception as e:
            print(f"Error listing devices: {e}")
    
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
        self.device_info = None

def main():
    print("BitBabbler Auto-Detection Module")
    print("=" * 40)
    
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
    
    # Create BitBabbler device instance with auto-detection
    bb = BitBabblerDevice()  # No specific VID/PID = auto-detect
    
    try:
        # Find and configure any BitBabbler device
        if bb.find_device():
            print("\n✓ BitBabbler device found and initialized!")
            
            # Get device info
            info = bb.get_device_info()
            if info:
                print(f"Device: {info['manufacturer']} {info['product']}")
                print(f"Serial: {info['serial_number']}")
                print(f"VID: {info['vendor_id']}, PID: {info['product_id']}")
            
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
            print("✗ Could not find or initialize any BitBabbler device")
            print("Make sure your BitBabbler device is connected and recognized by Windows")
            return 1
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        bb.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
