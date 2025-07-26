"use client";

import type { SpectrumData } from "@/types/spectrum";

interface SpectrumDataInfoProps {
  spectrumData: SpectrumData;
}

export function SpectrumDataInfo({ spectrumData }: SpectrumDataInfoProps) {
  const formatFrequency = (freq: number) => {
    if (freq >= 1e9) {
      return `${(freq / 1e9).toFixed(2)} GHz`;
    } else if (freq >= 1e6) {
      return `${(freq / 1e6).toFixed(2)} MHz`;
    } else if (freq >= 1e3) {
      return `${(freq / 1e3).toFixed(2)} kHz`;
    } else {
      return `${freq.toFixed(2)} Hz`;
    }
  };

  return (
    <div className="bg-neutral-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-3">Spectrum Data</h3>
      <div className="grid grid-cols-1 gap-3 text-sm">
        <div>
          <span className="text-neutral-400">FFT Points:</span>
          <span className="ml-2 font-mono">
            {spectrumData.frequencies.length}
          </span>
        </div>
        <div>
          <span className="text-neutral-400">Frequency Range:</span>
          <span className="ml-2 font-mono">
            {formatFrequency(Math.min(...spectrumData.frequencies))} -{" "}
            {formatFrequency(Math.max(...spectrumData.frequencies))}
          </span>
        </div>
        <div>
          <span className="text-neutral-400">Power Range:</span>
          <span className="ml-2 font-mono">
            {Math.min(...spectrumData.fft_data).toFixed(1)} to{" "}
            {Math.max(...spectrumData.fft_data).toFixed(1)} dBm
          </span>
        </div>
      </div>
    </div>
  );
}
