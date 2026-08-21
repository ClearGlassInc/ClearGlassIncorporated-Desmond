import Link from 'next/link';

const panels = [
  ['Authorized Target Setup', 'Define owner, approved ports, purpose and expiry. Scope validation fails closed.'],
  ['FTP Service Audit', 'Banner, TLS/FTPS, anonymous configuration, passive-port observation and timeout checks only.'],
  ['Authentication Simulation', 'Local Docker fixture only. No real passwords or password lists are transmitted.'],
  ['Defensive Claim', 'Audit completed · Risk identified · Recommended remediation · No credentials obtained · No exploitation performed'],
  ['Reports', 'JSON, CSV and PDF report contracts with authorization statement and redaction guarantees.'],
  ['Developer Console', 'lab:start · lab:reset · audit:ftp · simulation:run · report:generate'],
];

export default function Dashboard() {
  return <main className="min-h-screen bg-[#05070b] text-cyan-100 p-6 font-mono">
    <header className="max-w-7xl mx-auto border border-cyan-400/30 rounded-2xl p-6 bg-white/[.03] backdrop-blur-xl shadow-[0_0_50px_rgba(34,211,238,.08)]">
      <div className="flex justify-between gap-4 flex-wrap"><div><p className="text-xs tracking-[.35em] text-cyan-300">CLEARGLASS // DEFENSIVE SECURITY LAB</p><h1 className="text-4xl font-bold mt-2">HYDRAGUARD LAB</h1><p className="text-sm text-slate-400 mt-2">Authorization-first FTP security assessment · simulation mode ON</p></div><div className="rounded-lg border border-emerald-400/40 px-4 py-2 text-emerald-300 text-sm">SAFE MODE: ACTIVE</div></div>
    </header>
    <section className="max-w-7xl mx-auto grid md:grid-cols-4 gap-4 mt-5">{[['CPU','18%'],['RAM','42%'],['ACTIVE JOBS','0'],['BLOCKED REQUESTS','0']].map(([k,v])=><div key={k} className="rounded-xl border border-cyan-400/20 bg-white/[.025] p-5"><div className="text-xs text-slate-500">{k}</div><div className="text-3xl mt-2 text-cyan-200">{v}</div></div>)}</section>
    <section className="max-w-7xl mx-auto grid lg:grid-cols-3 gap-4 mt-5">{panels.map(([title, body])=><article key={title} className="rounded-xl border border-cyan-400/20 bg-white/[.025] p-5 hover:border-cyan-300/50 transition"><h2 className="text-lg text-cyan-200">{title}</h2><p className="text-sm text-slate-400 mt-3 leading-6">{body}</p></article>)}</section>
    <section className="max-w-7xl mx-auto mt-5 rounded-xl border border-fuchsia-400/20 bg-black/40 p-5"><div className="flex justify-between"><h2 className="text-fuchsia-200">NEON TERMINAL</h2><Link href="/targets" className="text-xs text-cyan-300">OPEN TARGET SETUP →</Link></div><pre className="mt-4 text-xs text-slate-400">$ hydraguard status\n[SAFE] simulation_mode=true\n[POLICY] public_targets=DENY\n[POLICY] metadata=DENY\n[POLICY] credentials=NEVER_ACCEPT\n[LAB] awaiting authorized engagement...</pre></section>
    <footer className="max-w-7xl mx-auto mt-5 text-xs text-amber-300/80 border border-amber-400/20 rounded-xl p-4">WARNING: Results are valid only for systems for which the operator has explicit authorization. HydraGuard Lab is designed to fail closed outside approved scope.</footer>
  </main>;
}
