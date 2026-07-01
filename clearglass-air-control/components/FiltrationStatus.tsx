'use client';

import { motion } from 'framer-motion';

interface Props { value: number; onChange: (val: number) => void; }

export function FiltrationStatus({ value, onChange }: Props) {
  const status = value > 90 ? 'OPTIMAL' : value > 75 ? 'GOOD' : 'ATTENTION';
  return (
    <div>
      <div className="mb-3 flex items-center justify-between"><div className="text-5xl font-semibold tabular-nums tracking-[-2px]">{value}</div><div className="rounded-full bg-white/10 px-3 py-1 text-sm text-white/70">{status}</div></div>
      <div className="mb-4 h-2.5 overflow-hidden rounded-full bg-white/10"><motion.div className="h-full bg-emerald-400" animate={{ width: `${value}%` }} transition={{ type: 'spring' }} /></div>
      <input type="range" min="60" max="100" value={value} onChange={(e) => onChange(parseInt(e.target.value, 10))} className="w-full accent-emerald-400" />
    </div>
  );
}
