import adi
import numpy as np
from typing import Optional, Dict, Any


class PlutoSDR:
    """Helper class for PlutoSDR operations"""
    
    def __init__(self):
        self.sdr: Optional[adi.Pluto] = None
        self.is_connected = False
    
    def connect(self, uri: str = "ip:192.168.2.1") -> bool:
        """
        Connect to PlutoSDR
        
        Args:
            uri: Connection URI (default: "ip:192.168.2.1")
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.sdr = adi.Pluto(uri)
            self.is_connected = True
            print(f"Successfully connected to PlutoSDR at {uri}")
            return True
        except Exception as e:
            print(f"Failed to connect to PlutoSDR: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from PlutoSDR"""
        if self.sdr:
            try:
                del self.sdr
                self.sdr = None
                self.is_connected = False
                print("PlutoSDR disconnected successfully")
            except Exception as e:
                print(f"Error during disconnection: {e}")
    
    def set_configs(self, configs: Dict[str, Any]) -> bool:
        """
        Set SDR configurations
        
        Args:
            configs: Dictionary of configuration parameters
                    Possible keys: sample_rate, rx_lo, tx_lo, rx_rf_bandwidth,
                    tx_rf_bandwidth, rx_buffer_size, gain_control_mode, rx_hardwaregain
                    
        Returns:
            bool: True if all configs set successfully, False otherwise
        """
        if not self.is_connected or not self.sdr:
            print("Error: PlutoSDR not connected")
            return False
        
        try:
            # Map common parameter names to actual PlutoSDR attributes
            param_mapping = {
                'gain_control_mode': 'gain_control_mode_chan0',
                'rx_hardwaregain': 'rx_hardwaregain_chan0'
            }
            
            for key, value in configs.items():
                # Use mapped parameter name if available
                actual_key = param_mapping.get(key, key)
                
                if hasattr(self.sdr, actual_key):
                    setattr(self.sdr, actual_key, value)
                    print(f"Set {actual_key}: {value}")
                else:
                    print(f"Warning: Unknown configuration parameter: {key}")
            return True
        except Exception as e:
            print(f"Error setting configurations: {e}")
            return False
    
    def set_frequency(self, frequency_hz: int, is_tx: bool = False) -> bool:
        """
        Set frequency for RX or TX
        
        Args:
            frequency_hz: Frequency in Hz
            is_tx: If True, set TX frequency; if False, set RX frequency
            
        Returns:
            bool: True if frequency set successfully, False otherwise
        """
        if not self.is_connected or not self.sdr:
            print("Error: PlutoSDR not connected")
            return False
        
        try:
            if is_tx:
                self.sdr.tx_lo = frequency_hz
                # print(f"TX frequency set to: {frequency_hz} Hz")
            else:
                self.sdr.rx_lo = frequency_hz
                # print(f"RX frequency set to: {frequency_hz} Hz")
            return True
        except Exception as e:
            print(f"Error setting frequency: {e}")
            return False
    
    
    def get_sample_rate(self) -> Optional[int]:
        """Get current sample rate"""
        if self.is_connected and self.sdr:
            return self.sdr.sample_rate
        return None
    
    def get_rx_frequency(self) -> Optional[int]:
        """Get current RX frequency"""
        if self.is_connected and self.sdr:
            return self.sdr.rx_lo
        return None
    
    def capture_samples(self, num_samples: int = 1024) -> Optional[np.ndarray]:
        """
        Capture samples from the SDR
        
        Args:
            num_samples: Number of samples to capture
            
        Returns:
            numpy array of complex samples or None if error
        """
        if not self.is_connected or not self.sdr:
            print("Error: PlutoSDR not connected")
            return None
        
        try:
            self.sdr.rx_buffer_size = num_samples
            samples = self.sdr.rx()
            return samples
        except Exception as e:
            print(f"Error capturing samples: {e}")
            return None

