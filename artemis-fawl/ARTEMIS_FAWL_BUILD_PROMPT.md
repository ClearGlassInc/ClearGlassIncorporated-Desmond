# ARTEMIS FAWL — Canonical Brand-Clean Build Prompt

**Organization:** ClearGlass Inc.  
**Product:** ARTEMIS FAWL  
**Mission:** Brand-clean build  
**Status:** READY  
**Purpose:** Canonical engineering prompt for a governed, defensive public-source intelligence and situational-awareness platform.

> This document defines the target-state build specification. It does not itself assert that every listed capability is deployed, connected to live data, licensed, or production-verified.

```text
You are a senior full-stack engineer, geospatial systems architect, cybersecurity analyst, and product designer working for ClearGlass Inc.

Build a production-ready web application called “ARTEMIS FAWL” — ClearGlass Inc.’s governed, defensive public-source intelligence and situational-awareness platform.

Use attached or supplied reference screenshots only as visual inspiration. Do not copy third-party branding, names, logos, text, proprietary interface elements, or product identity.

## Brand requirements

- The only product and organization names permitted in the interface are ARTEMIS FAWL and ClearGlass Inc.
- Remove all unrelated names, fictional organizations, third-party product names, and placeholder branding from UI labels, metadata, demo records, documentation, seed data, comments, and test fixtures.
- Use ARTEMIS FAWL as the product name.
- Use ClearGlass Inc. as the organization name.
- Use neutral navigation labels such as Console, Wall, Brief, Hazards, Transit, Markets, Recon, Sources, and Settings.
- Third-party data providers may appear only in dedicated source-attribution fields when legally required.
- Do not use PROVENANCE or any unrelated product name as a product identity.

## Mission and lawful scope

Aggregate, normalize, visualize, and preserve provenance for lawful, publicly available data used for:

- Defensive monitoring.
- Infrastructure awareness.
- Emergency awareness.
- Cybersecurity research.
- Public-source intelligence education.
- Operational risk analysis.

Supported data categories may include:

- Public traffic cameras and transportation feeds.
- Earthquakes and seismic activity.
- Wildfires and public satellite fire detections.
- Weather hazards and disaster alerts.
- Public internet-outage reports.
- Public transit disruptions.
- Lawful public maritime and aviation data.
- Public news and geopolitical events.
- Public markets and economic indicators.
- Public satellite, webcam, and sensor metadata.

Never include:

- Private cameras.
- Restricted or credentialed feeds.
- Facial recognition.
- Person tracking.
- License-plate recognition.
- Doxxing.
- Stalking functionality.
- Weapon targeting.
- Unauthorized access.
- Credential bypassing.
- Instructions for evading access controls.

Apply data minimization and avoid exposing unnecessarily precise coordinates for sensitive infrastructure.

Display this disclaimer prominently:

“ARTEMIS FAWL provides situational awareness and research support. Verify critical information with official authorities and original sources.”

## Product vision

Create a dark, cinematic, high-trust ClearGlass Inc. command-center interface:

- Near-black background.
- Charcoal panels.
- Amber primary accent.
- Cyan and blue map markers.
- Red severity indicators.
- Compact monospace typography for timestamps and telemetry.
- High-density but readable information hierarchy.
- Responsive desktop, tablet, and mobile layouts.
- Futuristic cybersecurity aesthetics without sacrificing accessibility.
- No excessive glow, distracting animation, or decorative content that reduces operational clarity.

## Main application areas

### 1. Global navigation

Include:

- ARTEMIS FAWL brand mark.
- ClearGlass Inc. organization label.
- Current UTC clock.
- Console.
- Wall.
- Brief.
- Hazards.
- Transit.
- Markets.
- Recon.
- Sources.
- Settings.
- Theme controls.
- Support.
- Source controls.
- Keyboard-shortcut help.
- System-status indicators.
- Account and configuration controls.

### 2. Brief dashboard

Include:

- Feed-health summary.
- Live, delayed, offline, and authorization-required counters.
- Breaking-event ticker.
- “What’s Abnormal” event feed.
- Severity bars.
- Event category labels.
- Relative and exact UTC timestamps.
- Region and source metadata.
- Expandable event details.
- Stale-data indicators.
- Source-confidence indicators.
- Clear distinction between verified data, normalized data, heuristics, stale information, and unverified information.

### 3. Interactive map

Use MapLibre GL JS or Leaflet with an appropriately licensed open map provider.

Map requirements:

- Dark basemap.
- Clustered markers.
- Marker colors based on severity and category.
- Layer toggles.
- Hazard layer.
- Earthquake layer.
- Wildfire layer.
- Internet-outage layer.
- Transit layer.
- Weather layer.
- Public traffic layer.
- Search and geocoding.
- Bounding-box filtering.
- Timeline playback.
- Marker detail drawers.
- Performance-conscious clustering.
- Accessible keyboard navigation.
- Responsive mobile behavior.
- No unnecessary precision beyond what the original public source intentionally provides.

### 4. Source explorer

Display:

- Source name.
- Source category.
- Geographic coverage.
- Source URL.
- Last successful poll.
- Last failure.
- Current status.
- Update frequency.
- Attribution.
- License.
- Parser version.
- Data freshness.
- Error count.
- Retry controls.
- Enable/disable state.
- Data-quality notes.
- Provenance metadata.

Begin with mock source records, but design the schema for safe future integration of real public feeds.

### 5. Event detail panel

When a user selects an event, display:

- Event title.
- Severity.
- Category.
- Location.
- Coordinates where appropriate.
- First observed time.
- Last updated time.
- Source.
- Confidence.
- Evidence links.
- Sanitized source preview.
- Related events.
- Data freshness.
- Provenance chain.
- Safe link to the original source.

Clearly distinguish:

- Verified source data.
- System-generated normalization.
- Heuristics.
- User-configured thresholds.
- Unverified information.
- Stale information.
- Conflicting reports.

### 6. Wall mode

Create a configurable monitoring wall with widgets for:

- World map.
- Active hazards.
- Public internet outages.
- Earthquake stream.
- Public traffic-camera status.
- News ticker.
- Feed health.
- Timeline.
- System diagnostics.

Allow users to:

- Add widgets.
- Remove widgets.
- Resize widgets.
- Reorder widgets.
- Save layouts locally.
- Reset to the default layout.

### 7. Search and filtering

Support:

- Global search.
- Search by place.
- Search by source.
- Search by event type.
- Search by region.
- Search by date.
- Severity filtering.
- Category filtering.
- Source filtering.
- Freshness filtering.
- “Only abnormal” mode.
- URL query-state persistence.
- Debounced input.
- Clear-filter controls.

## Technical architecture

Use:

- Next.js with TypeScript.
- App Router.
- React.
- Tailwind CSS.
- shadcn/ui or an equivalent accessible component system.
- MapLibre GL JS or Leaflet.
- PostgreSQL with Prisma.
- Redis where justified.
- Zod for runtime validation.
- TanStack Query.
- Vitest.
- Playwright.
- Docker.
- GitHub Actions.

Use this structure:

app/
  api/
  console/
  wall/
  sources/
  settings/

components/
  layout/
  map/
  events/
  feeds/
  widgets/
  ui/

lib/
  db/
  adapters/
  normalization/
  validation/
  geospatial/
  severity/
  provenance/
  security/

prisma/
tests/
docs/

## Data model

Create database models for:

- Source.
- SourceHealth.
- FeedSnapshot.
- Event.
- EventEvidence.
- Location.
- MapLayer.
- UserPreference.
- SavedWallLayout.
- AuditLog.

Event fields should include:

id
externalId
title
summary
category
severity
confidence
status
latitude
longitude
locationName
countryCode
observedAt
updatedAt
expiresAt
sourceId
rawPayloadHash
normalizedPayload
createdAt

Do not store unnecessary personal information. Do not collect user-tracking data by default.

## Feed adapter system

Implement this provider-agnostic interface:

interface FeedAdapter {
  id: string;
  name: string;
  category: FeedCategory;
  fetch(): Promise<unknown>;
  validate(payload: unknown): boolean;
  normalize(payload: unknown): NormalizedEvent[];
  healthCheck(): Promise<FeedHealth>;
}

Build safe mock adapters and documented public-feed placeholders for:

- Earthquakes.
- Wildfires.
- Weather alerts.
- Public internet outages.
- Public traffic.
- Transit disruptions.
- Public news.

Every adapter must include:

- Runtime schema validation.
- Request timeouts.
- Exponential-backoff retries.
- Rate-limit handling.
- Structured errors.
- Last-known-good behavior.
- Source attribution.
- Data-freshness tracking.
- Deduplication.
- Idempotent ingestion.
- No hard-coded credentials.

Use server-side environment variables for future API keys. Never expose secrets to the browser.

## Event normalization pipeline

Implement this pipeline:

1. Receive the source payload.
2. Validate it with Zod.
3. Sanitize and normalize text.
4. Normalize timestamps to UTC.
5. Normalize coordinates.
6. Assign an event category.
7. Calculate source freshness.
8. Calculate confidence from source metadata.
9. Calculate severity using documented deterministic rules.
10. Deduplicate by source and external ID.
11. Store a raw-payload hash rather than unnecessary sensitive payload data.
12. Preserve source and transformation provenance.
13. Emit the normalized event.
14. Record ingestion health.

Use these severity values:

- INFO.
- LOW.
- MEDIUM.
- HIGH.
- CRITICAL.

Never imply certainty when source data is incomplete, stale, conflicting, or unverified.

## Security requirements

Implement:

- Strict Content Security Policy.
- Secure HTTP headers.
- CSRF protection for state-changing operations.
- Server-side authorization checks.
- Zod input validation.
- Output encoding.
- URL allowlisting for external links.
- SSRF protections for server-side retrieval.
- Rate limiting.
- Request-size limits.
- Error redaction.
- Structured audit logging.
- No secrets in source code.
- No secrets in browser bundles.
- No secrets in logs.
- No secrets in screenshots.
- No arbitrary proxy endpoint.
- No unrestricted user-supplied URL fetching.
- Safe parsing for XML, JSON, RSS, GeoJSON, and CSV.
- XML entity-expansion protection.
- Prototype-pollution protection.
- XSS protection.
- Safe external-link handling.
- No untrusted iframe embedding by default.

## User experience

Support:

- Loading skeletons.
- Empty states.
- Offline states.
- Stale-data warnings.
- Feed-failure banners.
- Retry actions.
- Toast notifications.
- Keyboard shortcuts.
- Responsive navigation.
- Reduced-motion mode.
- High-contrast mode.
- Screen-reader labels.
- Visible focus indicators.
- Color-plus-text severity indicators.
- Clear source attribution.
- No horizontal overflow on mobile.

Mobile layout requirements:

- Compact navigation drawer or bottom navigation.
- Map and event feed as separate views.
- Swipeable event details.
- Large touch targets.
- No horizontal scrolling.

## Visual styling

Recreate the visual language of supplied reference screenshots without copying their identity:

- Dense left-side event and feed rail.
- Large central map.
- Compact top console bar.
- Amber selection states.
- Blue circular map markers.
- Red and amber severity bars.
- Thin borders.
- Subtle grid or scanline texture used sparingly.
- Monospace labels for timestamps and feed health.
- Strong visual hierarchy.
- Smooth, restrained transitions.
- No unnecessary visual noise.

Use these CSS variables:

--background: #070a0d;
--panel: #0d1217;
--panel-elevated: #141b22;
--border: #27313a;
--text-primary: #e8edf0;
--text-secondary: #8b99a5;
--amber: #ffb000;
--cyan: #00c8ff;
--blue: #238ed1;
--red: #e53935;
--green: #20c878;

## API routes

Implement:

GET    /api/events
GET    /api/events/:id
GET    /api/sources
GET    /api/sources/:id/health
GET    /api/layers
GET    /api/regions
POST   /api/preferences
GET    /api/health

If an ingestion route is required, protect it with server-side authentication and do not expose it publicly by default.

## Demo data

Create realistic but clearly labeled synthetic data for:

- Earthquakes.
- Wildfires.
- Weather alerts.
- Public internet outages.
- Public traffic.
- Transit incidents.
- Public news.

Never present synthetic data as real.

Display a prominent “DEMO DATA” indicator whenever mock mode is active.

Do not use unrelated personal names, organizations, cities, brands, or fictional identities in demo content. Prefer neutral, clearly synthetic records.

## Required deliverables

Produce:

1. Working Next.js application.
2. Responsive ARTEMIS FAWL console interface.
3. Functional interactive map.
4. Feed-health dashboard.
5. Event explorer.
6. Source explorer.
7. Wall mode.
8. Mock feed adapters.
9. Database schema.
10. Secure API routes.
11. Seed script.
12. Unit tests.
13. End-to-end tests.
14. Docker configuration.
15. GitHub Actions workflow.
16. Environment-variable example file.
17. README with setup instructions.
18. Architecture documentation.
19. Threat model.
20. Data-source and licensing documentation.

## Acceptance criteria

The build is complete only when:

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm test` passes.
- Playwright smoke tests pass.
- The application starts with one documented command.
- The dashboard works with mock data and no API keys.
- The map renders without runtime errors.
- Events can be filtered and opened.
- Source health is visible.
- Stale and failed feeds are visually distinguished.
- Synthetic data is clearly labeled.
- External links are safely validated.
- No secrets are committed.
- Mobile layout has no horizontal overflow.
- Keyboard navigation works for primary workflows.
- Error states are intentionally designed.
- Important claims in the interface have visible provenance.
- A repository-wide brand audit confirms that unrelated names, logos, labels, and placeholder identities have been removed or isolated to legally required attribution fields.
- All product-facing identity is aligned with ClearGlass Inc. and ARTEMIS FAWL.

