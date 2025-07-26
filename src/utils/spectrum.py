import numpy as np
import time
from typing import Dict, Tuple, Optional
from scipy import signal
from .pluto import PlutoSDR
from .device import connect_to_plutosdr, disconnect_from_plutosdr

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
    print("CuPy detected and CUDA working - using GPU acceleration")
except Exception as e:
    CUDA_AVAILABLE = False
    print(f"CuPy/CUDA not available ({type(e).__name__}: {e}) - using CPU processing")
    print("To enable GPU acceleration, install CUDA Toolkit from: https://developer.nvidia.com/cuda-downloads")


def initialize_gpu_memory_pools():
    """Initialize CuPy memory pools for optimal GPU memory management."""
    if not CUDA_AVAILABLE:
        return None
    try:
        cp.cuda.MemoryPool().set_limit(size=2**30)  # 1GB limit
        mempool = cp.get_default_memory_pool()
        mempool.free_all_blocks()
        return mempool
    except Exception as e:
        print(f"Failed to initialize GPU memory pools: {e}")
        return None


def preallocate_arrays(num_steps: int, fft_size: int):
    """Pre-allocate arrays (GPU or CPU) to avoid allocation overhead during scanning."""
    if CUDA_AVAILABLE:
        # GPU arrays
        arrays = {
            'iq_buffer': cp.zeros(fft_size, dtype=cp.complex64),
            'windowed': cp.zeros(fft_size, dtype=cp.complex64),
            'fft_result': cp.zeros(fft_size, dtype=cp.complex64),
            'psd': cp.zeros(fft_size, dtype=cp.float32),
            'segments': cp.zeros((num_steps, fft_size), dtype=cp.float32),
            'freq_arrays': cp.zeros((num_steps, fft_size), dtype=cp.float32),
            'window': cp.asarray(signal.windows.hann(fft_size))
        }
    else:
        # CPU arrays
        arrays = {
            'iq_buffer': np.zeros(fft_size, dtype=np.complex64),
            'windowed': np.zeros(fft_size, dtype=np.complex64),
            'fft_result': np.zeros(fft_size, dtype=np.complex64),
            'psd': np.zeros(fft_size, dtype=np.float32),
            'segments': np.zeros((num_steps, fft_size), dtype=np.float32),
            'freq_arrays': np.zeros((num_steps, fft_size), dtype=np.float32),
            'window': signal.windows.hann(fft_size)
        }
    return arrays


def capture_and_process_segment(pluto: PlutoSDR, center_freq: int, arrays: Dict, 
                               sample_rate: int, fft_size: int) -> Tuple[np.ndarray, np.ndarray]:
    """Capture IQ samples and process them (GPU or CPU) for a single frequency segment."""
    # Tune PlutoSDR to center frequency
    pluto.set_frequency(center_freq)
    time.sleep(0.01)  # Frequency settling time
    
    # Capture IQ samples
    iq_samples = pluto.capture_samples(fft_size)[:fft_size]
    
    if CUDA_AVAILABLE:
        # GPU processing
        arrays['iq_buffer'][:] = cp.asarray(iq_samples, dtype=cp.complex64)
        
        # Apply windowing function on GPU
        cp.multiply(arrays['iq_buffer'], arrays['window'], out=arrays['windowed'])
        
        # Compute FFT on GPU
        cp.fft.fft(arrays['windowed'], out=arrays['fft_result'])
        
        # Convert to power spectral density
        cp.abs(arrays['fft_result'], out=arrays['psd'].view(dtype=cp.complex64).real)
        cp.square(arrays['psd'], out=arrays['psd'])
        
        # Normalize and convert to dB
        arrays['psd'] /= (sample_rate * cp.sum(arrays['window']))
        cp.maximum(arrays['psd'], 1e-12, out=arrays['psd'])  # Avoid log(0)
        cp.log10(arrays['psd'], out=arrays['psd'])
        arrays['psd'] *= 10.0  # Convert to dB
        
        # Generate frequency array for this segment
        freq_start = center_freq - sample_rate // 2
        freq_step = sample_rate / fft_size
        freqs = cp.arange(fft_size, dtype=cp.float32) * freq_step + freq_start
        
        return cp.asnumpy(freqs), cp.asnumpy(arrays['psd'].copy())
    else:
        # CPU processing
        arrays['iq_buffer'][:] = iq_samples
        
        # Apply windowing function
        arrays['windowed'][:] = arrays['iq_buffer'] * arrays['window']
        
        # Compute FFT
        arrays['fft_result'][:] = np.fft.fft(arrays['windowed'])
        
        # Convert to power spectral density
        arrays['psd'][:] = np.abs(arrays['fft_result']) ** 2
        
        # Normalize and convert to dB
        arrays['psd'] /= (sample_rate * np.sum(arrays['window']))
        arrays['psd'] = np.maximum(arrays['psd'], 1e-12)  # Avoid log(0)
        arrays['psd'] = 10.0 * np.log10(arrays['psd'])  # Convert to dB
        
        # Generate frequency array for this segment
        freq_start = center_freq - sample_rate // 2
        freq_step = sample_rate / fft_size
        freqs = np.arange(fft_size, dtype=np.float32) * freq_step + freq_start
        
        return freqs, arrays['psd'].copy()


