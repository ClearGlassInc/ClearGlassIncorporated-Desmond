'use client';

import { motion } from 'framer-motion';

export function TemperatureControl({ value, onChange }: { value: number; onChange: (val: number) => void }) {
  const width = ((value - 16) / 12) * 100;
  return <div className="space-y-6"><div className="flex items-baseline justify-between"><div className="text-[72px] font-semibold tabular-nums tracking-[-4px]">{value.toFixed(1)}</div><div className="text-2xl text-white/60">°C</div></div><input type="range" min="16" max="28" step="0.1" value={value} onChange={(e) => onChange(parseFloat(e.target.value))} className="w-full accent-cyan-400" /><div className="h-2 overflow-hidden rounded-full bg-white/10"><motion.div className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400" animate={{ width: `${width}%` }} transition={{ type: 'spring', bounce: 0.2 }} /></div></div>;
}
