'use client';

import { Droplets } from 'lucide-react';

export function HumidityBar({ value, onChange }: { value: number; onChange: (val: number) => void }) {
  return <div className="space-y-5"><div className="flex items-center justify-between"><Droplets className="h-8 w-8 text-cyan-300" /><span className="text-5xl font-semibold">{value}%</span></div><div className="grid grid-cols-20 gap-1">{Array.from({ length: 20 }).map((_, i) => <div key={i} className={`h-16 rounded-full ${i < value / 5 ? 'bg-cyan-300/80 shadow-[0_0_12px_rgba(103,232,249,0.4)]' : 'bg-white/10'}`} />)}</div><input type="range" min="20" max="80" value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-cyan-300" /></div>;
}
