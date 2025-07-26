#!/usr/bin/env python3
"""
PlutoSDR Frequency Scanner with FFT Peak Detection
Enhanced scanner that finds actual signal peaks within bandwidth using FFT
"""

import sys
import os
import time
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from utils.pluto import PlutoSDR
from utils.device import connect_to_plutosdr, disconnect_from_plutosdr

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Connection Configuration
PLUTO_URI = "ip:192.168.2.1"  # Default PlutoSDR IP address

# PlutoSDR Hardware Configuration
PLUTO_CONFIG = {
    'sample_rate': int(64.44e6),      # 30.72 MSPS sample rate for high resolution
    'rx_rf_bandwidth': int(30e6),     # 50 MHz RF bandwidth
    'rx_buffer_size': 8192,           # Large buffer for FFT analysis
    'gain_control_mode': 'manual',    # Manual gain control
    'rx_hardwaregain': 30             # 30 dB hardware gain for weak signals
}

# Scan Configuration
SCAN_CONFIG = {
    'start_frequency': int(1.4e9),    # 2.4 GHz start frequency
    'end_frequency': int(1.9e9),      # 5.0 GHz end frequency
    'step_frequency': int(20e6),      # 50 MHz frequency steps
    'dwell_time': 0.3                 # 300ms per frequency for accuracy
}

# FFT Peak Detection Configuration
FFT_CONFIG = {
    'fft_size': 2048,                 # FFT size (must be power of 2: 1024, 2048, 4096, 8192, 16384)
    'min_peak_height': -40.0,         # Minimum peak height in dB (adjusted for normalized FFT)
    'peak_threshold_db': 25.0,        # Peak must be 15dB above surrounding
    'window_size_divisor': 100,       # Adaptive window size (spectrum_len // divisor)
    'min_window_size': 5,             # Minimum window size for peak detection
    'max_peaks_per_band': 10          # Maximum peaks to detect per frequency band
}

# Display Configuration
DISPLAY_CONFIG = {
    'top_signals_count': 10,          # Number of top signals to display
    'peaks_per_center_freq': 3,       # Peaks to show per center frequency
    'freq_range_grouping': 100e6      # Group signals by frequency ranges (Hz)
}

# =============================================================================
# CUDA/FFT INITIALIZATION
# =============================================================================

# Try to import CuPy for GPU acceleration, fallback to scipy
CUDA_AVAILABLE = False
try:
    import cupy as cp
    from cupyx.scipy import fft as cp_fft
    # Test if CUDA is actually working
    cp.cuda.runtime.getDeviceCount()
    # Try a simple operation to verify CUDA functionality
    test_array = cp.array([1, 2, 3])
    cp_fft.fft(test_array)
    CUDA_AVAILABLE = True
    print("CuPy detected and CUDA working - using GPU acceleration")
except (ImportError, cp.cuda.runtime.CUDARuntimeError, Exception) as e:
    import scipy.fft as sp_fft
    CUDA_AVAILABLE = False
    print(f"CuPy/CUDA not available ({type(e).__name__}) - using CPU scipy")


def detect_peaks_in_spectrum(samples: np.ndarray, center_freq: int, sample_rate: int, 
                           bandwidth: int) -> List[Tuple[int, float]]:
    """
    Detect peaks in the frequency spectrum using FFT
    
    Args:
        samples: Complex IQ samples
        center_freq: Center frequency in Hz
        sample_rate: Sample rate in Hz
        bandwidth: RF bandwidth in Hz
        
    Returns:
        List of (frequency, power_db) tuples for detected peaks
        
    Note:
        Peak detection parameters are taken from FFT_CONFIG constants:
        - fft_size: FFT size for spectral analysis
        - min_peak_height: Minimum peak height in dB
        - peak_threshold_db: Peak must be this many dB above surrounding
    """
    if len(samples) == 0:
        return []
    
    # Use configured FFT size, but don't exceed sample length
    fft_size = min(FFT_CONFIG['fft_size'], len(samples))
    
    # Zero-pad or truncate samples to match FFT size
    if len(samples) < fft_size:
        # Zero-pad if we have fewer samples than FFT size
        padded_samples = np.zeros(fft_size, dtype=samples.dtype)
        padded_samples[:len(samples)] = samples
        samples = padded_samples
    elif len(samples) > fft_size:
        # Truncate if we have more samples than FFT size
        samples = samples[:fft_size]
    
    # Compute FFT
    if CUDA_AVAILABLE:
        # Use CuPy for GPU acceleration
        samples_gpu = cp.asarray(samples)
        fft_result = cp_fft.fft(samples_gpu)
        fft_result = cp.asnumpy(fft_result)  # Move back to CPU
    else:
        # Use scipy for CPU
        fft_result = sp_fft.fft(samples)
    
    # Compute power spectrum in dB with proper scaling
    # Normalize FFT result and convert to dB
    fft_magnitude = np.abs(fft_result)
    # Normalize by FFT size
    normalized_magnitude = fft_magnitude / fft_size
    # Convert to dB with proper reference
    power_spectrum = 20 * np.log10(normalized_magnitude + 1e-12)
    # Optional: Add calibration offset for more realistic dB values
    # power_spectrum -= 60  # Adjust based on your system
    
    # Create frequency array
    freqs = np.fft.fftfreq(len(samples), 1/sample_rate)
    # Shift to center around actual frequency
    freqs = np.fft.fftshift(freqs) + center_freq
    power_spectrum = np.fft.fftshift(power_spectrum)
    
    # Find peaks using configuration constants
    peaks = []
    window_size = max(
        FFT_CONFIG['min_window_size'], 
        len(power_spectrum) // FFT_CONFIG['window_size_divisor']
    )
    
    for i in range(window_size, len(power_spectrum) - window_size):
        current_power = power_spectrum[i]
        
        # Skip if below minimum threshold
        if current_power < FFT_CONFIG['min_peak_height']:
            continue
            
        # Check if it's a local maximum
        local_window = power_spectrum[i-window_size:i+window_size+1]
        if current_power == np.max(local_window):
            # Check if peak is significant enough above surrounding area
            surrounding_avg = np.mean(np.concatenate([
                power_spectrum[max(0, i-window_size*2):i-window_size],
                power_spectrum[i+window_size:min(len(power_spectrum), i+window_size*2)]
            ]))
            
            if current_power - surrounding_avg >= FFT_CONFIG['peak_threshold_db']:
                freq_hz = int(freqs[i])
                # Only include peaks within the expected bandwidth
                if abs(freq_hz - center_freq) <= bandwidth // 2:
                    peaks.append((freq_hz, current_power))
    
    # Sort by power (strongest first) and limit results
    peaks.sort(key=lambda x: x[1], reverse=True)
    return peaks[:FFT_CONFIG['max_peaks_per_band']]


