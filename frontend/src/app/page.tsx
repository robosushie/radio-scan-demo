"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";

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
    dwell_time: 0.05,
  });
  const [isStreaming, setIsStreaming] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus("connecting");

    const ws = new WebSocket("ws://localhost:8000/ws/stream");

    ws.onopen = () => {
      console.log("WebSocket connected");
      setConnectionStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data: SpectrumData = JSON.parse(event.data);
        setSpectrumData(data);
      } catch (error) {
        console.error("Error parsing WebSocket data:", error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setConnectionStatus("disconnected");
      setSpectrumData(null);
      // Attempt to reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnectionStatus("disconnected");
    };

    wsRef.current = ws;
  };

  const updateScanParams = async () => {
    try {
      const response = await fetch("http://localhost:8000/set_scan_params", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(scanParams),
      });

      if (response.ok) {
        console.log("Scan parameters updated successfully");
      } else {
        console.error("Failed to update scan parameters");
      }
    } catch (error) {
      console.error("Error updating scan parameters:", error);
    }
  };

  const toggleStreaming = async () => {
    try {
      const response = await fetch("http://localhost:8000/toggle_streaming", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ streaming: !isStreaming }),
      });

      if (response.ok) {
        const result = await response.json();
        setIsStreaming(result.streaming);
        console.log(`Streaming ${result.streaming ? 'started' : 'stopped'}`);
      } else {
        console.error("Failed to toggle streaming");
      }
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
          type: "scatter" as const,
          mode: "lines" as const,
          line: { color: "#3b82f6", width: 1 },
          name: "Power Spectrum",
        },
      ]
    : [];

  const plotLayout = {
    title: {
      text: "Real-time PlutoSDR Spectrum",
      font: { size: 20 },
    },
    xaxis: {
      title: "Frequency (GHz)",
      gridcolor: "#374151",
      gridwidth: 1,
    },
    yaxis: {
      title: "Power Spectral Density (dB)",
      type: "linear" as const,
      gridcolor: "#374151",
      gridwidth: 1,
    },
    plot_bgcolor: "#1f2937",
    paper_bgcolor: "#111827",
    font: { color: "#e5e7eb" },
    margin: { l: 60, r: 20, t: 50, b: 50 },
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
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">
          PlutoSDR Spectrum Scanner
        </h1>

        {/* Connection Status */}
        <div className="mb-4 text-center">
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
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Scan Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">
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
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
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
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
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
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
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
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
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
                min="0.1"
                max="5.0"
                step="0.1"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-4">
            <button
              onClick={updateScanParams}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-md font-medium transition-colors"
            >
              Update Parameters
            </button>
            <button
              onClick={toggleStreaming}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                isStreaming
                  ? "bg-red-600 hover:bg-red-700"
                  : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {isStreaming ? "Stop Streaming" : "Start Streaming"}
            </button>
          </div>
        </div>

        {/* Spectrum Plot */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="h-96 w-full">
            {connectionStatus === "connected" && spectrumData ? (
              <Plot
                data={plotData}
                layout={plotLayout}
                config={plotConfig}
                style={{ width: "100%", height: "100%" }}
                useResizeHandler={true}
              />
            ) : (
              <div className="flex items-center justify-center h-full bg-gray-700 rounded-lg">
                <div className="text-center">
                  <div className="text-gray-400 text-lg mb-2">
                    {connectionStatus === "connecting"
                      ? "Connecting to backend..."
                      : "No stream from backend"}
                  </div>
                  <div className="text-gray-500 text-sm">
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
          <div className="mt-4 bg-gray-800 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Data Points:</span>
                <span className="ml-2 font-mono">
                  {spectrumData.frequencies.length}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Frequency Range:</span>
                <span className="ml-2 font-mono">
                  {formatFrequency(Math.min(...spectrumData.frequencies))} -{" "}
                  {formatFrequency(Math.max(...spectrumData.frequencies))}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Power Range:</span>
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
