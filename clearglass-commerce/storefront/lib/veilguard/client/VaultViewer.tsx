"use client";

/**
 * VEILGUARD — the vault viewer.
 *
 * Requests a grant for the selected item and renders it shielded. Re-attesting
 * after the preview window closes is a fresh grant request, which means a
 * viewer whose risk band rose mid-session comes back with *less* capability
 * than they had a minute ago — the leash tightens without anyone intervening.
 *
 * Denials are rendered as calm, specific copy rather than an error. A viewer
 * who is refused because their session looks unusual is told that, and told
 * how to resolve it; a viewer refused on plan is told that instead. Security
 * copy that reads as an accusation generates support tickets, not compliance.
 */

import { useCallback, useEffect, useState } from "react";
import { isDenial, type ShieldGrantDTO, type ShieldGrantResponse } from "../contract";
import { ShieldedMedia } from "./ShieldedMedia";

export type VaultItem = {
  assetId: string;
  title: string;
  classification: string;
};

export function VaultViewer({ items }: { items: VaultItem[] }) {
  const [selected, setSelected] = useState(items[0]?.assetId ?? "");
  const [grant, setGrant] = useState<ShieldGrantDTO | null>(null);
  const [denial, setDenial] = useState<{ reason: string; band: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const requestGrant = useCallback(async (assetId: string) => {
    if (!assetId) return;
    setLoading(true);
    setDenial(null);
    setGrant(null);
    try {
      const response = await fetch("/api/veilguard/grant", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ assetId }),
      });
      const payload = (await response.json()) as ShieldGrantResponse;
      if (isDenial(payload)) {
        setDenial({ reason: payload.reason, band: payload.risk.band });
      } else {
        setGrant(payload);
      }
    } catch {
      setDenial({ reason: "The shield could not be reached. Try again in a moment.", band: "unknown" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void requestGrant(selected);
  }, [selected, requestGrant]);

  return (
    <div style={{ display: "grid", gap: 22 }}>
      <div role="group" aria-label="Protected items" style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {items.map((item: VaultItem) => {
          const active = item.assetId === selected;
          return (
            <button
              key={item.assetId}
              type="button"
              onClick={() => setSelected(item.assetId)}
              aria-pressed={active}
              style={{
                padding: "8px 14px",
                borderRadius: 999,
                cursor: "pointer",
                border: `1px solid ${active ? "rgba(34,211,238,.55)" : "rgba(124,150,255,.22)"}`,
                background: active ? "rgba(34,211,238,.14)" : "rgba(124,150,255,.06)",
                color: active ? "#67e8f9" : "#9aa6c8",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {item.title}
              <span style={{ marginLeft: 8, opacity: 0.7, fontWeight: 400, fontSize: 11.5 }}>{item.classification}</span>
            </button>
          );
        })}
      </div>

      {loading ? <p style={{ color: "#9aa6c8", margin: 0 }}>Opening a secure preview…</p> : null}

      {denial ? (
        <div
          role="alert"
          style={{
            padding: "16px 18px",
            borderRadius: 12,
            border: "1px solid rgba(248,113,113,.32)",
            background: "rgba(248,113,113,.07)",
            color: "#fecaca",
          }}
        >
          <p style={{ margin: "0 0 6px", fontWeight: 700 }}>Preview not available</p>
          <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.6 }}>{denial.reason}</p>
        </div>
      ) : null}

      {grant ? (
        <ShieldedMedia key={grant.grantId} grant={grant} onReattest={() => void requestGrant(selected)} />
      ) : null}
    </div>
  );
}
