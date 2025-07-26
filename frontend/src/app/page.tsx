"use client";

import { useState, useEffect, useRef } from "react";
import { WebSocketService } from "@/lib/websocket";
import { ApiService } from "@/lib/api";
import DistanceMap from "@/components/DistanceMap";
import type { SpectrumData, ConnectionStatus } from "@/types/spectrum";
import { ConnectionStatus as ConnectionStatusComponent } from "@/components/ConnectionStatus";
import { SpectrumPlot } from "@/components/SpectrumPlot";
import { ControlPanel } from "@/components/ControlPanel";
import { LiveMeasurements } from "@/components/LiveMeasurements";
import { SpectrumDataInfo } from "@/components/SpectrumDataInfo";

export default function Home() {
  const [spectrumData, setSpectrumData] = useState<SpectrumData | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [rssiRef, setRssiRef] = useState(-50.0);
  const [isStreaming, setIsStreaming] = useState(false);
  const [distanceHistory, setDistanceHistory] = useState<
    { timestamp: number; distance: number }[]
  >([]);

  // Input field for RSSI reference
  const [rssiRefInput, setRssiRefInput] = useState("-50");

  const wsServiceRef = useRef<WebSocketService | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    if (spectrumData) {
      setDistanceHistory((prev) => {
        const now = Date.now();
        // Remove points older than 30 seconds
        const filtered = prev.filter((d) => now - d.timestamp <= 30000);
        return [
          ...filtered,
          { timestamp: now, distance: spectrumData.distance },
        ];
      });
    }
  }, [spectrumData]);

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

  const updateRSSIRef = async () => {
    try {
      const numValue = parseFloat(rssiRefInput);
      if (!isNaN(numValue)) {
        await ApiService.setRSSIRef(numValue);
        setRssiRef(numValue);
        console.log("RSSI reference updated successfully");
      }
    } catch (error) {
      console.error("Error updating RSSI reference:", error);
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

  return (
    <div className="min-h-screen w-screen bg-neutral-900 text-white p-4">
      <div className="w-full h-full overflow-x-hidden flex flex-col gap-4">
        {/* Connection Status */}
        <ConnectionStatusComponent status={connectionStatus} />

        <div className="bg-neutral-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold">Radio Scan Demo</h2>
        </div>

        {/* Spectrum Plot */}
        <SpectrumPlot
          spectrumData={spectrumData}
          connectionStatus={connectionStatus}
        />

        <div className="w-full flex gap-4">
          <div className="w-1/2">
            <DistanceMap distance={spectrumData?.distance || 0} />
          </div>
          <div className="w-1/2 flex flex-col gap-4">
            {/* Control Panel */}
            <ControlPanel
              rssiRefInput={rssiRefInput}
              setRssiRefInput={setRssiRefInput}
              updateRSSIRef={updateRSSIRef}
              toggleStreaming={toggleStreaming}
              isStreaming={isStreaming}
            />

            {/* Live Data Display */}
            {spectrumData && (
              <div className="w-full flex flex-col gap-4">
                {/* Live Measurements */}
                <LiveMeasurements
                  spectrumData={spectrumData}
                  distanceHistory={distanceHistory}
                />

                {/* Spectrum Data Info */}
                <SpectrumDataInfo spectrumData={spectrumData} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
