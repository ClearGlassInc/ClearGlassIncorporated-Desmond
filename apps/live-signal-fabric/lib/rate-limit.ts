const MAX_WINDOWS = 10_000;
const windows = new Map<string, { count: number; resetAt: number }>();

function pruneExpired(now: number): void {
  for (const [key, window] of windows) {
    if (window.resetAt <= now) windows.delete(key);
  }
}

function ensureCapacity(now: number): void {
  if (windows.size < MAX_WINDOWS) return;
  pruneExpired(now);
  while (windows.size >= MAX_WINDOWS) {
    const oldestKey = windows.keys().next().value;
    if (typeof oldestKey !== "string") break;
    windows.delete(oldestKey);
  }
}

export function allowRequest(key: string, limit: number, windowMs = 60_000): boolean {
  if (!key || !Number.isSafeInteger(limit) || limit <= 0 || !Number.isSafeInteger(windowMs) || windowMs <= 0) {
    return false;
  }

  const now = Date.now();
  const current = windows.get(key);
  if (!current || current.resetAt <= now) {
    if (!current) ensureCapacity(now);
    windows.set(key, { count: 1, resetAt: now + windowMs });
    return true;
  }
  if (current.count >= limit) return false;
  current.count += 1;
  return true;
}
