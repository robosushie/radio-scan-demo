"use client";

import dynamic from "next/dynamic";
import type { SpectrumData } from "@/types/spectrum";
import { DISTANCE_CONFIG } from "@/lib/constants";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface LiveMeasurementsProps {
  spectrumData: SpectrumData;
  distanceHistory: { timestamp: number; distance: number }[];
}

export function LiveMeasurements({
  spectrumData,
  distanceHistory,
}: LiveMeasurementsProps) {
  const distancePlotData = [
    {
      x:
        distanceHistory.length > 0
          ? distanceHistory.map(
              (d) => (d.timestamp - distanceHistory[0].timestamp) / 1000
            )
          : [],
      y: distanceHistory.map((d) => d.distance),
      type: "scatter" as const,
      mode: "lines+markers" as const,
      line: { color: "#3b82f6", width: 2 },
      marker: { color: "#3b82f6" },
      name: "Distance (m)",
    },
  ];

  const distancePlotLayout = {
    xaxis: {
      title: { text: "Time (s)" },
      color: "#e5e7eb",
      gridcolor: "#525252",
      range: [0, 30],
    },
    yaxis: {
      title: { text: "Distance (m)" },
      color: "#e5e7eb",
      gridcolor: "#525252",
      range: [0, DISTANCE_CONFIG.max_distance],
    },
    plot_bgcolor: "#171717",
    paper_bgcolor: "#262626",
    font: { color: "#e5e7eb" },
    margin: { l: 40, r: 20, t: 20, b: 40 },
    showlegend: false,
    autosize: true,
    height: 200,
  };

  return (
    <div className="bg-neutral-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold mb-3">Live Measurements</h3>
      <div className="flex justify-around items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-neutral-400">Peak RSSI:</span>
          <span className="font-mono text-lg font-bold text-green-400">
            {spectrumData.peak_rssi.toFixed(2)} dBm
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-neutral-400">RSSI Reference:</span>
          <span className="font-mono">
            {spectrumData.rssi_ref.toFixed(1)} dBm
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-neutral-400">Distance:</span>
          <span className="font-mono text-lg font-bold text-blue-400">
            {spectrumData.distance.toFixed(2)} m
          </span>
        </div>
      </div>
      <div className="mt-4">
        <Plot
          data={distancePlotData}
          layout={distancePlotLayout}
          config={{ displayModeBar: false, responsive: true }}
          style={{ width: "100%", height: "200px" }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
}
