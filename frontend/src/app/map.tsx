"use client";
import React from "react";

import { MapContainer, TileLayer, Circle, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default markers in react-leaflet
import L from "leaflet";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

interface DistanceMapProps {
  distance: number; // Distance in meters
}

const DistanceMap: React.FC<DistanceMapProps> = ({ distance }) => {
  // Fixed coordinates (San Francisco as example)
  const fixedPosition: [number, number] = [37.7749, -122.4194];

  return (
    <div className="w-full h-full min-h-96 rounded-lg overflow-hidden shadow-lg">
      <MapContainer
        center={fixedPosition}
        zoom={13}
        style={{ height: "100%", width: "100%" }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Center marker */}
        <Marker position={fixedPosition}>
          <Popup>
            Center Point
            <br />
            Lat: {fixedPosition[0]}, Lng: {fixedPosition[1]}
          </Popup>
        </Marker>

        {/* Distance circle */}
        <Circle
          center={fixedPosition}
          radius={distance}
          pathOptions={{
            color: "blue",
            fillColor: "lightblue",
            fillOpacity: 0.2,
            weight: 2,
          }}
        >
          <Popup>
            Radius: {distance.toLocaleString()} meters
            <br />({(distance / 1000).toFixed(2)} km)
          </Popup>
        </Circle>
      </MapContainer>
    </div>
  );
};

export default DistanceMap;
