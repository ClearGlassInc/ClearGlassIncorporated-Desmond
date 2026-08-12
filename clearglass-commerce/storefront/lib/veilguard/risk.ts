/**
 * VEILGUARD — device, session and anomaly risk scoring.
 *
 * Produces a 0–100 score and a band that `policy.ts` consumes to withdraw
 * capability. Every point is attributed to a named signal with a
 * human-readable reason, because a score that cannot be explained cannot be
 * appealed — and a viewer downgraded to preview-only deserves to be told why,
 * as does the reviewer reading the ledger six months later.
 *
 * Deliberate design limits:
 *
 *   - Signals are coarse, first-party and consented. There is no covert device
 *     fingerprinting, no canvas/font probing, no cross-site identifier. A
 *     "device" here is a salted first-party token the viewer's browser stores
 *     after being told it exists.
 *   - No signal is a biometric, and none is derived from content the viewer
 *     produced. Risk is about access *shape*, not about the person.
 *   - Scoring is monotone and capped per signal, so a single noisy input
 *     cannot drive a lockout on its own — with one deliberate exception, the
 *     honeypot, which is a near-unambiguous misuse indicator.
 *
 * Pure module: no I/O, no secrets, client-safe.
 */

import type { RiskBand } from "./policy";

export type RiskSignals = {
  /** Has this first-party device token been seen before, for this subject? */
  deviceKnown: boolean;
  /** Age of the device token in days. New devices carry more uncertainty. */
  deviceAgeDays: number;
  /** Distinct protected assets this session touched in the scoring window. */
  distinctAssetsInWindow: number;
  /** Grants issued to this session in the window. */
  grantsInWindow: number;
  /** Grant requests refused in the window (probing indicator). */
  failedGrantsInWindow: number;
  /** Client-reported capture-shaped interactions (see `client/deterrence`). */
  captureSuspicions: number;
  /** Honeypot assets touched. Near-unambiguous: nothing links to these. */
  honeypotTouches: number;
  /** Count of automation indicators reported by the runtime (headless, webdriver). */
  automationIndicators: number;
  /** Request arrived over an anonymizing network, per the edge's own classification. */
  anonymizedNetwork: boolean;
  /** Implied travel speed since the last request, km/h. Null when unknown. */
  geoVelocityKmh: number | null;
};

export type RiskContribution = {
  signal: keyof RiskSignals | "baseline";
  points: number;
  reason: string;
};

export type RiskAssessment = {
  score: number;
  band: RiskBand;
  contributions: RiskContribution[];
  /** Set when a signal is severe enough that the band was forced upward. */
  override: string | null;
};

/** Band thresholds. Inclusive lower bounds. */
const BAND_FLOORS: readonly { floor: number; band: RiskBand }[] = [
  { floor: 75, band: "critical" },
  { floor: 50, band: "high" },
  { floor: 25, band: "elevated" },
  { floor: 0, band: "nominal" },
];

export function bandFor(score: number): RiskBand {
  for (const { floor, band } of BAND_FLOORS) {
    if (score >= floor) return band;
  }
  return "nominal";
}

/** Physically implausible travel between two requests on one session. */
const IMPOSSIBLE_TRAVEL_KMH = 900;

