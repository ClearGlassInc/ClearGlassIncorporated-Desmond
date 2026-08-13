/**
 * VEILGUARD — traceable content variants and leak tracing.
 *
 * Every render of a protected item carries a 40-bit *tracer* bound to the
 * (asset, subject, session) triple. The tracer surfaces two ways:
 *
 *   1. as an 8-character code printed into the visible watermark, and
 *   2. as a set of imperceptible per-tile rendering deltas (`variantsFromBits`)
 *      so that two viewers' renders of the same asset are not byte-identical.
 *
 * When something leaks, an analyst reads whatever survived — a cropped corner,
 * a re-photographed monitor, four legible characters out of eight — and
 * `traceLeak` ranks the candidate grants by how well they match, reporting an
 * honest false-match probability rather than a bare "it was them".
 *
 * Pure module: no secrets, no Node built-ins, safe in the client bundle. The
 * keyed derivation that produces a tracer lives in `watermark.ts` (server only).
 */

/** Tracer width in bits. 40 bits = exactly 8 Crockford base32 characters. */
export const TRACER_BITS = 40;
export const TRACER_CHARS = TRACER_BITS / 5;

/**
 * Crockford base32: no I, L, O or U, so a code read off a screen or a photo
 * has fewer ways to go wrong. Unknown characters are written as `?`.
 */
const ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
const UNKNOWN = "?";

/** Crockford's canonical confusions, applied before decoding. */
const NORMALIZE: Record<string, string> = { I: "1", L: "1", O: "0", U: "V" };

export type TracerBits = readonly number[];

/**
 * A partially-recovered tracer. `bits[i]` is only meaningful where
 * `mask[i] === 1`; unknown positions carry 0 and must not be compared.
 */
export type RecoveredTracer = {
  bits: TracerBits;
  mask: readonly number[];
  knownBits: number;
};

export function bitsToCode(bits: TracerBits): string {
  if (bits.length !== TRACER_BITS) {
    throw new RangeError(`tracer must be ${TRACER_BITS} bits, received ${bits.length}`);
  }
  let code = "";
  for (let i = 0; i < TRACER_BITS; i += 5) {
    let value = 0;
    for (let j = 0; j < 5; j += 1) value = (value << 1) | (bits[i + j] ? 1 : 0);
    code += ALPHABET[value];
  }
  return code;
}

/**
 * Parse a code that may be lowercase, hyphenated, padded with `?` for
 * illegible characters, or shorter than full width (trailing positions are
 * then treated as unknown). Anything else is rejected.
 */
export function parseTracerCode(input: string): RecoveredTracer {
  const cleaned = input
    .toUpperCase()
    .replace(/[\s-]/g, "")
    .split("")
    .map((ch) => NORMALIZE[ch] ?? ch)
    .join("");

  if (cleaned.length > TRACER_CHARS) {
    throw new RangeError(`tracer code is at most ${TRACER_CHARS} characters, received ${cleaned.length}`);
  }

  const bits: number[] = [];
  const mask: number[] = [];
  for (let i = 0; i < TRACER_CHARS; i += 1) {
    const ch = cleaned[i] ?? UNKNOWN;
    if (ch === UNKNOWN) {
      bits.push(0, 0, 0, 0, 0);
      mask.push(0, 0, 0, 0, 0);
      continue;
    }
    const value = ALPHABET.indexOf(ch);
    if (value < 0) throw new RangeError(`invalid tracer character: ${ch}`);
    for (let j = 4; j >= 0; j -= 1) {
      bits.push((value >> j) & 1);
      mask.push(1);
    }
  }

  return { bits, mask, knownBits: mask.reduce((sum: number, m: number) => sum + m, 0) };
}

/** Hamming distance over the recovered tracer's known positions only. */
export function maskedDistance(recovered: RecoveredTracer, candidate: TracerBits): number {
  if (candidate.length !== TRACER_BITS) {
    throw new RangeError(`candidate must be ${TRACER_BITS} bits, received ${candidate.length}`);
  }
  let distance = 0;
  for (let i = 0; i < TRACER_BITS; i += 1) {
    if (recovered.mask[i] && recovered.bits[i] !== candidate[i]) distance += 1;
  }
  return distance;
}

