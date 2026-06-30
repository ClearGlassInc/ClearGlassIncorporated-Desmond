'use client';

import { motion } from 'framer-motion';
import { RotateCcw } from 'lucide-react';

export function VentDial({ value, onChange }: { value: number; onChange: (val: number) => void }) {
  return <div className="space-y-6"><div className="relative mx-auto flex h-48 w-48 items-center justify-center rounded-full border border-white/15 bg-white/5"><motion.div className="absolute h-3 w-24 origin-left rounded-full bg-gradient-to-r from-cyan-300 to-emerald-300" style={{ left: '50%' }} animate={{ rotate: value - 90 }} /><div className="z-10 rounded-full bg-[#0a0f1e] p-5 text-center"><RotateCcw className="mx-auto h-5 w-5 text-cyan-300" /><div className="text-3xl font-semibold">{value}°</div></div></div><input type="range" min="0" max="90" value={value} onChange={(e) => onChange(Number(e.target.value))} className="w-full accent-cyan-400" /></div>;
}
