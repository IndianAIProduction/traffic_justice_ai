"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { matchIndianState } from "@/lib/constants";

interface LocationResult {
  detectedState: string | null;
  city: string | null;
  detecting: boolean;
  error: string | null;
  detect: () => void;
}

interface BigDataCloudResponse {
  principalSubdivision: string;
  city: string;
  locality: string;
  countryCode: string;
  countryName: string;
}

async function reverseGeocode(lat: number, lng: number): Promise<BigDataCloudResponse> {
  const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Reverse geocoding failed");
  return res.json();
}

export function useAutoLocation(autoDetectOnMount = true): LocationResult {
  const [detectedState, setDetectedState] = useState<string | null>(null);
  const [city, setCity] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasFired = useRef(false);

  const detect = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported by your browser");
      return;
    }

    setDetecting(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const geo = await reverseGeocode(latitude, longitude);

          if (geo.countryCode !== "IN") {
            setError("Location detected outside India");
            setDetectedState(null);
            setCity(null);
            setDetecting(false);
            return;
          }

          const matched = matchIndianState(geo.principalSubdivision);
          setDetectedState(matched);
          setCity(geo.city || geo.locality || null);

          if (!matched) {
            setError(`Could not match state: ${geo.principalSubdivision}`);
          }
        } catch {
          setError("Failed to determine location");
          setDetectedState(null);
          setCity(null);
        } finally {
          setDetecting(false);
        }
      },
      (posError) => {
        setDetecting(false);
        switch (posError.code) {
          case posError.PERMISSION_DENIED:
            setError("Location permission denied");
            break;
          case posError.POSITION_UNAVAILABLE:
            setError("Location unavailable");
            break;
          case posError.TIMEOUT:
            setError("Location request timed out");
            break;
          default:
            setError("Failed to get location");
        }
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
    );
  }, []);

  useEffect(() => {
    if (autoDetectOnMount && !hasFired.current) {
      hasFired.current = true;
      detect();
    }
  }, [autoDetectOnMount, detect]);

  return { detectedState, city, detecting, error, detect };
}
