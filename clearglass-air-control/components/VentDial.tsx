'use client';

import { motion } from 'framer-motion';

interface Props { value: number; onChange: (val: number) => void; }

export function VentDial({ value, onChange }: Props) {
  return (
    <div className="flex flex-col items-center">
      <div className="relative h-32 w-32"><svg viewBox="0 0 100 100" className="h-full w-full -rotate-90"><circle cx="50" cy="50" r="42" fill="none" stroke="#ffffff20" strokeWidth="8" /><motion.circle cx="50" cy="50" r="42" fill="none" stroke="#22d3ee" strokeWidth="8" strokeDasharray="264" strokeDashoffset={264 - (value / 90) * 264} strokeLinecap="round" /></svg><div className="absolute inset-0 flex items-center justify-center font-mono text-3xl tracking-[-2px]" style={{ transform: `rotate(${value * 4}deg)` }}>{value}°</div></div>
      <input type="range" min="0" max="90" value={value} onChange={(e) => onChange(parseInt(e.target.value, 10))} className="mt-4 w-40 accent-cyan-400" />
    </div>
  );
}
