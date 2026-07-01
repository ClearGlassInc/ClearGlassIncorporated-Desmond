'use client';

import { motion } from 'framer-motion';

interface Props { value: number; onChange: (val: number) => void; }

export function PressureGauge({ value, onChange }: Props) {
  const width = Math.max(0, Math.min(100, ((value - 95) / 15) * 100));
  return (
    <div className="space-y-4">
      <div className="flex items-baseline gap-2"><div className="text-6xl font-semibold tabular-nums tracking-[-3px]">{value.toFixed(1)}</div><div className="text-xl text-white/60">kPa</div></div>
      <div className="relative h-2 rounded-full bg-white/10"><motion.div className="absolute left-0 top-0 h-2 rounded-full bg-gradient-to-r from-blue-400 to-cyan-400" animate={{ width: `${width}%` }} transition={{ type: 'spring', bounce: 0.2 }} /></div>
      <input type="range" min="95" max="110" step="0.1" value={value} onChange={(e) => onChange(parseFloat(e.target.value))} className="w-full accent-blue-400" />
    </div>
  );
}
