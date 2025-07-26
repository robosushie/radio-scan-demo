"use client";

import dynamic from "next/dynamic";
import type { SpectrumData, ConnectionStatus } from "@/types/spectrum";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface SpectrumPlotProps {
  spectrumData: SpectrumData | null;
  connectionStatus: ConnectionStatus;
}

export function SpectrumPlot({
  spectrumData,
  connectionStatus,
}: SpectrumPlotProps) {
  const plotData = spectrumData
    ? [
        {
          x: spectrumData.frequencies.map((f) => f / 1e6), // Convert to MHz
          y: spectrumData.fft_data,
          type: "scatter" as const,
          mode: "lines" as const,
          line: { color: "#3b82f6", width: 1.5 },
          name: "FFT Spectrum",
        },
      ]
    : [];

  const plotLayout = {
    xaxis: {
      title: { text: "Frequency (MHz)", font: { color: "#e5e7eb" } },
      gridcolor: "#525252",
      gridwidth: 1,
      color: "#e5e7eb",
    },
    yaxis: {
      type: "linear" as const,
      range: [-60, 100], // Adjusted range for dBm
      title: { text: "Power (dBm)", font: { color: "#e5e7eb" } },
      gridcolor: "#525252",
      gridwidth: 1,
      color: "#e5e7eb",
    },
    plot_bgcolor: "#171717",
    paper_bgcolor: "#262626",
    font: { color: "#e5e7eb" },
    margin: { l: 25, r: 25, t: 25, b: 25 },
    showlegend: false,
    autosize: true,
  };

  const plotConfig = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ["pan2d", "lasso2d", "select2d"] as any,
    displaylogo: false,
  };

  return (
    <div className="bg-neutral-800 rounded-lg">
      <div className="h-96 w-full">
        {connectionStatus === "connected" && spectrumData ? (
          <Plot
            data={plotData}
            layout={plotLayout}
            config={plotConfig}
            style={{ width: "100%", height: "100%" }}
            className="rounded-lg overflow-hidden"
            useResizeHandler={true}
          />
        ) : (
          <div className="flex items-center justify-center h-full bg-neutral-700 rounded-lg">
            <div className="text-center">
              <div className="text-neutral-400 text-lg mb-2">
                {connectionStatus === "connecting"
                  ? "Connecting to backend..."
                  : "No stream from backend"}
              </div>
              <div className="text-neutral-500 text-sm">
                {connectionStatus === "disconnected" &&
                  "Check if the backend server is running"}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