def find_overlap_regions(freq1: np.ndarray, freq2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Find overlapping frequency bins between adjacent segments."""
    if CUDA_AVAILABLE:
        # GPU operations
        overlap_mask1 = (freq1 >= freq2[0]) & (freq1 <= freq2[-1])
        overlap_mask2 = (freq2 >= freq1[0]) & (freq2 <= freq1[-1])
        return cp.where(overlap_mask1)[0], cp.where(overlap_mask2)[0]
    else:
        # CPU operations
        overlap_mask1 = (freq1 >= freq2[0]) & (freq1 <= freq2[-1])
        overlap_mask2 = (freq2 >= freq1[0]) & (freq2 <= freq1[-1])
        return np.where(overlap_mask1)[0], np.where(overlap_mask2)[0]


def align_segments_with_correlation(psd1: np.ndarray, psd2: np.ndarray, 
                                  overlap_idx1: np.ndarray, overlap_idx2: np.ndarray) -> float:
    """Use cross-correlation to find optimal alignment between segments."""
    if len(overlap_idx1) == 0 or len(overlap_idx2) == 0:
        return 0.0
    
    overlap1 = psd1[overlap_idx1]
    overlap2 = psd2[overlap_idx2]
    
    if CUDA_AVAILABLE:
        correlation = cp.correlate(overlap1, overlap2, mode='full')
        max_idx = cp.argmax(correlation)
    else:
        correlation = np.correlate(overlap1, overlap2, mode='full')
        max_idx = np.argmax(correlation)
    
    offset = max_idx - len(overlap2) + 1
    return float(offset)


def calculate_gain_corrections(segments: np.ndarray) -> np.ndarray:
    """Calculate gain correction factors using median normalization."""
    if CUDA_AVAILABLE:
        segments_gpu = cp.asarray(segments)
        gain_corrections = cp.ones(len(segments), dtype=cp.float32)
        reference_level = cp.median(segments_gpu[0])
        
        for i in range(1, len(segments)):
            current_level = cp.median(segments_gpu[i])
            gain_corrections[i] = reference_level / current_level
        
        return cp.asnumpy(gain_corrections)
    else:
        gain_corrections = np.ones(len(segments), dtype=np.float32)
        reference_level = np.median(segments[0])
        
        for i in range(1, len(segments)):
            current_level = np.median(segments[i])
            gain_corrections[i] = reference_level / current_level
        
        return gain_corrections


def stitch_segments_with_overlap_handling(segments: np.ndarray, freq_arrays: np.ndarray, 
                                        gain_corrections: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Stitch all segments together with overlap handling and gain correction."""
    if CUDA_AVAILABLE:
        current_freqs = cp.asarray(freq_arrays[0])
        current_psd = cp.asarray(segments[0])
        
        for i in range(1, len(segments)):
            next_freqs = cp.asarray(freq_arrays[i])
            next_psd = cp.asarray(segments[i]) * gain_corrections[i]
            
            # Simple non-overlapping concatenation for performance
            if current_freqs[-1] < next_freqs[0]:
                current_freqs = cp.concatenate([current_freqs, next_freqs])
                current_psd = cp.concatenate([current_psd, next_psd])
            else:
                # Quick overlap handling - just take the unique parts
                overlap_start = cp.searchsorted(next_freqs, current_freqs[-1])
                if overlap_start < len(next_freqs):
                    current_freqs = cp.concatenate([current_freqs, next_freqs[overlap_start:]])
                    current_psd = cp.concatenate([current_psd, next_psd[overlap_start:]])
        
        return cp.asnumpy(current_freqs), cp.asnumpy(current_psd)
    else:
        current_freqs = freq_arrays[0].copy()
        current_psd = segments[0].copy()
        
        for i in range(1, len(segments)):
            next_freqs = freq_arrays[i]
            next_psd = segments[i] * gain_corrections[i]
            
            # Simple non-overlapping concatenation for performance
            if current_freqs[-1] < next_freqs[0]:
                current_freqs = np.concatenate([current_freqs, next_freqs])
                current_psd = np.concatenate([current_psd, next_psd])
            else:
                # Quick overlap handling - just take the unique parts
                overlap_start = np.searchsorted(next_freqs, current_freqs[-1])
                if overlap_start < len(next_freqs):
                    current_freqs = np.concatenate([current_freqs, next_freqs[overlap_start:]])
                    current_psd = np.concatenate([current_psd, next_psd[overlap_start:]])
        
        return current_freqs, current_psd


def apply_final_smoothing(psd: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Apply final smoothing filter."""
    if len(psd) > kernel_size * 2:
        if CUDA_AVAILABLE:
            kernel = cp.ones(kernel_size) / kernel_size
            return cp.convolve(psd, kernel, mode='same')
        else:
            kernel = np.ones(kernel_size) / kernel_size
            return np.convolve(psd, kernel, mode='same')
    return psd


def scan_and_stitch_spectrum(pluto_config: Dict, fft_config: Dict, scan_config: Dict, 
                           uri: str = "ip:192.168.2.1") -> Tuple[np.ndarray, np.ndarray]:
    """
    Main function to scan entire frequency range and stitch into single spectrum.
    
    Uses CuPy memory pools and pre-allocated GPU arrays for maximum performance.
    All intermediate processing stays on GPU to minimize memory transfers.
    
    Args:
        pluto_config: PlutoSDR configuration dictionary
        fft_config: FFT processing configuration dictionary  
        scan_config: Scanning parameters dictionary
        uri: PlutoSDR connection URI
        
    Returns:
        Tuple of (frequencies, power_spectral_density) as numpy arrays
    """
    # Initialize GPU memory pools
    mempool = initialize_gpu_memory_pools()
    
    # Connect to PlutoSDR using existing device.py functions
    pluto = connect_to_plutosdr(uri)
    if not pluto:
        print("Failed to connect to PlutoSDR")
        return np.array([]), np.array([])
    
    # Configure PlutoSDR
    if not pluto.set_configs(pluto_config):
        print("Failed to configure PlutoSDR")
        disconnect_from_plutosdr(pluto)
        return np.array([]), np.array([])
    
    try:
        # Calculate parameters
        start_freq = scan_config['start_frequency']
        end_freq = scan_config['end_frequency']
        step_freq = scan_config['step_frequency']
        num_steps = int((end_freq - start_freq) / step_freq) + 1
        fft_size = fft_config['fft_size']
        sample_rate = pluto_config['sample_rate']
        
        # Pre-allocate GPU arrays
        arrays = preallocate_arrays(num_steps, fft_size)
        
        
        # Scan all frequency segments
        for i, center_freq in enumerate(range(start_freq, end_freq + 1, step_freq)):
            if i >= num_steps:
                break
                
            
            freqs, psd = capture_and_process_segment(pluto, center_freq, arrays, sample_rate, fft_size)
            
            # Store in pre-allocated arrays
            arrays['segments'][i] = psd
            arrays['freq_arrays'][i] = freqs
            
            # Brief pause for PlutoSDR
            time.sleep(scan_config.get('dwell_time', 0.1))
        
        # Calculate gain corrections across all segments
        gain_corrections = calculate_gain_corrections(arrays['segments'][:num_steps])
        
        # Stitch all segments together
        final_freqs, final_psd = stitch_segments_with_overlap_handling(
            arrays['segments'][:num_steps],
            arrays['freq_arrays'][:num_steps],
            gain_corrections
        )
        
        # Apply final smoothing filter
        final_psd = apply_final_smoothing(final_psd)
        
        # Transfer final result back to CPU if using GPU
        if CUDA_AVAILABLE:
            cpu_freqs = cp.asnumpy(final_freqs)
            cpu_psd = cp.asnumpy(final_psd)
        else:
            cpu_freqs = final_freqs
            cpu_psd = final_psd
        
        return cpu_freqs, cpu_psd
        
    finally:
        # Clean up memory and disconnect PlutoSDR
        if CUDA_AVAILABLE and mempool:
            mempool.free_all_blocks()
        disconnect_from_plutosdr(pluto)


def scan_and_stitch_spectrum_with_connection(pluto: PlutoSDR, fft_config: Dict, scan_config: Dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scan spectrum using existing PlutoSDR connection.
    Does NOT connect/disconnect - uses provided connection.
    
    Args:
        pluto: Existing connected PlutoSDR instance
        fft_config: FFT processing configuration dictionary  
        scan_config: Scanning parameters dictionary
        
    Returns:
        Tuple of (frequencies, power_spectral_density) as numpy arrays
    """
    if not pluto or not pluto.is_connected:
        return np.array([]), np.array([])
    
    try:
        # Calculate parameters
        start_freq = scan_config['start_frequency']
        end_freq = scan_config['end_frequency']
        step_freq = scan_config['step_frequency']
        num_steps = int((end_freq - start_freq) / step_freq) + 1
        fft_size = fft_config['fft_size']
        sample_rate = pluto.get_sample_rate()
        
        # Pre-allocate arrays
        arrays = preallocate_arrays(num_steps, fft_size)
        
        # Scan all frequency segments
        for i, center_freq in enumerate(range(start_freq, end_freq + 1, step_freq)):
            if i >= num_steps:
                break
                
            freqs, psd = capture_and_process_segment(pluto, center_freq, arrays, sample_rate, fft_size)
            
            # Store in pre-allocated arrays
            arrays['segments'][i] = psd
            arrays['freq_arrays'][i] = freqs
            
            # Brief pause for PlutoSDR
            time.sleep(scan_config.get('dwell_time', 0.05))
        
        # Calculate gain corrections across all segments
        gain_corrections = calculate_gain_corrections(arrays['segments'][:num_steps])
        
        # Stitch all segments together
        final_freqs, final_psd = stitch_segments_with_overlap_handling(
            arrays['segments'][:num_steps],
            arrays['freq_arrays'][:num_steps],
            gain_corrections
        )
        
        # Apply final smoothing filter
        final_psd = apply_final_smoothing(final_psd)
        
        # Transfer final result back to CPU if using GPU
        if CUDA_AVAILABLE:
            cpu_freqs = cp.asnumpy(final_freqs) if hasattr(final_freqs, 'get') else final_freqs
            cpu_psd = cp.asnumpy(final_psd) if hasattr(final_psd, 'get') else final_psd
        else:
            cpu_freqs = final_freqs
            cpu_psd = final_psd
        
        return cpu_freqs, cpu_psd
        
    except Exception as e:
        print(f"Error in spectrum scan: {e}")
        return np.array([]), np.array([])