/**
 * Probability that an unrelated tracer would match this well by chance:
 * sum(C(k, i) for i <= d) / 2^k, over k known bits and d mismatches.
 *
 * This is the number that keeps a trace honest. Four legible characters
 * (k = 20) with a clean match is ~1e-6 — strong. Two characters with two bit
 * errors is ~1e-2 — a lead, not a conclusion.
 */
export function falseMatchProbability(knownBits: number, distance: number): number {
  if (knownBits <= 0) return 1;
  let ways = 0;
  for (let i = 0; i <= Math.min(distance, knownBits); i += 1) ways += binomial(knownBits, i);
  return ways / Math.pow(2, knownBits);
}

function binomial(n: number, k: number): number {
  if (k < 0 || k > n) return 0;
  let result = 1;
  for (let i = 1; i <= k; i += 1) result = (result * (n - k + i)) / i;
  return result;
}

export type TraceCandidate = {
  /** Opaque grant identifier, so a trace result can be joined to the ledger. */
  grantId: string;
  assetId: string;
  subject: string;
  sessionId: string;
  issuedAt: string;
  bits: TracerBits;
};

export type TraceMatch = {
  candidate: TraceCandidate;
  distance: number;
  knownBits: number;
  falseMatchProbability: number;
  /** Coarse verdict, so callers do not have to interpret the probability. */
  confidence: "conclusive" | "strong" | "indicative" | "inconclusive";
};

/** Verdict thresholds, expressed as false-match probability ceilings. */
const CONCLUSIVE = 1e-9;
const STRONG = 1e-6;
const INDICATIVE = 1e-3;

/**
 * Rank candidate grants against a recovered tracer.
 *
 * Returns every candidate within `maxDistance`, best match first. Callers get
 * the full ranked list on purpose: a second candidate at a similar distance
 * means the evidence does not separate two people, and that has to be visible
 * rather than hidden behind a top-1 answer.
 */
export function traceLeak(
  recoveredCode: string,
  candidates: readonly TraceCandidate[],
  options: { maxDistance?: number } = {},
): { recovered: RecoveredTracer; matches: TraceMatch[] } {
  const recovered = parseTracerCode(recoveredCode);
  const maxDistance = options.maxDistance ?? 4;

  const matches = candidates
    .map((candidate) => {
      const distance = maskedDistance(recovered, candidate.bits);
      const p = falseMatchProbability(recovered.knownBits, distance);
      return {
        candidate,
        distance,
        knownBits: recovered.knownBits,
        falseMatchProbability: p,
        confidence: verdict(p),
      };
    })
    .filter((match) => match.distance <= maxDistance)
    .sort((a, b) => a.distance - b.distance || a.candidate.issuedAt.localeCompare(b.candidate.issuedAt));

  return { recovered, matches };
}

function verdict(p: number): TraceMatch["confidence"] {
  if (p <= CONCLUSIVE) return "conclusive";
  if (p <= STRONG) return "strong";
  if (p <= INDICATIVE) return "indicative";
  return "inconclusive";
}

/**
 * Per-tile rendering deltas derived from the tracer.
 *
 * The overlay is drawn as a grid of tiles; each tile takes a sub-pixel offset
 * and a fractional opacity trim from two bits of the tracer. The deltas are far
 * below the perceptual threshold individually, but the *pattern* across tiles
 * is a recoverable signal, and it is stable for a given grant — so a re-render,
 * a resize, or a partial crop still carries the same variant.
 *
 * This is a deterrence-and-attribution control, not an unbreakable one: a
 * determined re-encode can wash it out. Its job is to make casual reuse
 * traceable and to corroborate the printed code, not to stand alone.
 */
export type TileVariant = {
  index: number;
  offsetXPx: number;
  offsetYPx: number;
  opacityDelta: number;
};

export function variantsFromBits(bits: TracerBits, tileCount = 20): TileVariant[] {
  if (bits.length !== TRACER_BITS) {
    throw new RangeError(`tracer must be ${TRACER_BITS} bits, received ${bits.length}`);
  }
  const variants: TileVariant[] = [];
  for (let index = 0; index < tileCount; index += 1) {
    const a = bits[(index * 2) % TRACER_BITS];
    const b = bits[(index * 2 + 1) % TRACER_BITS];
    const c = bits[(index * 3 + 7) % TRACER_BITS];
    variants.push({
      index,
      offsetXPx: a ? 0.5 : -0.5,
      offsetYPx: b ? 0.5 : -0.5,
      opacityDelta: c ? 0.012 : -0.012,
    });
  }
  return variants;
}
