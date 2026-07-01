'use client';

import { motion } from 'framer-motion';

interface Props { value: number; onChange: (val: number) => void; }

export function AirflowGauge({ value, onChange }: Props) {
  return (
    <div>
      <div className="mb-4 flex items-baseline justify-between"><div className="text-6xl font-semibold tabular-nums tracking-[-3px]">{value}</div><div className="text-xl text-white/60">CFM</div></div>
      <input type="range" min="20" max="120" value={value} onChange={(e) => onChange(parseInt(e.target.value, 10))} className="mb-6 w-full accent-cyan-400" />
      <div className="relative h-3 overflow-hidden rounded-full bg-white/10"><motion.div className="absolute h-full bg-gradient-to-r from-cyan-400 via-white to-cyan-400" animate={{ x: ['-100%', '300%'] }} transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }} style={{ width: `${value}%` }} /></div>
    </div>
  );
}
