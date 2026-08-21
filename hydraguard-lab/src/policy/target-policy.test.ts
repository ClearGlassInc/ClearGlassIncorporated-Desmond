import { describe, expect, it } from 'vitest';
import { validateTarget } from '../src/policy/target-policy';

const scope = (host: string, port = 21) => ({
  approvedHosts: [host], approvedPorts: [port], expiresAt: new Date(Date.now() + 60_000), confirmed: true,
});

describe('TargetPolicy', () => {
  it('allows localhost only when explicitly authorized', async () => {
    await expect(validateTarget('127.0.0.1', 21, scope('127.0.0.1'))).resolves.toMatchObject({ allowed: true });
  });
  it('denies public IPv4 even when placed in an engagement', async () => {
    await expect(validateTarget('8.8.8.8', 21, scope('8.8.8.8'))).resolves.toMatchObject({ allowed: false });
  });
  it('denies cloud metadata address', async () => {
    await expect(validateTarget('169.254.169.254', 80, scope('169.254.169.254', 80))).resolves.toMatchObject({ allowed: false });
  });
  it('denies multicast and global IPv6', async () => {
    await expect(validateTarget('224.0.0.1', 21, scope('224.0.0.1'))).resolves.toMatchObject({ allowed: false });
    await expect(validateTarget('2001:4860:4860::8888', 21, scope('2001:4860:4860::8888'))).resolves.toMatchObject({ allowed: false });
  });
  it('denies unapproved ports and expired authorization', async () => {
    await expect(validateTarget('127.0.0.1', 22, scope('127.0.0.1'))).resolves.toMatchObject({ allowed: false });
    await expect(validateTarget('127.0.0.1', 21, { ...scope('127.0.0.1'), expiresAt: new Date(Date.now() - 1) })).resolves.toMatchObject({ allowed: false });
  });
  it('fails closed without confirmation', async () => {
    await expect(validateTarget('127.0.0.1', 21, { ...scope('127.0.0.1'), confirmed: false })).resolves.toMatchObject({ allowed: false });
  });
});