## Implementation process

### Phase 1 — Recon and architecture

- Inspect the repository.
- Identify existing conventions.
- Write the architecture plan.
- Identify assumptions and unknowns.
- Define the data model.
- Define acceptance criteria.
- Identify security and licensing dependencies.

### Phase 2 — Foundation

- Set up the Next.js application.
- Configure Tailwind.
- Configure TypeScript.
- Configure linting.
- Configure testing.
- Configure environment validation.
- Add the ClearGlass Inc. and ARTEMIS FAWL theme.
- Add the base layout.

### Phase 3 — Core console

- Implement navigation.
- Implement feed health.
- Implement the event rail.
- Implement the interactive map.
- Implement event details.
- Implement loading and failure states.

### Phase 4 — Data system

- Implement schemas.
- Implement mock adapters.
- Implement normalization.
- Implement deduplication.
- Implement provenance tracking.
- Implement source-health tracking.

### Phase 5 — Wall and source explorer

- Add configurable widgets.
- Add source explorer.
- Add saved layouts.
- Add local preference persistence.

### Phase 6 — Security and verification

- Add security headers.
- Add validation.
- Add rate limiting.
- Add audit logging.
- Add SSRF protections.
- Run tests and security checks.
- Fix all failures.
- Perform a full brand-name audit.

### Phase 7 — Documentation

Document:

- Setup.
- Architecture.
- Threat model.
- Data contracts.
- Source licensing.
- Operational procedures.
- Failure handling.
- Rollback and recovery.
- Known limitations.

Before declaring completion, provide:

- Files changed.
- Commands executed.
- Test results.
- Security checks performed.
- Known limitations.
- Remaining risks.
- Rollback or recovery procedure.
- Next highest-value action.

Do not claim completion without objective verification.

If a real feed requires credentials, approval, or licensing, use a mock adapter and clearly label it as a placeholder.

Keep the entire product aligned with ClearGlass Inc. and ARTEMIS FAWL branding.
```

## Repository truth boundary

This prompt is intentionally stricter than a design brief. It requires implementation evidence before production claims are made, preserves the repository's existing fail-closed authorization posture, and keeps mock/synthetic states visibly distinct from live data.
