import dns from 'node:dns/promises';
import net from 'node:net';

export type EngagementScope = {
  approvedHosts: string[];
  approvedPorts: number[];
  expiresAt: Date;
  confirmed: boolean;
};

export type PolicyResult = { allowed: true; addresses: string[] } | { allowed: false; reason: string };

const DENIED = new Set(['169.254.169.254', '0.0.0.0', '255.255.255.255']);
const PRIVATE4 = [
  ['10.0.0.0', '10.255.255.255'],
  ['172.16.0.0', '172.31.255.255'],
  ['192.168.0.0', '192.168.255.255'],
];

function ipv4ToInt(ip: string): number {
  return ip.split('.').reduce((n, octet) => ((n << 8) + Number(octet)) >>> 0, 0);
}
function inRange(ip: string, low: string, high: string) {
  const n = ipv4ToInt(ip);
  return n >= ipv4ToInt(low) && n <= ipv4ToInt(high);
}
function isAllowedAddress(ip: string, explicit: Set<string>): boolean {
  if (explicit.has(ip)) return true;
  if (net.isIPv4(ip)) {
    if (DENIED.has(ip)) return false;
    if (ip === '127.0.0.1') return true;
    if (PRIVATE4.some(([a, b]) => inRange(ip, a, b))) return true;
    return false;
  }
  if (net.isIPv6(ip)) {
    const normalized = ip.toLowerCase();
    if (normalized === '::1') return true;
    if (normalized.startsWith('ff')) return false;
    if (normalized.startsWith('fe80:')) return false;
    if (normalized.startsWith('fc') || normalized.startsWith('fd')) return explicit.has(ip);
    return false;
  }
  return false;
}

export async function validateTarget(host: string, port: number, scope: EngagementScope): Promise<PolicyResult> {
  if (!scope.confirmed) return { allowed: false, reason: 'Engagement scope confirmation is required.' };
  if (scope.expiresAt.getTime() <= Date.now()) return { allowed: false, reason: 'Authorization has expired.' };
  if (!Number.isInteger(port) || port < 1 || port > 65535 || !scope.approvedPorts.includes(port)) {
    return { allowed: false, reason: 'Port is not explicitly approved by the engagement.' };
  }
  const approved = new Set(scope.approvedHosts.map((h) => h.toLowerCase()));
  const canonical = host.trim().toLowerCase().replace(/\.$/, '');
  if (!canonical || !approved.has(canonical)) {
    return { allowed: false, reason: 'Target is not explicitly authorized by the engagement.' };
  }
  if (net.isIP(canonical)) {
    return isAllowedAddress(canonical, approved)
      ? { allowed: true, addresses: [canonical] }
      : { allowed: false, reason: `Target address ${canonical} is outside the permitted lab scope.` };
  }
  if (canonical === 'localhost') return { allowed: true, addresses: ['127.0.0.1'] };
  let records: dns.LookupAddress[];
  try {
    records = await dns.lookup(canonical, { all: true, verbatim: true });
  } catch {
    return { allowed: false, reason: 'Target DNS resolution failed.' };
  }
  if (!records.length) return { allowed: false, reason: 'Target resolved to no addresses.' };
  const addresses = [...new Set(records.map((r) => r.address))];
  if (!addresses.every((ip) => isAllowedAddress(ip, approved))) {
    return { allowed: false, reason: 'Target DNS resolution escaped the permitted scope.' };
  }
  return { allowed: true, addresses };
}
