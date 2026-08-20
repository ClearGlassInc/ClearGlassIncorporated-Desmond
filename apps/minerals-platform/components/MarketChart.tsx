"use client";

import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";

export default function MarketChart() {
  const host = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState("Loading market series…");

  useEffect(() => {
    if (!host.current) return;
    const chart = echarts.init(host.current, undefined, { renderer: "canvas" });
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch("/api/v1/markets?pageSize=120", { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json() as { data?: { items?: Array<{ timestamp: string; value: string | number; mineral?: { name?: string }; benchmark?: string }> } };
        const rows = payload.data?.items ?? [];
        const sorted = [...rows].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        if (cancelled) return;
        chart.setOption({
          animation: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
          backgroundColor: "transparent",
          textStyle: { color: "#94a3b8" },
          tooltip: { trigger: "axis", backgroundColor: "rgba(6,10,18,.96)", borderColor: "rgba(148,163,184,.2)", textStyle: { color: "#e2e8f0" } },
          grid: { left: 52, right: 20, top: 26, bottom: 42 },
          xAxis: { type: "category", data: sorted.map((r) => new Date(r.timestamp).toLocaleDateString()), axisLine: { lineStyle: { color: "#243244" } }, axisLabel: { color: "#64748b", hideOverlap: true } },
          yAxis: { type: "value", scale: true, axisLine: { show: false }, splitLine: { lineStyle: { color: "rgba(100,116,139,.14)" } }, axisLabel: { color: "#64748b" } },
          series: [{ type: "line", data: sorted.map((r) => Number(r.value)), smooth: true, showSymbol: false, lineStyle: { width: 2, color: "#60a5fa" }, areaStyle: { color: "rgba(96,165,250,.08)" } }],
          graphic: sorted.length ? [] : [{ type: "text", left: "center", top: "middle", style: { text: "NO LICENSED MARKET SERIES LOADED", fill: "#64748b", font: "12px monospace" } }]
        });
        setStatus(sorted.length ? `${sorted.length} observations · source status retained per record` : "No licensed market observations loaded; no synthetic price line shown.");
      } catch (error) {
        setStatus(`Market data unavailable: ${error instanceof Error ? error.message : String(error)}`);
        chart.setOption({ graphic: [{ type: "text", left: "center", top: "middle", style: { text: "MARKET FEED UNAVAILABLE", fill: "#64748b", font: "12px monospace" } }] });
      }
    }
    void load();
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => { cancelled = true; window.removeEventListener("resize", resize); chart.dispose(); };
  }, []);

  return <div><div ref={host} className="cg-chart" aria-label="Mineral market chart" /><p className="px-5 pb-4 text-xs text-slate-500" aria-live="polite">{status}</p></div>;
}
