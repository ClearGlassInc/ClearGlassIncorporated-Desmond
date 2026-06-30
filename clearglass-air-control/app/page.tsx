'use client';

import { BrainCircuit, Cpu, Network, Sparkles } from 'lucide-react';
import { GlassPanel } from '@/components/GlassPanel';
import { AirflowGauge } from '@/components/AirflowGauge';
import { TemperatureControl } from '@/components/TemperatureControl';
import { ZoneSelector } from '@/components/ZoneSelector';
import { PressureGauge } from '@/components/PressureGauge';
import { HumidityBar } from '@/components/HumidityBar';
import { FiltrationStatus } from '@/components/FiltrationStatus';
import { VentDial } from '@/components/VentDial';
import { useAirSystem } from '@/hooks/useAirSystem';

const baselines = [
  { label: 'SPD/PDLC glass bus', Icon: Cpu },
  { label: 'IBM quantum optimizer', Icon: Sparkles },
  { label: 'Neuralink BCI-ready HMI', Icon: BrainCircuit },
  { label: 'Siemens AI-GLASS telemetry', Icon: Network },
];

export default function AirControlSurface() {
  const air = useAirSystem();
  const { state } = air;
  return (
    <main className="min-h-screen overflow-hidden bg-[#0a0f1e] text-white">
      <div className="fixed inset-0 bg-[radial-gradient(#1a2a4a_0.8px,transparent_1px)] bg-[length:4px_4px] opacity-40" />
      <div className="fixed inset-0 bg-gradient-to-br from-[#0a0f1e] via-[#0f1629] to-[#0a0f1e]" />
      <div className="fixed left-1/3 top-0 h-96 w-96 rounded-full bg-cyan-400/20 blur-[120px]" />
      <div className="relative z-10 mx-auto max-w-[1920px] px-6 py-8 lg:px-8">
        <header className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-xs tracking-[4px] text-cyan-400/70">CLEARGLASS INC • QUANTUM-NEURAL INTERFACE</div>
            <h1 className="text-4xl font-semibold tracking-tighter lg:text-6xl">Air Systems Control Surface</h1>
          </div>
          <div className="rounded-3xl border border-emerald-300/20 bg-emerald-300/10 px-5 py-4 text-sm text-white/70 backdrop-blur-xl">
            <div>STAGING • AURORA PLATFORM</div>
            <div className="text-emerald-300">CONNECTED • 14 ZONES • RISK {air.riskIndex}%</div>
          </div>
        </header>

        <section className="mb-6 grid gap-4 lg:grid-cols-4">
          {baselines.map(({ label, Icon }) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm text-white/65 backdrop-blur-xl"><Icon className="mb-3 h-5 w-5 text-cyan-300" />{label}</div>
          ))}
        </section>

        <section className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <GlassPanel title="AIRFLOW RATE" className="lg:col-span-5"><AirflowGauge value={state.airflow} onChange={air.setAirflow} /></GlassPanel>
          <GlassPanel title="TEMPERATURE" className="lg:col-span-4"><TemperatureControl value={state.temperature} onChange={air.setTemperature} /></GlassPanel>
          <GlassPanel title="ZONE CONTROL" className="lg:col-span-3"><ZoneSelector activeZone={state.activeZone} onZoneChange={air.setActiveZone} /></GlassPanel>
          <GlassPanel title="PRESSURE DELTA" className="lg:col-span-4"><PressureGauge value={state.pressure} onChange={air.setPressure} /></GlassPanel>
          <GlassPanel title="HUMIDITY" className="lg:col-span-4"><HumidityBar value={state.humidity} onChange={air.setHumidity} /></GlassPanel>
          <GlassPanel title="FILTRATION STATUS" className="lg:col-span-4"><FiltrationStatus value={state.filtration} onChange={air.setFiltration} /></GlassPanel>
          <GlassPanel title="VENT VECTORING" className="lg:col-span-4"><VentDial value={state.ventAngle} onChange={air.setVentAngle} /></GlassPanel>
          <GlassPanel title="AIP RECOMMENDATION" className="lg:col-span-8">
            <div className="space-y-4 text-white/70">
              <p className="text-2xl font-semibold text-white">Maintain positive pressure in {state.activeZone}; increase filtration confidence before next occupancy surge.</p>
              <p>Human approval required before Apollo deployment to real SPD/PDLC or HVAC control endpoints. Prototype state is persisted locally for investor demos and architecture reviews.</p>
              <button onClick={() => air.setAutonomousMode(!state.autonomousMode)} className="rounded-full border border-cyan-300/40 bg-cyan-300/10 px-5 py-3 text-cyan-100">{state.autonomousMode ? 'Autonomous assist enabled' : 'Autonomous assist paused'}</button>
            </div>
          </GlassPanel>
        </section>
      </div>
    </main>
  );
}
