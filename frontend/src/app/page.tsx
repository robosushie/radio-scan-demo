"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { WebSocketService } from "@/lib/websocket";
import { ApiService } from "@/lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface SpectrumData {
  frequencies: number[];
  power_spectrum: number[];
  timestamp: number;
}

export default function Home() {
  const [spectrumData, setSpectrumData] = useState<SpectrumData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    "disconnected" | "connecting" | "connected"
  >("disconnected");
  const [scanParams, setScanParams] = useState({
    start_frequency: 1.4e9,
    end_frequency: 1.9e9,
    step_frequency: 20e6,
    gain: 10,
    dwell_time: 0.01,
  });
  const [isStreaming, setIsStreaming] = useState(false);

  const wsServiceRef = useRef<WebSocketService | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect();
      }
    };
  }, []);

  const connectWebSocket = async () => {
    try {
      setConnectionStatus("connecting");

      wsServiceRef.current = new WebSocketService(
        "ws://localhost:8000/ws/stream",
        (data: SpectrumData) => {
          setSpectrumData(data);
        }
      );

      await wsServiceRef.current.connect();
      setConnectionStatus("connected");
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
      setConnectionStatus("disconnected");
    }
  };

  const updateScanParams = async () => {
    try {
      await ApiService.setScanParams(scanParams);
      console.log("Scan parameters updated successfully");
    } catch (error) {
      console.error("Error updating scan parameters:", error);
    }
  };

  const toggleStreaming = async () => {
    try {
      const result = await ApiService.toggleStreaming(!isStreaming);
      setIsStreaming(result.streaming);
      console.log(`Streaming ${result.streaming ? "started" : "stopped"}`);
    } catch (error) {
      console.error("Error toggling streaming:", error);
    }
  };

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

  const plotData = spectrumData
    ? [
        {
          x: spectrumData.frequencies.map((f) => f / 1e9), // Convert to GHz
          y: spectrumData.power_spectrum,
          type: "scatter",
          mode: "lines",
          line: { color: "#3b82f6", width: 1.5 },
          name: "Power Spectrum",
        },
      ]
    : [];

  const plotLayout = {
    xaxis: {
      title: { text: "Frequency (GHz)", font: { color: "#e5e7eb" } },
      gridcolor: "#525252",
      gridwidth: 1,
      color: "#e5e7eb",
    },
    yaxis: {
      type: "linear",
      gridcolor: "#525252",
      gridwidth: 1,
      color: "#e5e7eb",
    },
    plot_bgcolor: "#171717", //"#262626", // neutral-800
    paper_bgcolor: "#262626", //"#171717", // neutral-900
    font: { color: "#e5e7eb" },
    margin: { l: 25, r: 25, t: 25, b: 25 },
    showlegend: false,
    autosize: true,
  };

  const plotConfig = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ["pan2d", "lasso2d", "select2d"],
    displaylogo: false,
  };

  return (
    <div className="min-h-screen w-screen bg-neutral-900 text-white p-4">
      <div className="w-full h-full overflow-x-hidden flex flex-col gap-4">
        {/* Connection Status */}
        <div className=" absolute flex w-full justify-center text-center">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              connectionStatus === "connected"
                ? "bg-green-100 text-green-800"
                : connectionStatus === "connecting"
                ? "bg-yellow-100 text-yellow-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full mr-2 ${
                connectionStatus === "connected"
                  ? "bg-green-500"
                  : connectionStatus === "connecting"
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
            ></div>
            {connectionStatus === "connected"
              ? "Connected"
              : connectionStatus === "connecting"
              ? "Connecting..."
              : "Disconnected"}
          </span>
        </div>

        {/* Control Panel */}
        <div className="bg-neutral-800 rounded-lg p-2 flex flex-col gap-4">
          <h2 className="text-xl font-semibold">Scan Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Start Frequency
              </label>
              <input
                type="text"
                value={formatFrequency(scanParams.start_frequency)}
                onChange={(e) => {
                  const value = parseFloat(e.target.value) * 1e9;
                  if (!isNaN(value)) {
                    setScanParams((prev) => ({
                      ...prev,
                      start_frequency: value,
                    }));
                  }
                }}
                className="w-full px-3 py-1 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                End Frequency
              </label>
              <input
                type="text"
                value={formatFrequency(scanParams.end_frequency)}
                onChange={(e) => {
                  const value = parseFloat(e.target.value) * 1e9;
                  if (!isNaN(value)) {
                    setScanParams((prev) => ({
                      ...prev,
                      end_frequency: value,
                    }));
                  }
                }}
                className="w-full px-3 py-1 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Step Size
              </label>
              <input
                type="text"
                value={formatFrequency(scanParams.step_frequency)}
                onChange={(e) => {
                  const value = parseFloat(e.target.value) * 1e6;
                  if (!isNaN(value)) {
                    setScanParams((prev) => ({
                      ...prev,
                      step_frequency: value,
                    }));
                  }
                }}
                className="w-full px-3 py-1 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Gain (dB)
              </label>
              <input
                type="number"
                value={scanParams.gain}
                onChange={(e) =>
                  setScanParams((prev) => ({
                    ...prev,
                    gain: parseInt(e.target.value),
                  }))
                }
                min="-10"
                max="73"
                className="w-full px-3 py-1 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Dwell Time (s)
              </label>
              <input
                type="number"
                value={scanParams.dwell_time}
                onChange={(e) =>
                  setScanParams((prev) => ({
                    ...prev,
                    dwell_time: parseFloat(e.target.value),
                  }))
                }
                min="0"
                max="5.0"
                step="0.01"
                className="w-full px-3 py-1 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="text-xs text-neutral-400 mt-1">
                {scanParams.dwell_time === 0
                  ? "⚠️ No dwell time may cause frequency settling issues"
                  : "Time spent on each frequency step"}
              </div>
            </div>
          </div>
          <div className="flex gap-4">
            <button
              onClick={updateScanParams}
              className="px-6 py-2 bg-blue-700 hover:bg-blue-900 rounded-md font-medium transition-colors cursor-pointer"
            >
              Update Parameters
            </button>
            <button
              onClick={toggleStreaming}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                isStreaming
                  ? "bg-red-700 hover:bg-red-900"
                  : "bg-green-700 hover:bg-green-900"
              }`}
            >
              {isStreaming ? "Stop Streaming" : "Start Streaming"}
            </button>
          </div>
        </div>

        {/* Spectrum Plot */}
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

        {/* Data Info */}
        {spectrumData && (
          <div className="mt-4 bg-neutral-800 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-neutral-400">Data Points:</span>
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
                  {Math.min(...spectrumData.power_spectrum).toFixed(1)} to{" "}
                  {Math.max(...spectrumData.power_spectrum).toFixed(1)} dB
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
