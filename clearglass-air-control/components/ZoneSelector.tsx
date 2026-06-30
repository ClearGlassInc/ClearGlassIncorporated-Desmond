'use client';

import { zones, ZoneId } from '@/lib/types';

export function ZoneSelector({ activeZone, onZoneChange }: { activeZone: ZoneId; onZoneChange: (zone: ZoneId) => void }) {
  return <div className="grid gap-3">{zones.map((zone, i) => <button key={zone} onClick={() => onZoneChange(zone)} className={`rounded-2xl border px-4 py-3 text-left transition ${activeZone === zone ? 'border-cyan-300/60 bg-cyan-300/15 text-cyan-100 shadow-[0_0_24px_rgba(34,211,238,0.16)]' : 'border-white/10 bg-white/5 text-white/60 hover:border-white/25'}`}><div className="flex items-center justify-between"><span>{zone}</span><span className="text-xs">{12 + i * 3} nodes</span></div></button>)}</div>;
}
