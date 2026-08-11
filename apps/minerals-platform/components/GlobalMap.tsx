"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { type GeoJSONSource, type Map } from "maplibre-gl";

type FeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Point, Record<string, unknown>>;
const EMPTY: FeatureCollection = { type: "FeatureCollection", features: [] };

export default function GlobalMap() {
  const host = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const [status, setStatus] = useState("Loading source-grounded features…");

  useEffect(() => {
    if (!host.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: host.current,
      center: [0, 18],
      zoom: 1.15,
      attributionControl: false,
      style: {
        version: 8,
        sources: {},
        layers: [{ id: "background", type: "background", paint: { "background-color": "#07101a" } }]
      }
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");
    map.on("load", async () => {
      map.addSource("minerals-features", { type: "geojson", data: EMPTY, cluster: true, clusterRadius: 46, clusterMaxZoom: 8 });
      map.addLayer({ id: "clusters", type: "circle", source: "minerals-features", filter: ["has", "point_count"], paint: { "circle-color": "#60a5fa", "circle-radius": ["step", ["get", "point_count"], 14, 25, 19, 100, 25], "circle-opacity": 0.72, "circle-stroke-color": "#dbeafe", "circle-stroke-width": 1 } });
      map.addLayer({ id: "entities", type: "circle", source: "minerals-features", filter: ["!", ["has", "point_count"]], paint: { "circle-color": ["match", ["get", "entityType"], "mine", "#a78bfa", "project", "#60a5fa", "facility", "#34d399", "logistics", "#f59e0b", "#f472b6"], "circle-radius": 6, "circle-stroke-color": "#f8fafc", "circle-stroke-width": 1, "circle-opacity": 0.85 } });
      try {
        const response = await fetch("/api/v1/map/features?type=all&limit=2500", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json() as { data?: FeatureCollection };
        const data = payload.data ?? EMPTY;
        (map.getSource("minerals-features") as GeoJSONSource).setData(data);
        setStatus(data.features.length ? `${data.features.length} source-grounded geospatial records` : "No geospatial records loaded. Empty state preserved.");
      } catch (error) {
        setStatus(`Map data unavailable: ${error instanceof Error ? error.message : String(error)}`);
      }
    });
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  return <div><div ref={host} className="cg-map" aria-label="Critical minerals geospatial map" /><p className="px-5 pb-4 text-xs text-slate-500" aria-live="polite">{status}</p></div>;
}
