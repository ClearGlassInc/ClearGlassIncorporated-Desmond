'use client';

import { motion } from 'framer-motion';

interface Props { value: number; onChange: (val: number) => void; }

export function HumidityBar({ value, onChange }: Props) {
  const activeBars = Math.round(value / 5);
  return (
    <div className="space-y-5">
      <div className="flex items-baseline justify-between"><div className="text-5xl font-semibold tabular-nums tracking-[-2px]">{value}</div><div className="text-xl text-white/60">%RH</div></div>
      <div className="grid grid-cols-20 gap-1">{Array.from({ length: 20 }).map((_, index) => <motion.div key={index} className={`h-16 rounded-full ${index < activeBars ? 'bg-cyan-300/80 shadow-[0_0_12px_rgba(103,232,249,0.4)]' : 'bg-white/10'}`} animate={{ opacity: index < activeBars ? 1 : 0.35 }} />)}</div>
      <input type="range" min="20" max="80" value={value} onChange={(e) => onChange(parseInt(e.target.value, 10))} className="w-full accent-cyan-300" />
    </div>
  );
}
