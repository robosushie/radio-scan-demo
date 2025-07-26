#!/usr/bin/env python3
"""
Test script for GPU-accelerated spectrum scanning and stitching functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from utils.spectrum import scan_and_stitch_spectrum

# PlutoSDR Hardware Configuration
PLUTO_CONFIG = {
    'sample_rate': int(61.44e6),      # 64.44 MSPS sample rate for high resolution
    'rx_rf_bandwidth': int(30e6),     # 30 MHz RF bandwidth
    'rx_buffer_size': 8192,           # Large buffer for FFT analysis
    'gain_control_mode': 'manual',    # Manual gain control
    'rx_hardwaregain': 10             # 30 dB hardware gain for weak signals
}

# Scan Configuration - 2.4-2.8 GHz with 20MHz steps
SCAN_CONFIG = {
    'start_frequency': int(1.4e9),    # 2.4 GHz start frequency
    'end_frequency': int(1.9e9),      # 2.8 GHz end frequency
    'step_frequency': int(20e6),      # 20 MHz frequency steps
    'dwell_time': 0.3                 # 300ms per frequency for accuracy
}

# FFT Peak Detection Configuration
FFT_CONFIG = {
    'fft_size': 2048,                 # FFT size (must be power of 2)
    'min_peak_height': -40.0,         # Minimum peak height in dB
    'peak_threshold_db': 25.0,        # Peak must be 25dB above surrounding
    'window_size_divisor': 100,       # Adaptive window size
    'min_window_size': 5,             # Minimum window size for peak detection
    'max_peaks_per_band': 10          # Maximum peaks to detect per frequency band
}


def test_live_spectrum_scanning():
    """Test live PlutoSDR scanning in 2.4-2.8 GHz band."""
    print("Starting 2.4-2.8 GHz spectrum scanning and stitching...")
    print(f"Frequency range: {SCAN_CONFIG['start_frequency']/1e9:.2f} - {SCAN_CONFIG['end_frequency']/1e9:.2f} GHz")
    print(f"Step size: {SCAN_CONFIG['step_frequency']/1e6:.1f} MHz")
    print(f"PlutoSDR bandwidth: 30 MHz")
    print(f"FFT size: {FFT_CONFIG['fft_size']}")
    
    try:
        # Perform spectrum scan and stitching
        frequencies, power_spectrum = scan_and_stitch_spectrum(
            PLUTO_CONFIG, 
            FFT_CONFIG, 
            SCAN_CONFIG
        )
        
        if len(frequencies) == 0:
            print("ERROR: No data captured during scan")
            return False
        
        print(f"Scan and stitching completed successfully!")
        print(f"Total spectrum points: {len(frequencies)}")
        print(f"Stitched frequency range: {frequencies[0]/1e9:.3f} - {frequencies[-1]/1e9:.3f} GHz")
        print(f"Power range: {np.min(power_spectrum):.1f} to {np.max(power_spectrum):.1f} dB")
        
        # Save results to file
        save_results(frequencies, power_spectrum)
        
        # Plot results
        plot_spectrum(frequencies, power_spectrum)
        
        return True
        
    except Exception as e:
        print(f"ERROR during spectrum scan: {e}")
        return False


def save_results(frequencies, power_spectrum, filename="stitched_1.4_1.9GHz_results.npz"):
    """Save scan results to file."""
    try:
        np.savez(filename, 
                frequencies=frequencies, 
                power_spectrum=power_spectrum,
                pluto_config=PLUTO_CONFIG,
                scan_config=SCAN_CONFIG,
                fft_config=FFT_CONFIG)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"Error saving results: {e}")


def plot_spectrum(frequencies, power_spectrum, save_plot=True):
    """Plot the stitched spectrum."""
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(frequencies/1e9, power_spectrum, linewidth=0.8)
        plt.xlabel('Frequency (GHz)')
        plt.ylabel('Power Spectral Density (dB)')
        plt.title('Stitched 2.4-2.8 GHz Spectrum')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_plot:
            plt.savefig('stitched_1.4_1.9GHz_spectrum.png', dpi=300, bbox_inches='tight')
            print("Stitched spectrum plot saved to stitched_2.4_2.8GHz_spectrum.png")
        
        plt.show()
        
    except Exception as e:
        print(f"Error plotting spectrum: {e}")


def test_synthetic_data():
    """Test stitching algorithm with synthetic data."""
    print("\nTesting with synthetic data...")
    
    # Create synthetic overlapping segments
    freq1 = np.linspace(1.4e9, 1.5e9, 1000)
    freq2 = np.linspace(1.45e9, 1.55e9, 1000)  # 50 MHz overlap
    freq3 = np.linspace(1.5e9, 1.6e9, 1000)
    
    # Create synthetic power spectra with some peaks
    power1 = -80 + 10 * np.sin(2 * np.pi * (freq1 - 1.4e9) / 50e6) + np.random.normal(0, 2, len(freq1))
    power2 = -75 + 15 * np.sin(2 * np.pi * (freq2 - 1.45e9) / 30e6) + np.random.normal(0, 2, len(freq2))
    power3 = -82 + 8 * np.sin(2 * np.pi * (freq3 - 1.5e9) / 40e6) + np.random.normal(0, 2, len(freq3))
    
    # Add a strong signal in the overlap region
    peak_freq = 1.475e9
    for i, f in enumerate(freq1):
        if abs(f - peak_freq) < 5e6:
            power1[i] += 30 * np.exp(-((f - peak_freq) / 2e6)**2)
    
    for i, f in enumerate(freq2):
        if abs(f - peak_freq) < 5e6:
            power2[i] += 30 * np.exp(-((f - peak_freq) / 2e6)**2)
    
    # Plot synthetic segments
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(freq1/1e9, power1, label='Segment 1', alpha=0.7)
    plt.plot(freq2/1e9, power2, label='Segment 2', alpha=0.7)
    plt.plot(freq3/1e9, power3, label='Segment 3', alpha=0.7)
    plt.xlabel('Frequency (GHz)')
    plt.ylabel('Power (dB)')
    plt.title('Synthetic Overlapping Segments')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Simple stitching demonstration
    plt.subplot(2, 1, 2)
    all_freqs = np.concatenate([freq1, freq2, freq3])
    all_powers = np.concatenate([power1, power2, power3])
    
    # Sort by frequency
    sort_idx = np.argsort(all_freqs)
    sorted_freqs = all_freqs[sort_idx]
    sorted_powers = all_powers[sort_idx]
    
    plt.plot(sorted_freqs/1e9, sorted_powers, 'b-', linewidth=0.8, label='Simple Concatenation')
    plt.xlabel('Frequency (GHz)')
    plt.ylabel('Power (dB)')
    plt.title('Stitched Result (Simple Concatenation)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('synthetic_stitching_test.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Synthetic data test completed")


if __name__ == "__main__":
    print("GPU-Accelerated Spectrum Stitching Test")
    print("=" * 50)
    
    # Test with synthetic data first
    test_synthetic_data()
    
    # Test with real PlutoSDR data
    print("\n" + "=" * 50)
    success = test_live_spectrum_scanning()
    
    if success:
        print("\nAll tests completed successfully!")
    else:
        print("\nSome tests failed. Check PlutoSDR connection and configuration.")