def enhanced_frequency_scan(pluto: PlutoSDR) -> Dict[int, List[Tuple[int, float]]]:
    """
    Enhanced frequency scanner that detects actual peaks within each bandwidth
    
    Args:
        pluto: PlutoSDR instance
        
    Returns:
        Dict mapping center frequencies to lists of (actual_freq, power) peaks
    """
    if not pluto.is_connected or not pluto.sdr:
        print("Error: PlutoSDR not connected")
        return {}
    
    scan_results = {}
    current_freq = SCAN_CONFIG['start_frequency']
    sample_rate = pluto.get_sample_rate()
    rf_bandwidth = getattr(pluto.sdr, 'rx_rf_bandwidth', SCAN_CONFIG['step_frequency'])
    
    print(f"Starting enhanced frequency scan from {SCAN_CONFIG['start_frequency']/1e6:.1f} to {SCAN_CONFIG['end_frequency']/1e6:.1f} MHz")
    print(f"Step: {SCAN_CONFIG['step_frequency']/1e6:.1f} MHz, Sample Rate: {sample_rate/1e6:.1f} MSPS")
    print(f"RF Bandwidth: {rf_bandwidth/1e6:.1f} MHz, Dwell time: {SCAN_CONFIG['dwell_time']:.1f}s")
    print(f"Peak detection: min_height={FFT_CONFIG['min_peak_height']}dB, threshold={FFT_CONFIG['peak_threshold_db']}dB")
    print("\nPress Ctrl+C to stop scanning\n")
    
    try:
        while current_freq <= SCAN_CONFIG['end_frequency']:
            # Set frequency
            pluto.set_frequency(current_freq)
            
            # Wait for settling
            time.sleep(SCAN_CONFIG['dwell_time'])
            
            # Capture samples using configured buffer size
            samples = pluto.capture_samples(PLUTO_CONFIG['rx_buffer_size'])
            
            if samples is not None:
                # Detect peaks in this bandwidth
                peaks = detect_peaks_in_spectrum(
                    samples, current_freq, sample_rate, rf_bandwidth
                )
                
                scan_results[current_freq] = peaks
                
                if peaks:
                    print(f"Center: {current_freq/1e6:.1f} MHz - Found {len(peaks)} peaks:")
                    for freq, power in peaks[:DISPLAY_CONFIG['peaks_per_center_freq']]:
                        print(f"  -> {freq/1e6:.3f} MHz: {power:.1f} dB")
                else:
                    # Calculate average power for comparison
                    avg_power = 20 * np.log10(np.sqrt(np.mean(np.abs(samples)**2)) + 1e-12)
                    print(f"Center: {current_freq/1e6:.1f} MHz - No significant peaks (avg: {avg_power:.1f} dB)")
            else:
                print(f"Center: {current_freq/1e6:.1f} MHz - Failed to capture samples")
                scan_results[current_freq] = []
            
            current_freq += SCAN_CONFIG['step_frequency']
            
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error during scan: {e}")
    
    return scan_results


