import { streamNames, type StreamName } from "./contracts";

const positiveInt = (name: string, fallback: number) => {
  const value = Number(process.env[name] ?? fallback);
  return Number.isSafeInteger(value) && value > 0 ? value : fallback;
};

const validStreams = new Set<string>(streamNames);

function isStreamName(value: string): value is StreamName {
  return validStreams.has(value);
}

export function parseEnabledStreams(value: string | undefined): Set<StreamName> {
  const configured = (value ?? streamNames.join(","))
    .split(",")
    .map((stream) => stream.trim())
    .filter(Boolean);

  const invalid = configured.filter((stream) => !isStreamName(stream));
  if (invalid.length > 0) {
    throw new Error(`Invalid LIVE_FABRIC_ENABLED_STREAMS value: ${invalid.join(", ")}`);
  }

  return new Set(configured.filter(isStreamName));
}

export const fabricConfig = {
  enabled: process.env.LIVE_FABRIC_ENABLED === "true" && (process.env.NODE_ENV !== "production" || process.env.LIVE_FABRIC_PRODUCTION_APPROVED === "true"),
  allowedOrigins: new Set((process.env.LIVE_FABRIC_ALLOWED_ORIGINS ?? "http://localhost:3030").split(",").map((v) => v.trim()).filter(Boolean)),
  knownSources: new Set((process.env.LIVE_FABRIC_KNOWN_SOURCES ?? (process.env.NODE_ENV === "production" ? "" : "development-disabled-source")).split(",").map((v) => v.trim()).filter(Boolean)),
  publicConnectionsPerIp: positiveInt("LIVE_FABRIC_PUBLIC_CONNECTIONS_PER_IP", 3),
  authConnectionsPerUser: positiveInt("LIVE_FABRIC_AUTH_CONNECTIONS_PER_USER", 5),
  maxEventBytes: positiveInt("LIVE_FABRIC_MAX_EVENT_BYTES", 16_384),
  heartbeatMs: positiveInt("LIVE_FABRIC_HEARTBEAT_MS", 15_000),
  streamTtlMs: positiveInt("LIVE_FABRIC_STREAM_TTL_MS", 300_000),
  enabledStreams: parseEnabledStreams(process.env.LIVE_FABRIC_ENABLED_STREAMS)
};
