"use client";

import { useAirSystem } from "../hooks/useAirSystem";
import GlassPanel from "../components/GlassPanel";
import TemperatureControl from "../components/TemperatureControl";
import HumidityBar from "../components/HumidityBar";
import ZoneSelector from "../components/ZoneSelector";

export default function Page() {
  const { state, logs, derived, zones, setNumber, setZone, optimize, purge } =
    useAirSystem();

  return (
    <main className="stage">
      <div className="particles" />
      <div className="beam" />
      <div className="shell">
        <section className="hero">
          <div>
            <div className="eyebrow">
              <span className="live-dot" /> ClearGlassInc Artemis · Air Systems
            </div>
            <h1>Frosted-glass atmospheric command surface.</h1>
            <p>
              A live, premium cockpit-style console for airflow, pressure, thermal
              balance, humidity, filtration, vent geometry, and zone orchestration.
            </p>
          </div>
          <GlassPanel
            className="mission-card"
            kicker="Mission State"
            title="Building / Aerospace HVAC Digital Twin"
          >
            <div className="status-grid" style={{ marginTop: 16 }}>
              <div className="status">
                <b>{derived.efficiency}%</b>
                <span>efficiency</span>
              </div>
              <div className="status">
                <b>{derived.comfort}</b>
                <span>comfort</span>
              </div>
              <div className="status">
                <b>12ms</b>
                <span>UI loop</span>
              </div>
            </div>
          </GlassPanel>
        </section>

        <section className="grid" aria-label="Interactive air systems controls">
          <GlassPanel wide kicker="Airflow Rate" title="Animated flow gauge" value={state.airflow} unit="%">
            <svg className="gauge" viewBox="0 0 520 220" role="img" aria-label="Airflow gauge">
              <defs>
                <linearGradient id="grad" x1="0" x2="1">
                  <stop stopColor="#38d9ff" />
                  <stop offset=".55" stopColor="#60a5fa" />
                  <stop offset="1" stopColor="#3ff6a8" />
                </linearGradient>
              </defs>
              <path className="track" d="M70 175 A190 190 0 0 1 450 175" />
              <path
                className="progress"
                pathLength={100}
                strokeDasharray={`${state.airflow} 100`}
                d="M70 175 A190 190 0 0 1 450 175"
              />
              <path className="flowline" d="M95 140 C175 85 240 205 326 118 S442 110 486 74" />
              <path
                className="flowline"
                style={{ animationDelay: "-1.8s" }}
                d="M35 88 C130 38 195 132 270 78 S398 54 482 128"
              />
            </svg>
            <div className="control">
              <input
                className="range"
                type="range"
                min={20}
                max={100}
                value={state.airflow}
                aria-label="Airflow (%)"
                onChange={(e) => setNumber("airflow", Number(e.target.value))}
              />
              <div className="metric-row">
                <span>quiet economy</span>
                <span>storm purge</span>
              </div>
            </div>
          </GlassPanel>

          <GlassPanel kicker="Pressure" title="Pulsing indicator" value={derived.pressure} unit=" kPa">
            <div className="pressure-orb">
              <div className="mono">{derived.pressureState}</div>
            </div>
          </GlassPanel>

          <GlassPanel kicker="Temperature" title="Gradient thermal column" value={state.temp.toFixed(1)} unit="°C">
            <TemperatureControl value={state.temp} onChange={(v) => setNumber("temp", v)} />
          </GlassPanel>

          <GlassPanel kicker="Humidity" title="Moisture balance" value={state.humidity} unit="%">
            <HumidityBar value={state.humidity} onChange={(v) => setNumber("humidity", v)} />
          </GlassPanel>

          <GlassPanel kicker="Filtration" title="HEPA / carbon stack" value={state.filter} unit="%">
            <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <div className="filter-icon">⌬</div>
              <div style={{ flex: 1 }}>
                <div className="bar">
                  <i style={{ width: `${state.filter}%` }} />
                </div>
                <p style={{ color: "var(--muted)" }}>
                  Ionization field stable. Replace cartridge below 25%.
                </p>
              </div>
            </div>
          </GlassPanel>

          <GlassPanel kicker="Vent Position" title="Vector dial" value={state.vent} unit="°">
            <div className="dial-wrap">
              <div className="dial">
                <div
                  className="needle"
                  style={{ transform: `rotate(${state.vent}deg) translateY(-2px)` }}
                />
              </div>
              <input
                className="range"
                type="range"
                min={-90}
                max={90}
                value={state.vent}
                aria-label="Vent position (°)"
                onChange={(e) => setNumber("vent", Number(e.target.value))}
              />
            </div>
          </GlassPanel>

          <GlassPanel wide kicker="Zone Control" title="Selectable active comfort cells">
            <div className="actions" style={{ marginBottom: 14 }}>
              <button type="button" className="action primary" onClick={optimize}>
                AUTO OPTIMIZE
              </button>
              <button type="button" className="action" onClick={purge}>
                PURGE CYCLE
              </button>
            </div>
            <ZoneSelector zones={zones} active={state.zone} onSelect={setZone} />
          </GlassPanel>

          <GlassPanel kicker="Operations Log" title="Real-time control trace">
            <div className="log">
              {logs.length === 0 ? (
                <p>Atmospheric digital twin synchronized · glass control surface online</p>
              ) : (
                logs.map((l) => (
                  <p key={l.id}>
                    {l.t} · {l.msg}
                  </p>
                ))
              )}
            </div>
          </GlassPanel>
        </section>
      </div>
    </main>
  );
}
