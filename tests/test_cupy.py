#!/usr/bin/env python3
"""
Test script to check CuPy installation and CUDA functionality
"""

import sys
import numpy as np

print("Testing CuPy installation...")

try:
    import cupy as cp
    print("✓ CuPy imported successfully")
    
    # Test CUDA device detection
    device_count = cp.cuda.runtime.getDeviceCount()
    print(f"✓ Found {device_count} CUDA device(s)")
    
    # Test basic GPU operations
    test_array = cp.array([1, 2, 3, 4, 5])
    print(f"✓ GPU array created: {test_array}")
    
    # Test FFT on GPU
    fft_result = cp.fft.fft(test_array)
    print(f"✓ GPU FFT successful: {fft_result}")
    
    # Test memory transfer
    cpu_array = cp.asnumpy(test_array)
    print(f"✓ GPU to CPU transfer successful: {cpu_array}")
    
    print("\n🎉 CuPy is working correctly!")
    print("GPU acceleration should be available.")
    
except ImportError as e:
    print(f"✗ CuPy import failed: {e}")
    print("Please check CuPy installation.")
    
except Exception as e:
    print(f"✗ CuPy test failed: {e}")
    print("CUDA may not be properly configured.")

print("\nTesting NumPy fallback...")
test_array = np.array([1, 2, 3, 4, 5])
fft_result = np.fft.fft(test_array)
print(f"✓ NumPy FFT successful: {fft_result}")
print("✓ CPU fallback is working.") 