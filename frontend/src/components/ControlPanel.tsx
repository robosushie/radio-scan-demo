"use client";

import { DISTANCE_CONFIG } from "@/lib/constants";

interface ControlPanelProps {
  rssiRefInput: string;
  setRssiRefInput: (value: string) => void;
  updateRSSIRef: () => void;
  toggleStreaming: () => void;
  isStreaming: boolean;
}

export function ControlPanel({
  rssiRefInput,
  setRssiRefInput,
  updateRSSIRef,
  toggleStreaming,
  isStreaming,
}: ControlPanelProps) {
  return (
    <div className="bg-neutral-800 rounded-lg p-4 flex flex-col gap-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            RSSI Reference (dBm)
          </label>
          <input
            type="number"
            value={rssiRefInput}
            onChange={(e) => {
              setRssiRefInput(e.target.value);
            }}
            min="-120"
            max="0"
            step="0.1"
            className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={DISTANCE_CONFIG.rssi_ref_default.toString()}
          />
          <div className="text-xs text-neutral-400 mt-1">
            Reference RSSI for distance calculation at 1 meter
          </div>
        </div>
      </div>
      <div className="flex gap-4">
        <button
          onClick={updateRSSIRef}
          className="px-6 py-2 bg-blue-700 hover:bg-blue-900 rounded-md font-medium transition-colors cursor-pointer"
        >
          Update RSSI Reference
        </button>

        <button
          onClick={toggleStreaming}
          className={`px-6 py-2 rounded-md font-medium cursor-pointer transition-colors ${
            isStreaming
              ? "bg-red-700 hover:bg-red-900"
              : "bg-green-700 hover:bg-green-900"
          }`}
        >
          {isStreaming ? "Stop Streaming" : "Start Streaming"}
        </button>
      </div>
    </div>
  );
}
