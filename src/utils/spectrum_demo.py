"""
Single frequency spectrum processing for FFT and peak RSSI detection.
Optimized for real-time streaming with GPU acceleration support.
"""

import numpy as np
from typing import Tuple
from scipy import signal

# Try to import CuPy for GPU acceleration, fallback to CPU
CUDA_AVAILABLE = False
try:
    import cupy as cp
    # Test if CUDA is actually working
    device_count = cp.cuda.runtime.getDeviceCount()
    print(f"Found {device_count} CUDA device(s)")
    
    # Try a simple operation to verify CUDA functionality
    test_array = cp.array([1, 2, 3])
    cp.fft.fft(test_array)
    
    CUDA_AVAILABLE = True
    print("CuPy detected and CUDA working - using GPU acceleration for FFT")
except Exception as e:
    CUDA_AVAILABLE = False
    print(f"CuPy/CUDA not available ({type(e).__name__}: {e}) - using CPU processing")

class SpectrumProcessor:
    """
    Single frequency spectrum processor for real-time FFT analysis and peak detection.
    """
    
    def __init__(self, fft_size: int = 4096, sample_rate: int = int(61.44e6), 
                 center_frequency: int = int(155e6)):
        """
        Initialize the spectrum processor.
        
        Args:
            fft_size: Size of FFT (default 4096)
            sample_rate: Sampling rate in Hz (default 61.44 MSPS)
            center_frequency: Center frequency in Hz (default 155 MHz)
        """
        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.center_frequency = center_frequency
        
        # Pre-calculate frequency array
        freq_step = sample_rate / fft_size
        freq_start = center_frequency - sample_rate // 2
        self.frequencies = np.arange(fft_size) * freq_step + freq_start
        
        # Pre-allocate arrays for processing
        if CUDA_AVAILABLE:
            self._init_gpu_arrays()
        else:
            self._init_cpu_arrays()
        
        print(f"SpectrumProcessor initialized: {fft_size}-point FFT, "
              f"{sample_rate/1e6:.2f} MSPS, center: {center_frequency/1e6:.2f} MHz")
    
    def _init_gpu_arrays(self):
        """Initialize GPU arrays for processing."""
        self.window = cp.asarray(signal.windows.hann(self.fft_size))
        self.iq_buffer = cp.zeros(self.fft_size, dtype=cp.complex64)
        self.windowed = cp.zeros(self.fft_size, dtype=cp.complex64)
        self.fft_result = cp.zeros(self.fft_size, dtype=cp.complex64)
        self.psd = cp.zeros(self.fft_size, dtype=cp.float32)
        self.frequencies_gpu = cp.asarray(self.frequencies)
    
    def _init_cpu_arrays(self):
        """Initialize CPU arrays for processing."""
        self.window = signal.windows.hann(self.fft_size)
        self.iq_buffer = np.zeros(self.fft_size, dtype=np.complex64)
        self.windowed = np.zeros(self.fft_size, dtype=np.complex64)
        self.fft_result = np.zeros(self.fft_size, dtype=np.complex64)
        self.psd = np.zeros(self.fft_size, dtype=np.float32)
    
    def process_fft(self, iq_samples: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Process IQ samples to compute FFT and find peak RSSI.
        
        Args:
            iq_samples: Complex IQ samples array
            
        Returns:
            Tuple of (frequencies, fft_magnitude_db, peak_rssi_dbm)
        """
        # Ensure we have exactly fft_size samples
        if len(iq_samples) > self.fft_size:
            iq_samples = iq_samples[:self.fft_size]
        elif len(iq_samples) < self.fft_size:
            # Pad with zeros if needed
            padded = np.zeros(self.fft_size, dtype=np.complex64)
            padded[:len(iq_samples)] = iq_samples
            iq_samples = padded
        
        if CUDA_AVAILABLE:
            return self._process_fft_gpu(iq_samples)
        else:
            return self._process_fft_cpu(iq_samples)
    
    def _process_fft_gpu(self, iq_samples: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """GPU-accelerated FFT processing."""
        # Transfer data to GPU
        self.iq_buffer[:] = cp.asarray(iq_samples, dtype=cp.complex64)
        
        # Apply windowing function
        cp.multiply(self.iq_buffer, self.window, out=self.windowed)
        
        # Compute FFT
        cp.fft.fft(self.windowed, out=self.fft_result)
        
        # Shift zero frequency to center
        self.fft_result = cp.fft.fftshift(self.fft_result)
        
        # Convert to power spectral density (magnitude squared)
        cp.abs(self.fft_result, out=self.psd.view(dtype=cp.complex64).real)
        cp.square(self.psd, out=self.psd)
        
        # Normalize
        self.psd /= (self.sample_rate * cp.sum(self.window))
        
        # Convert to dBm (assuming 50-ohm impedance)
        # Power in dBm = 10*log10(P_watts * 1000) where P_watts = V^2/R and R=50
        cp.maximum(self.psd, 1e-12, out=self.psd)  # Avoid log(0)
        self.psd = 10.0 * cp.log10(self.psd) + 30 - 10*np.log10(50)  # Convert to dBm
        
        # Find peak RSSI
        peak_idx = cp.argmax(self.psd)
        peak_rssi = float(self.psd[peak_idx])
        
        # Transfer results back to CPU
        frequencies_out = cp.asnumpy(self.frequencies_gpu)
        fft_data_out = cp.asnumpy(self.psd.copy())
        
        return frequencies_out, fft_data_out, peak_rssi
    
    def _process_fft_cpu(self, iq_samples: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        """CPU FFT processing."""
        # Copy to buffer
        self.iq_buffer[:] = iq_samples
        
        # Apply windowing function
        self.windowed[:] = self.iq_buffer * self.window
        
        # Compute FFT
        self.fft_result[:] = np.fft.fft(self.windowed)
        
        # Shift zero frequency to center
        self.fft_result = np.fft.fftshift(self.fft_result)
        
        # Convert to power spectral density (magnitude squared)
        self.psd[:] = np.abs(self.fft_result) ** 2
        
        # Normalize
        self.psd /= (self.sample_rate * np.sum(self.window))
        
        # Convert to dBm (assuming 50-ohm impedance)
        self.psd = np.maximum(self.psd, 1e-12)  # Avoid log(0)
        self.psd = 10.0 * np.log10(self.psd) + 30 - 10*np.log10(50)  # Convert to dBm
        
        # Find peak RSSI
        peak_idx = np.argmax(self.psd)
        peak_rssi = float(self.psd[peak_idx])
        
        return self.frequencies.copy(), self.psd.copy(), peak_rssi
    
    def get_frequency_range(self) -> Tuple[float, float]:
        """Get the frequency range of this processor."""
        return float(self.frequencies[0]), float(self.frequencies[-1])
    
    def get_center_frequency(self) -> float:
        """Get the center frequency."""
        return float(self.center_frequency)
    
    def set_center_frequency(self, center_freq: int):
        """Update center frequency and recalculate frequency array."""
        self.center_frequency = center_freq
        freq_step = self.sample_rate / self.fft_size
        freq_start = center_freq - self.sample_rate // 2
        self.frequencies = np.arange(self.fft_size) * freq_step + freq_start
        
        if CUDA_AVAILABLE:
            self.frequencies_gpu = cp.asarray(self.frequencies)

# Utility function for distance calculation verification
def calculate_distance(peak_rssi: float, rssi_ref: float) -> float:
    """
    Calculate distance using the formula: distance = 10^((peak_rssi - rssi_ref) / 20)
    
    This formula is correct for free-space path loss model where:
    RSSI = RSSI_ref - 20*log10(distance/distance_ref)
    
    Solving for distance:
    distance = distance_ref * 10^((RSSI_ref - RSSI) / 20)
    
    If distance_ref = 1 meter, then:
    distance = 10^((RSSI_ref - RSSI) / 20)
    
    Which can be rewritten as:
    distance = 10^((peak_rssi - rssi_ref) / 20) when peak_rssi < rssi_ref
    
    Args:
        peak_rssi: Peak RSSI value in dBm
        rssi_ref: Reference RSSI value in dBm (at 1 meter distance)
        
    Returns:
        Distance in meters (relative to reference distance of 1 meter)
    """
    return 10 ** ((peak_rssi - rssi_ref) / 20)

# Test function to verify the implementation
if __name__ == "__main__":
    # Test the spectrum processor
    processor = SpectrumProcessor()
    
    # Generate test signal
    t = np.linspace(0, 1024/61.44e6, 1024, endpoint=False)
    test_signal = np.exp(1j * 2 * np.pi * 155e6 * t) + 0.1 * (np.random.randn(1024) + 1j * np.random.randn(1024))
    
    # Process the signal
    freqs, fft_data, peak_rssi = processor.process_fft(test_signal)
    
    print(f"Frequency range: {freqs[0]/1e6:.2f} - {freqs[-1]/1e6:.2f} MHz")
    print(f"Peak RSSI: {peak_rssi:.2f} dBm")
    print(f"Distance (ref=-50dBm): {calculate_distance(peak_rssi, -50):.2f} m")