export function scoreRisk(signals: RiskSignals): RiskAssessment {
  const contributions: RiskContribution[] = [];
  let override: string | null = null;

  const add = (signal: RiskContribution["signal"], points: number, reason: string) => {
    if (points > 0) contributions.push({ signal, points, reason });
  };

  // An unrecognised device is the single most common precursor to account
  // sharing, so it is weighted meaningfully — but it is also the most common
  // benign event (new laptop, cleared storage), so it cannot reach a lockout
  // alone. It decays as the device establishes history.
  if (!signals.deviceKnown) {
    add("deviceKnown", 18, "device not previously seen for this viewer");
  } else if (signals.deviceAgeDays < 1) {
    add("deviceAgeDays", 8, "device first seen less than a day ago");
  } else if (signals.deviceAgeDays < 7) {
    add("deviceAgeDays", 4, "device established less than a week ago");
  }

  // Breadth-then-volume: touching many *different* protected items in one
  // window looks like harvesting in a way that re-reading one item does not.
  if (signals.distinctAssetsInWindow > 25) {
    add("distinctAssetsInWindow", 22, `${signals.distinctAssetsInWindow} distinct protected assets opened in the window`);
  } else if (signals.distinctAssetsInWindow > 12) {
    add("distinctAssetsInWindow", 12, `${signals.distinctAssetsInWindow} distinct protected assets opened in the window`);
  } else if (signals.distinctAssetsInWindow > 6) {
    add("distinctAssetsInWindow", 5, `${signals.distinctAssetsInWindow} distinct protected assets opened in the window`);
  }

  if (signals.grantsInWindow > 60) {
    add("grantsInWindow", 14, `${signals.grantsInWindow} grants requested in the window`);
  } else if (signals.grantsInWindow > 30) {
    add("grantsInWindow", 7, `${signals.grantsInWindow} grants requested in the window`);
  }

  // Refusals are the clearest probing signal: legitimate clients rarely ask
  // for things the UI never offered them.
  if (signals.failedGrantsInWindow > 0) {
    add(
      "failedGrantsInWindow",
      Math.min(signals.failedGrantsInWindow * 6, 24),
      `${signals.failedGrantsInWindow} grant request(s) refused in the window`,
    );
  }

  // Capture-shaped interactions are individually weak — a print-screen may be
  // for an unrelated window — so they only matter in repetition.
  if (signals.captureSuspicions > 0) {
    add(
      "captureSuspicions",
      Math.min(signals.captureSuspicions * 7, 28),
      `${signals.captureSuspicions} capture-shaped interaction(s) observed`,
    );
  }

  if (signals.automationIndicators > 0) {
    add(
      "automationIndicators",
      Math.min(signals.automationIndicators * 10, 25),
      `${signals.automationIndicators} automation indicator(s) reported by the runtime`,
    );
  }

  // Anonymised egress is not misuse — plenty of legitimate viewers use a VPN.
  // It is scored as mild uncertainty, not as guilt.
  if (signals.anonymizedNetwork) {
    add("anonymizedNetwork", 8, "request arrived over an anonymising network");
  }

  if (signals.geoVelocityKmh !== null && signals.geoVelocityKmh > IMPOSSIBLE_TRAVEL_KMH) {
    add(
      "geoVelocityKmh",
      20,
      `implied travel of ${Math.round(signals.geoVelocityKmh)} km/h since the previous request`,
    );
  }

  // The honeypot is the one deliberate override. Nothing in the product links
  // to a canary asset, so reaching one is not something a normal session does
  // by accident — it means someone is enumerating, or replaying a leaked
  // reference. This forces the band to critical regardless of the total.
  if (signals.honeypotTouches > 0) {
    add("honeypotTouches", 60, `${signals.honeypotTouches} honeypot asset(s) touched — canaries are never linked`);
    override = "honeypot_touched";
  }

  const score = Math.min(
    100,
    contributions.reduce((total: number, contribution: RiskContribution) => total + contribution.points, 0),
  );

  const band = override ? "critical" : bandFor(score);

  if (contributions.length === 0) {
    contributions.push({ signal: "baseline", points: 0, reason: "no elevated signals observed" });
  }

  return { score, band, contributions, override };
}

/** Neutral signal set — the shape a first, clean request presents. */
export function baselineSignals(overrides: Partial<RiskSignals> = {}): RiskSignals {
  return {
    deviceKnown: true,
    deviceAgeDays: 90,
    distinctAssetsInWindow: 1,
    grantsInWindow: 1,
    failedGrantsInWindow: 0,
    captureSuspicions: 0,
    honeypotTouches: 0,
    automationIndicators: 0,
    anonymizedNetwork: false,
    geoVelocityKmh: null,
    ...overrides,
  };
}

/** One-line summary for the ledger's `detail` bag. */
export function summarizeRisk(assessment: RiskAssessment): string {
  const top = assessment.contributions
    .filter((c: RiskContribution) => c.points > 0)
    .sort((a: RiskContribution, b: RiskContribution) => b.points - a.points)
    .slice(0, 3)
    .map((c: RiskContribution) => `${c.signal}+${c.points}`)
    .join(" ");
  return top ? `${assessment.score}/${assessment.band} (${top})` : `${assessment.score}/${assessment.band}`;
}
