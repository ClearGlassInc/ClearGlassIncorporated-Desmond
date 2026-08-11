import { z } from "zod";

export const sourceEnvelopeSchema = z.object({
  sourceId: z.string(),
  status: z.enum(["LIVE", "DELAYED", "STATIC_REFERENCE", "STALE", "OFFLINE", "ESTIMATED", "ANALYST", "DEMO", "UNKNOWN"]),
  collectedAt: z.string().datetime().nullable(),
  transformedAt: z.string().datetime(),
  confidence: z.number().min(0).max(1).nullable(),
  license: z.string().nullable(),
  attribution: z.string().nullable(),
  records: z.array(z.record(z.string(), z.unknown())),
  errors: z.array(z.string()).default([])
});

export type SourceEnvelope = z.infer<typeof sourceEnvelopeSchema>;

export type SourceAdapter = {
  id: string;
  cadence: string;
  license: string;
  fetch(signal?: AbortSignal): Promise<SourceEnvelope>;
};

const allowedFeeds = new Set(["prices", "production", "reserves", "trade", "policy", "sanctions", "supply-risk", "news", "provenance"]);

export class PublicSnapshotAdapter implements SourceAdapter {
  readonly cadence = "provider-defined";
  readonly license = "per upstream source metadata";

  constructor(public readonly id: string, private readonly baseUrl: string) {
    if (!allowedFeeds.has(id)) throw new Error(`Unsupported public feed: ${id}`);
  }

  async fetch(signal?: AbortSignal): Promise<SourceEnvelope> {
    const url = new URL(`/data/minerals/latest/${this.id}.json`, this.baseUrl);
    const response = await fetch(url, { signal, headers: { Accept: "application/json" } });
    if (!response.ok) {
      return sourceEnvelopeSchema.parse({
        sourceId: this.id,
        status: "OFFLINE",
        collectedAt: null,
        transformedAt: new Date().toISOString(),
        confidence: null,
        license: null,
        attribution: null,
        records: [],
        errors: [`HTTP ${response.status} from ${url.origin}`]
      });
    }
    const payload = await response.json() as { metadata?: Record<string, unknown>; records?: unknown[]; message?: string };
    const metadata = payload.metadata ?? {};
    const rawStatus = String(metadata.status ?? "UNKNOWN").toUpperCase().replaceAll(" ", "_");
    const status = sourceEnvelopeSchema.shape.status.safeParse(rawStatus).success ? rawStatus : "UNKNOWN";
    return sourceEnvelopeSchema.parse({
      sourceId: this.id,
      status,
      collectedAt: metadata.retrieved_at ?? metadata.last_updated ?? null,
      transformedAt: new Date().toISOString(),
      confidence: typeof metadata.confidence === "number" ? metadata.confidence : null,
      license: typeof metadata.license === "string" ? metadata.license : null,
      attribution: typeof metadata.provider === "string" ? metadata.provider : null,
      records: Array.isArray(payload.records) ? payload.records.filter((item): item is Record<string, unknown> => !!item && typeof item === "object" && !Array.isArray(item)) : [],
      errors: payload.message ? [payload.message] : []
    });
  }
}

export function configuredPublicAdapters(): SourceAdapter[] {
  const baseUrl = process.env.PUBLIC_MINERALS_BASE_URL ?? "https://www.clearglassinc.com";
  return [...allowedFeeds].map((id) => new PublicSnapshotAdapter(id, baseUrl));
}
