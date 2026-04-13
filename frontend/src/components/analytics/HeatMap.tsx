"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { HeatmapPoint } from "@/types";

interface HeatMapProps {
  points: HeatmapPoint[];
}

const INDIA_CENTER: [number, number] = [20.5937, 78.9629];

export default function HeatMap({ points }: HeatMapProps) {
  return (
    <div className="h-[400px] rounded-lg overflow-hidden">
      <MapContainer
        center={INDIA_CENTER}
        zoom={5}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {points.map((point, i) => (
          <CircleMarker
            key={i}
            center={[point.lat, point.lng]}
            radius={6}
            pathOptions={{
              color: "#ef4444",
              fillColor: "#ef4444",
              fillOpacity: 0.6,
            }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-medium capitalize">{point.type.replace("_", " ")}</p>
                <p className="text-muted-foreground">{point.city}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
        {points.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center z-[1000] pointer-events-none">
            <p className="text-sm text-muted-foreground bg-background/80 px-4 py-2 rounded-md">
              No incident data available yet
            </p>
          </div>
        )}
      </MapContainer>
    </div>
  );
}
