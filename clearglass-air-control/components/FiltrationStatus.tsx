'use client';

import { ShieldCheck } from 'lucide-react';
import { RingGauge } from './RingGauge';

export function FiltrationStatus({ value, onChange }: { value: number; onChange: (val: number) => void }) {
  return <div className="space-y-4"><RingGauge value={value} label="HEPA + PDLC particulate confidence" unit="PURE" gradientId="filter" /><div className="flex items-center justify-between rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4 text-emerald-200"><ShieldCheck className="h-5 w-5" /><span>Bio-safe circulation nominal</span></div><input type="range" min="70" max="100" value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-emerald-400" /></div>;
}
