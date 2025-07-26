export interface SpectrumData {
  frequencies: number[];
  fft_data: number[];
  peak_rssi: number;
  distance: number;
  rssi_ref: number;
  timestamp: number;
}

export type ConnectionStatus = "disconnected" | "connecting" | "connected";
