# ClearGlass Air Systems Control — v0.2

A build-ready **Next.js 14 + Tailwind** prototype of the ClearGlass / Artemis
**Air Systems Control Surface** — an aerospace-grade glassmorphism HVAC "digital
twin" console with live, interactive controls for airflow, pressure, temperature,
humidity, filtration, vent geometry, and zone orchestration.

This is a faithful React port of the static reference page shipped on the site at
[`/air-systems-control.html`](../../air-systems-control.html) — refactored into
reusable components and a single source-of-truth state hook.

## Run it

```bash
cd apps/air-control
npm install
npm run dev
# open http://localhost:3000
```

Build a production bundle:

```bash
npm run build && npm start
```

> Requires Node 18.17+ (Next 14). No environment variables are needed — the
> console is entirely client-side and deterministic.

## Structure

```
apps/air-control/
├── app/
│   ├── globals.css          # Tailwind layers + the glassmorphism design system
│   ├── layout.tsx           # root layout, fonts, metadata
│   └── page.tsx             # composes the console from the components below
├── components/
│   ├── GlassPanel.tsx       # reusable frosted-glass panel (header + value + body)
│   ├── TemperatureControl.tsx  # gradient thermal column + range control
│   ├── HumidityBar.tsx      # moisture-balance bar meter + range control
│   └── ZoneSelector.tsx     # selectable active comfort cells
├── hooks/
│   └── useAirSystem.ts      # hardened state, derived metrics, and actions
└── (config: package.json, tsconfig.json, tailwind.config.ts, …)
```

## The state hook

`useAirSystem()` is the single source of truth. Every setter **clamps** its input
to a safe range, derived values (pressure, efficiency, comfort) are memoised, and
the operations log is capped. Actions: `optimize()` (comfort/efficiency target
vector) and `purge()` (storm-purge cycle).

## Notes

- Fully responsive; honours `prefers-reduced-motion`.
- Components are presentational and receive `value` + `onChange`, so they are easy
  to wire to a real backend/websocket later — swap the hook's internals for live
  telemetry without touching the UI.
