import time
import json
import os
from typing import Optional, Dict, Any, Callable
from .pluto import PlutoSDR
from .constants import CONSTANTS

def scan_frequency_range(pluto: PlutoSDR, start_freq: int, end_freq: int, 
                        step_freq: int = 1000000, dwell_time: float = 0.1, 
                        callback: Optional[Callable] = None) -> Dict[int, float]:
    """
    Continuously scan frequency range
    
    Args:
        pluto: PlutoSDR instance
        start_freq: Starting frequency in Hz
        end_freq: Ending frequency in Hz
        step_freq: Step frequency in Hz (default: 1MHz)
        dwell_time: Time to spend on each frequency in seconds
        callback: Optional callback function called for each frequency
        
    Returns:
        Dict[int, float]: Dictionary mapping frequencies to power levels
    """
    if not pluto.is_connected or not pluto.sdr:
        print("Error: PlutoSDR not connected")
        return {}
    
    scan_results = {}
    current_freq = start_freq
    
    print(f"Starting frequency scan from {start_freq} Hz to {end_freq} Hz")
    print(f"Step: {step_freq} Hz, Dwell time: {dwell_time}s")
    
    try:
        while current_freq <= end_freq:
            # Set frequency
            pluto.set_frequency(current_freq)
            
            # Wait for settling
            time.sleep(dwell_time)
            
            # Capture samples
            samples = pluto.sdr.rx()
            
            # Calculate power (simple RMS)
            import numpy as np
            power_db = 20 * np.log10(np.sqrt(np.mean(np.abs(samples)**2)))
            
            scan_results[current_freq] = power_db
            
            # Call callback if provided
            if callback:
                callback(current_freq, power_db)
            
            print(f"Freq: {current_freq/1e6:.3f} MHz, Power: {power_db:.2f} dB")
            
            current_freq += step_freq
            
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error during scan: {e}")
    
    print(f"Scan completed. Scanned {len(scan_results)} frequencies")
    return scan_results


def connect_to_plutosdr(uri: str = None) -> Optional[PlutoSDR]:
    """
    Convenience function to connect to PlutoSDR
    
    Args:
        uri: Connection URI (defaults to constants.json value)
        
    Returns:
        PlutoSDR instance if successful, None otherwise
    """
    if uri is None:
        uri = CONSTANTS["pluto"]["connection"]["uri"]
    
    pluto = PlutoSDR()
    if pluto.connect(uri):
        return pluto
    return None


def disconnect_from_plutosdr(pluto: PlutoSDR) -> None:
    """
    Convenience function to disconnect from PlutoSDR
    
    Args:
        pluto: PlutoSDR instance
    """
    if pluto:
        pluto.disconnect()