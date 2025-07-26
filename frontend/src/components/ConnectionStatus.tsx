"use client";

import type { ConnectionStatus } from "@/types/spectrum";

interface ConnectionStatusProps {
  status: ConnectionStatus;
}

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  return (
    <div className="absolute flex w-full justify-center text-center">
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
          status === "connected"
            ? "bg-green-100 text-green-800"
            : status === "connecting"
            ? "bg-yellow-100 text-yellow-800"
            : "bg-red-100 text-red-800"
        }`}
      >
        <div
          className={`w-2 h-2 rounded-full mr-2 ${
            status === "connected"
              ? "bg-green-500"
              : status === "connecting"
              ? "bg-yellow-500"
              : "bg-red-500"
          }`}
        ></div>
        {status === "connected"
          ? "Connected"
          : status === "connecting"
          ? "Connecting..."
          : "Disconnected"}
      </span>
    </div>
  );
}
