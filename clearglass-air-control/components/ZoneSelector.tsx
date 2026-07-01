'use client';

import { motion } from 'framer-motion';
import { zones, ZoneId } from '@/lib/types';

interface Props { activeZone: ZoneId; onZoneChange: (zone: ZoneId) => void; }

export function ZoneSelector({ activeZone, onZoneChange }: Props) {
  return <div className="grid gap-3">{zones.map((zone, index) => { const active = activeZone === zone; return <motion.button key={zone} type="button" onClick={() => onZoneChange(zone)} whileTap={{ scale: 0.98 }} className={`rounded-2xl border px-4 py-3 text-left transition ${active ? 'border-cyan-300/60 bg-cyan-300/15 text-cyan-100 shadow-[0_0_24px_rgba(34,211,238,0.16)]' : 'border-white/10 bg-white/5 text-white/60 hover:border-white/25'}`}><div className="flex items-center justify-between"><span>{zone}</span><span className="text-xs">{12 + index * 3} nodes</span></div></motion.button>; })}</div>;
}
