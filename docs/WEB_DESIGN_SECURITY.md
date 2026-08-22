# Web Design Page — Security & Threat Model

## Scope

`web-design.html` on branch `feat/web-design-homepage-crystal`.

## Architecture

- Existing static HTML page and shared ClearGlass CSS remain the application boundary.
- The change is CSS-only and scoped by `body:has(.legacy-hero-title)` so other routes retain the existing global theme behavior.
- No new runtime dependency, API, storage mechanism, authentication path, or third-party JavaScript was introduced.
- The visual system now follows the homepage crystal/prism palette: light surfaces, prism gradient, glass panels, restrained ambient motion, and keyboard-visible focus states.

## Threat model

| Asset | Entry point | Threat | Control | Status |
|---|---|---|---|---|
| Page rendering | CSS cascade | Cross-route style regression | Route-specific `:has(.legacy-hero-title)` scope | Implemented |
| User navigation | Keyboard/focus | Focus visibility loss | Explicit `:focus-visible` ring | Implemented |
| Motion/animation | CSS animations | Motion sensitivity / excessive motion | `prefers-reduced-motion` shutdown path | Implemented |
| High-contrast rendering | Forced colors | Loss of semantic contrast | `forced-colors: active` fallback | Implemented |
| Client inputs | URL/query/hash/postMessage | Injection or trust-boundary abuse | Not introduced or processed by this CSS change | Unchanged / verify at runtime |
| Network/API | Fetch/XHR | CSRF, SSRF, token exposure | No new network operation introduced | Unchanged / verify separately |
| Third-party assets | Fonts/CDN | Supply-chain/SRI risk | Existing Google Fonts dependency remains | Open |
| Security headers | HTTP response | CSP/clickjacking/Trusted Types | Not controllable from this CSS-only mutation | Open |

## Residual risk

The repository audit identifies the homepage as having a large inline style block and the site as using multiple navigation systems. The existing design-system documentation also records that the homepage is intentionally a light crystal/prism theme. Those concerns are outside the reversible CSS mutation and require a separate runtime/header hardening pass.

## Rollback

Revert commit `b54fdf34cbb2a6a8c324522c4374f4c26457dd36`, or restore `theme.css` from `main`. No application data or deployment configuration is changed by this commit.
