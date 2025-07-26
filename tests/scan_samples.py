#!/usr/bin/env python3
"""
PlutoSDR Radio Scanner Demo
Basic frequency scanning using simple power measurement
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from utils.device import scan_frequency_range, connect_to_plutosdr, disconnect_from_plutosdr

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Connection Configuration
PLUTO_URI = "ip:192.168.2.1"  # Default PlutoSDR IP address

# PlutoSDR Hardware Configuration
PLUTO_CONFIG = {
    'sample_rate': int(15.36e6),      # 30.72 MSPS sample rate
    'rx_rf_bandwidth': int(10e6),     # 50 MHz RF bandwidth
    'rx_buffer_size': 4096,           # Buffer size for samples
    'gain_control_mode': 'manual',    # Manual gain control
    'rx_hardwaregain': 20             # 20 dB hardware gain
}

# Scan Configuration
SCAN_CONFIG = {
    'start_frequency': int(2.4e9),    # 2.4 GHz start frequency
    'end_frequency': int(5.0e9),      # 5.0 GHz end frequency
    'step_frequency': int(10e6),      # 50 MHz frequency steps
    'dwell_time': 0.1                 # 100ms per frequency
}

# Display Configuration
DISPLAY_CONFIG = {
    'top_signals_count': 5            # Number of top signals to display
}


def scan_callback(frequency, power):
    """Callback function for scan results"""
    print(f"  -> {frequency/1e6:.3f} MHz: {power:.2f} dB")


def main():
    """Main function for basic frequency scanning"""
    print("PlutoSDR Radio Scanner Demo")
    print("=" * 40)
    
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
        # Configure SDR settings
        print("\nConfiguring PlutoSDR...")
        if pluto.set_configs(PLUTO_CONFIG):
            print("SDR configured successfully")
        else:
            print("Warning: Some configurations may not have been set")
        
        # Display current settings
        print("\nCurrent Settings:")
        print(f"Sample Rate: {pluto.get_sample_rate()/1e6:.1f} MSPS")
        print(f"RX Frequency: {pluto.get_rx_frequency()/1e6:.3f} MHz")
        print(f"Hardware Gain: {PLUTO_CONFIG['rx_hardwaregain']} dB")
        
        # Display scan configuration
        print("\nStarting frequency scan...")
        print(f"Range: {SCAN_CONFIG['start_frequency']/1e6:.1f} - {SCAN_CONFIG['end_frequency']/1e6:.1f} MHz")
        print(f"Step: {SCAN_CONFIG['step_frequency']/1e6:.1f} MHz")
        print(f"Dwell time: {SCAN_CONFIG['dwell_time']*1000:.0f} ms")
        print("\nPress Ctrl+C to stop scanning\n")
        
        # Perform the scan
        scan_results = scan_frequency_range(
            pluto=pluto,
            start_freq=SCAN_CONFIG['start_frequency'],
            end_freq=SCAN_CONFIG['end_frequency'],
            step_freq=SCAN_CONFIG['step_frequency'],
            dwell_time=SCAN_CONFIG['dwell_time'],
            callback=scan_callback
        )
        
        # Display results summary
        display_scan_results(scan_results)
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error during operation: {e}")
        return 1
    finally:
        # Always disconnect
        print("\nDisconnecting from PlutoSDR...")
        disconnect_from_plutosdr(pluto)
        print("Demo completed")
    
    return 0


def display_scan_results(scan_results):
    """Display and analyze scan results"""
    if not scan_results:
        print("\nNo scan results to display")
        return
    
    print("\nScan Results Summary:")
    print(f"Total frequencies scanned: {len(scan_results)}")
    
    # Find strongest signal
    max_freq = max(scan_results, key=scan_results.get)
    max_power = scan_results[max_freq]
    print(f"Strongest signal: {max_freq/1e6:.3f} MHz at {max_power:.2f} dB")
    
    # Find top signals
    sorted_results = sorted(scan_results.items(), key=lambda x: x[1], reverse=True)
    top_count = DISPLAY_CONFIG['top_signals_count']
    print(f"\nTop {top_count} strongest signals:")
    for i, (freq, power) in enumerate(sorted_results[:top_count]):
        print(f"{i+1}. {freq/1e6:.3f} MHz: {power:.2f} dB")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)