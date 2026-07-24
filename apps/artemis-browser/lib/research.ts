export type Role = "analyst" | "reviewer" | "admin";
export type Source = { id: string; title: string; url: string; hash: string; capturedAt: string };
export type Claim = { text: string; sourceIds: string[] };
export type Agent = { name: string; purpose: string; guardrail: string; status: "ready" | "approval-gated" };

export const agents: Agent[] = [
  { name: "Triage Agent", purpose: "Ranks public-source browser captures by defensive relevance.", guardrail: "Never ingests private, leaked, credentialed, or exploit-only sources.", status: "ready" },
  { name: "Citation Agent", purpose: "Refuses unsupported claims and attaches source IDs to every sentence.", guardrail: "Blocks summaries until every claim maps to captured provenance.", status: "ready" },
  { name: "Workflow Upgrade Agent", purpose: "Drafts prompt and workflow improvements from analyst feedback.", guardrail: "Human approval and eval pass required before Apollo promotion.", status: "approval-gated" },
];

export const sources: Source[] = [
  { id: "src-001", title: "Vendor advisory", url: "https://example.org/security/advisory", hash: "sha256:9f27…", capturedAt: "2026-07-24T09:30:00Z" },
  { id: "src-002", title: "Public CVE record", url: "https://example.org/cve/CVE-2026-0001", hash: "sha256:b472…", capturedAt: "2026-07-24T09:32:00Z" },
  { id: "src-003", title: "Defensive detection note", url: "https://example.org/detection", hash: "sha256:c118…", capturedAt: "2026-07-24T09:34:00Z" },
];

export const claims: Claim[] = [
  { text: "A patch is available and should be prioritized for internet-facing assets.", sourceIds: ["src-001", "src-002"] },
  { text: "Detection engineering can begin from public behavioral indicators without collecting credentials or private data.", sourceIds: ["src-003"] },
];