def analyze_scan_results(scan_results: Dict[int, List[Tuple[int, float]]]) -> None:
    """Analyze and display scan results"""
    if not scan_results:
        print("No scan results to analyze")
        return
    
    # Collect all peaks
    all_peaks = []
    total_center_freqs = len(scan_results)
    center_freqs_with_peaks = 0
    
    for center_freq, peaks in scan_results.items():
        if peaks:
            center_freqs_with_peaks += 1
            all_peaks.extend(peaks)
    
    print(f"\n{'='*60}")
    print("SCAN RESULTS ANALYSIS")
    print(f"{'='*60}")
    print(f"Total center frequencies scanned: {total_center_freqs}")
    print(f"Center frequencies with peaks: {center_freqs_with_peaks}")
    print(f"Total peaks detected: {len(all_peaks)}")
    
    if all_peaks:
        # Sort all peaks by power
        all_peaks.sort(key=lambda x: x[1], reverse=True)
        
        top_count = DISPLAY_CONFIG['top_signals_count']
        print(f"\nTOP {top_count} STRONGEST SIGNALS:")
        print(f"{'Rank':<4} {'Frequency':<12} {'Power':<10}")
        print("-" * 30)
        
        for i, (freq, power) in enumerate(all_peaks[:top_count]):
            print(f"{i+1:<4} {freq/1e6:>8.3f} MHz {power:>8.1f} dB")
        
        # Group by frequency ranges for better analysis
        freq_ranges = {}
        range_size = DISPLAY_CONFIG['freq_range_grouping']
        for freq, power in all_peaks:
            range_key = int(freq // range_size) * int(range_size/1e6)  # Group by configured ranges
            if range_key not in freq_ranges:
                freq_ranges[range_key] = []
            freq_ranges[range_key].append((freq, power))
        
        print(f"\nSIGNALS BY FREQUENCY RANGE:")
        range_size_mhz = int(DISPLAY_CONFIG['freq_range_grouping']/1e6)
        for range_start in sorted(freq_ranges.keys()):
            range_peaks = freq_ranges[range_start]
            range_end = range_start + range_size_mhz
            print(f"\n{range_start}-{range_end} MHz range: {len(range_peaks)} signals")
            
            # Show top peaks in this range
            range_peaks.sort(key=lambda x: x[1], reverse=True)
            show_count = min(DISPLAY_CONFIG['peaks_per_center_freq'], len(range_peaks))
            for freq, power in range_peaks[:show_count]:
                print(f"  {freq/1e6:>8.3f} MHz: {power:>6.1f} dB")


def main():
    """Main function for enhanced frequency scanning with FFT peak detection"""
    print("PlutoSDR Enhanced Frequency Scanner with FFT Peak Detection")
    print("=" * 65)
    
    print(f"Attempting to connect to PlutoSDR at {PLUTO_URI}")
    
    # Connect to PlutoSDR
    pluto = connect_to_plutosdr(PLUTO_URI)
    if not pluto:
        print("Failed to connect to PlutoSDR. Please check:")
        print("1. PlutoSDR is connected and powered on")
        print("2. Network connection is working")
        print("3. PlutoSDR IP address is correct")
        return 1
    
    try:
        # Configure SDR settings for optimal sensitivity
        print("\nConfiguring PlutoSDR...")
        if pluto.set_configs(PLUTO_CONFIG):
            print("SDR configured successfully")
        else:
            print("Warning: Some configurations may not have been set")
        
        # Display current settings
        print(f"\nCurrent Settings:")
        print(f"Sample Rate: {pluto.get_sample_rate()/1e6:.1f} MSPS")
        print(f"RX Frequency: {pluto.get_rx_frequency()/1e6:.3f} MHz") 
        print(f"Hardware Gain: {PLUTO_CONFIG['rx_hardwaregain']} dB")
        print(f"Buffer Size: {PLUTO_CONFIG['rx_buffer_size']} samples")
        
        # Display scan configuration
        print(f"\nScan Configuration:")
        print(f"Range: {SCAN_CONFIG['start_frequency']/1e6:.1f} - {SCAN_CONFIG['end_frequency']/1e6:.1f} MHz")
        print(f"Step: {SCAN_CONFIG['step_frequency']/1e6:.1f} MHz")
        print(f"Dwell time: {SCAN_CONFIG['dwell_time']*1000:.0f} ms")
        
        # Display FFT configuration
        current_sample_rate = pluto.get_sample_rate()
        print(f"\nFFT Peak Detection:")
        print(f"FFT size: {FFT_CONFIG['fft_size']} points")
        print(f"Frequency resolution: {current_sample_rate/FFT_CONFIG['fft_size']/1e3:.1f} kHz")
        print(f"Min peak height: {FFT_CONFIG['min_peak_height']} dB")
        print(f"Peak threshold: {FFT_CONFIG['peak_threshold_db']} dB above surrounding")
        print(f"Max peaks per band: {FFT_CONFIG['max_peaks_per_band']}")
        
        # Perform the enhanced scan
        scan_results = enhanced_frequency_scan(pluto)
        
        # Analyze results
        analyze_scan_results(scan_results)
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error during operation: {e}")
        return 1
    finally:
        # Always disconnect
        print("\nDisconnecting from PlutoSDR...")
        disconnect_from_plutosdr(pluto)
        print("Enhanced scan completed")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)