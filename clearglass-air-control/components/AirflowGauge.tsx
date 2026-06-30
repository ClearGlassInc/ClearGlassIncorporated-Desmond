'use client';

import { Wind } from 'lucide-react';
import { RingGauge } from './RingGauge';

export function AirflowGauge({ value, onChange }: { value: number; onChange: (val: number) => void }) {
  return <div className="space-y-5"><RingGauge value={value} label="Quantum-optimized supply velocity" unit="CFM%" gradientId="airflow" /><label className="flex items-center gap-3 text-white/60"><Wind className="h-4 w-4 text-cyan-300" /> Manual override</label><input type="range" min="0" max="100" value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-cyan-400" /></div>;
}
