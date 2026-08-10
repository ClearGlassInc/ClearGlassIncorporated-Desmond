# ClearGlass Cinematic Motion Runbook

## Architecture boundary

The public homepage remains the static GitHub Pages `index.html`. The repository also contains independent Next.js applications under `apps/` and other product directories. The cinematic homepage layer must remain progressive enhancement and must not require a Next.js migration, server runtime, WebGPU support, or an animation CDN.

Primary motion assets:

- `assets/css/cinematic-motion.css`
- `assets/js/cinematic-motion.js`
- loaded by `platform.js`

## Quality gates

Run:

```bash
npm ci
npm run check:motion
```

`check:motion` runs the root TypeScript typecheck, existing Node tests, root TypeScript build, and the cinematic motion validator. The validator enforces JavaScript syntax, raw/gzip size budgets, all eight capability nodes, reduced-motion and constrained-device fallbacks, offscreen/background pausing, frame-rate caps, Core Web Vitals observers, and the emergency rollback switch.

The existing Lighthouse CI gate remains authoritative for browser-level budgets:

- Performance score: >= 0.95
- Accessibility score: >= 0.95
- SEO score: 1.00
- LCP: <= 2500 ms
- CLS: <= 0.10
- INP: warning threshold <= 200 ms

## Browser-local measurements

The motion runtime exposes no network telemetry. In DevTools:

```js
getClearGlassMotionMetrics()
```

Returns the current local snapshot for LCP, CLS, INP interaction candidate, measured motion FPS, long-task count, reduced-motion state, low-power state, and configured animation target FPS.

The runtime also dispatches `cg:motion-metrics` events locally after the initial observation window and when the page is hidden/unloaded.

## Performance behavior

- Normal continuous updates are capped at 24 FPS.
- Save-Data or <=4 GB reported device memory selects the low-power path and removes continuous procedural updates.
- Hero motion pauses when offscreen or when the browser tab is backgrounded.
- `prefers-reduced-motion: reduce` makes the interface static while preserving all content and controls.
- Static HTML/SVG remains authoritative if JavaScript, PerformanceObserver, IntersectionObserver, or WebGPU is unavailable.

## Emergency rollback

### Per-request kill switch

Append this query parameter to the homepage:

```text
?cg_motion=off
```

The cinematic runtime exits before applying the `cg-cinematic-ready` class.

### Persistent browser kill switch

In DevTools:

```js
localStorage.setItem("cg-motion", "off");
location.reload();
```

Restore motion with:

```js
localStorage.removeItem("cg-motion");
location.reload();
```

### Source rollback

If a production regression is confirmed, revert the PR/merge commit that introduced the regression rather than force-resetting `main`. The pre-quality-gate cinematic baseline is commit `d8715df1c18dbc9865294191f05b995ebd23c38e`.
