'use client';

import { Gauge } from 'lucide-react';

export function PressureGauge({ value, onChange }: { value: number; onChange: (val: number) => void }) {
  const pct = ((value - 0.5) / 4) * 100;
  return <div className="space-y-6"><div className="flex items-end justify-between"><Gauge className="h-8 w-8 text-emerald-300" /><div className="text-right"><div className="text-6xl font-semibold tracking-[-3px]">{value.toFixed(1)}</div><div className="text-white/50">Pa differential</div></div></div><div className="h-3 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-emerald-400 to-amber-300" style={{ width: `${pct}%` }} /></div><input type="range" min="0.5" max="4.5" step="0.1" value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-emerald-400" /></div>;
}
