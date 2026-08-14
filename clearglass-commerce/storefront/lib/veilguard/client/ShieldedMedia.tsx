"use client";

/**
 * VEILGUARD — the shielded viewer.
 *
 * Renders one protected item under one grant: capped resolution, rotating
 * per-viewer watermark, ephemeral render window, capture deterrence, and
 * telemetry back to the ledger.
 *
 * Design intent is *invisible protection*. The controls are layered and
 * mostly silent — the viewer sees a clean, well-lit surface and a quiet
 * disclosure line, not a wall of warnings and disabled buttons. Restriction
 * that announces itself invites the challenge; restriction that simply makes
 * the easy paths unrewarding, and the hard paths attributable, does not.
 *
 * Accessibility is a first-class constraint, not an exception:
 *   - the image keeps its real alt text; the watermark is `aria-hidden`
 *   - state changes are announced through a polite live region
 *   - the watermark stops animating under `prefers-reduced-motion` (it still
 *     rotates — that is a security function — it just does not transition)
 *   - permitted actions live in a real, focusable button, so no suppressed
 *     gesture is ever the only route to an allowed action
 *   - the obscured state is visual only; alt text and the notice stay readable
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { variantsFromBits, type TileVariant } from "../tracer";
import { grantAllowsCapability, type ShieldGrantDTO, type TelemetryEventDTO, type TelemetryKind } from "../contract";
import { installDeterrence, type DeterrenceEvent } from "./deterrence";

const TELEMETRY_ENDPOINT = "/api/veilguard/telemetry";
const WATERMARK_TILES = 20;

export type ShieldedMediaProps = {
  grant: ShieldGrantDTO;
  /** Called when the render window expires and the viewer asks to continue. */
  onReattest?: () => void;
  /** Where a viewer who needs an accessible or unmarked copy should be sent. */
  accessibleRequestHref?: string;
};

export function ShieldedMedia({ grant, onReattest, accessibleRequestHref = "/support/accessible-copy" }: ShieldedMediaProps) {
  const surfaceRef = useRef<HTMLDivElement | null>(null);
  const [obscured, setObscured] = useState(false);
  const [obscureReason, setObscureReason] = useState<string | null>(null);
  const [expired, setExpired] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [announcement, setAnnouncement] = useState("");
  const [reducedMotion, setReducedMotion] = useState(false);

  const { policy, watermark } = grant;
  const allowCopyText = grantAllowsCapability(policy, "copy_text");
  const allowExport = grantAllowsCapability(policy, "export");
  const allowDownload = grantAllowsCapability(policy, "download");

  const variants = useMemo(() => variantsFromBits(grant.tracerBits, WATERMARK_TILES), [grant.tracerBits]);

  const report = useCallback(
    (kind: TelemetryKind, extra: { method?: string; allowed?: boolean } = {}) => {
      const event: TelemetryEventDTO = {
        grantToken: grant.token,
        kind,
        occurredAt: new Date().toISOString(),
        ...extra,
      };
      const body = JSON.stringify(event);
      // sendBeacon survives the page going away mid-capture, which is exactly
      // when these events matter most; fetch is the fallback where it is absent.
      if (typeof navigator !== "undefined" && typeof navigator.sendBeacon === "function") {
        navigator.sendBeacon(TELEMETRY_ENDPOINT, new Blob([body], { type: "application/json" }));
        return;
      }
      void fetch(TELEMETRY_ENDPOINT, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
        keepalive: true,
      }).catch(() => {
        /* Telemetry is best-effort: never break the viewer over a failed report. */
      });
    },
    [grant.token],
  );

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReducedMotion(query.matches);
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  }, []);

  useEffect(() => {
    report("render_started");
  }, [report]);

  // Ephemeral render window. When it closes the frame stays obscured until the
  // viewer re-attests, so an unattended screen does not sit on confidential
  // content indefinitely.
  useEffect(() => {
    if (policy.renderTtlSeconds <= 0) {
      setExpired(true);
      return;
    }
    const timer = setTimeout(() => {
      setExpired(true);
      setAnnouncement("Secure preview window ended. Re-verify to continue viewing.");
      report("render_expired");
    }, policy.renderTtlSeconds * 1000);
    return () => clearTimeout(timer);
  }, [policy.renderTtlSeconds, report]);

  // Watermark rotation: re-place the tiles on an interval so a crop taken from
  // any one region still lands on a mark, and so a single cleaned frame does
  // not generalise to the next one.
  useEffect(() => {
    if (!watermark.rotateSeconds) return;
    const timer = setInterval(() => setRotation((value: number) => value + 1), watermark.rotateSeconds * 1000);
    return () => clearInterval(timer);
  }, [watermark.rotateSeconds]);

  useEffect(() => {
    const surface = surfaceRef.current;
    if (!surface) return;

    const stub = [
      `Protected content — ClearGlass Inc.`,
      `${grant.title} (${watermark.contextLabel})`,
      `Traceable copy ${watermark.tracerCode} issued to ${watermark.subjectLabel} at ${watermark.issuedAtIso}.`,
      `Reuse outside the terms of access is attributable to this copy.`,
    ].join("\n");

    return installDeterrence(surface, {
      allowCopyText,
      allowExport,
      obscureOnBlur: policy.obscureOnBlur,
      attributionStub: stub,
      onEvent: (event: DeterrenceEvent) => {
        if (event.kind === "capture_suspected") {
          report("capture_suspected", { method: event.method });
          setAnnouncement("Screen capture detected. This view is watermarked and the event has been logged.");
        } else if (event.kind === "export_attempted") {
          report("export_attempted", { method: event.method });
        } else if (event.kind === "copy_attempted") {
          report("copy_attempted", { allowed: event.allowed });
          if (!event.allowed) setAnnouncement("Copying is not permitted for this item. An attribution notice was copied instead.");
        } else {
          report("automation_suspected", { method: event.method });
        }
      },
      onObscureChange: (isObscured: boolean, reason: string | null) => {
        setObscured(isObscured);
        setObscureReason(reason);
      },
    });
  }, [allowCopyText, allowExport, policy.obscureOnBlur, report, grant.title, watermark]);

  const hidden = obscured || expired;

  return (
    <figure style={{ margin: 0 }}>
      <div
        ref={surfaceRef}
        data-veilguard-surface={grant.assetId}
        style={{
          position: "relative",
          overflow: "hidden",
          borderRadius: 14,
          border: "1px solid rgba(124,150,255,.22)",
          background: "linear-gradient(165deg,rgba(9,14,32,.96),rgba(12,9,28,.96))",
          boxShadow: "0 18px 54px rgba(0,0,0,.44), 0 0 34px rgba(34,211,238,.10)",
          maxWidth: policy.maxRenderedEdgePx ?? undefined,
          userSelect: allowCopyText ? "auto" : "none",
          WebkitUserSelect: allowCopyText ? "auto" : "none",
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- the render is
            policy-capped and deliberately not routed through the image
            optimiser, which would cache a copy outside the shielded path. */}
        <img
          src={grant.source}
          alt={grant.alt}
          draggable={false}
          style={{
            display: "block",
            width: "100%",
            height: "auto",
            filter: hidden ? "blur(22px) saturate(.4)" : "none",
            transition: reducedMotion ? "none" : "filter .18s ease-out",
            pointerEvents: "none",
          }}
        />

        {policy.requireVisibleWatermark ? (
          <WatermarkOverlay
            variants={variants}
            rotation={rotation}
            reducedMotion={reducedMotion}
            label={`${watermark.subjectLabel} · ${watermark.tracerCode}`}
            sublabel={watermark.contextLabel}
          />
        ) : null}

        {hidden ? (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "grid",
              placeItems: "center",
              padding: 20,
              textAlign: "center",
              background: "rgba(6,10,24,.72)",
              backdropFilter: "blur(6px)",
              color: "#d8e4ff",
            }}
          >
            <div>
              <p style={{ margin: "0 0 10px", fontWeight: 700, letterSpacing: ".04em" }}>
                {expired ? "Secure preview ended" : "View paused"}
              </p>
              <p style={{ margin: "0 0 14px", fontSize: 13, color: "#9aa6c8", maxWidth: 320 }}>
                {expired
                  ? "This preview window has closed. Re-verify to open a new one."
                  : obscureReason === "capture_keystroke"
                    ? "A capture gesture was detected. The frame is watermarked and the event is logged."
                    : "The window lost focus, so the content is hidden."}
              </p>
              {expired && onReattest ? (
                <button
                  type="button"
                  onClick={onReattest}
                  style={{
                    padding: "9px 18px",
                    borderRadius: 999,
                    border: "1px solid rgba(34,211,238,.45)",
                    background: "rgba(34,211,238,.12)",
                    color: "#67e8f9",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Re-verify to continue
                </button>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>

      <figcaption style={{ marginTop: 12 }}>
        <ProtectionNotice
          grant={grant}
          allowDownload={allowDownload}
          allowExport={allowExport}
          allowCopyText={allowCopyText}
          accessibleRequestHref={accessibleRequestHref}
        />
      </figcaption>

      <p aria-live="polite" role="status" style={SR_ONLY}>
        {announcement}
      </p>
    </figure>
  );
}

/**
 * The tiled mark.
 *
 * Tiles are laid out from the tracer variants, so two viewers looking at the
 * same asset get measurably different renders. Rotation shifts the whole grid
 * on a cadence, which is what stops a single cleaned crop from generalising.
 *
 * `aria-hidden` throughout: this is a visual attribution layer, and reading it
 * aloud would be noise between a screen-reader user and the actual content.
 */
function WatermarkOverlay({
  variants,
  rotation,
  reducedMotion,
  label,
  sublabel,
}: {
  variants: TileVariant[];
  rotation: number;
  reducedMotion: boolean;
  label: string;
  sublabel: string;
}) {
  const phase = rotation % 2 === 0 ? 0 : 26;

  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 0,
        transition: reducedMotion ? "none" : "transform .5s ease-in-out",
        transform: `translate(${phase * 0.4}px, ${phase * 0.25}px)`,
        mixBlendMode: "overlay",
      }}
    >
      {variants.map((variant: TileVariant) => (
        <div
          key={variant.index}
          style={{
            transform: `translate(${variant.offsetXPx}px, ${variant.offsetYPx}px) rotate(-24deg)`,
            opacity: 0.16 + variant.opacityDelta,
            display: "grid",
            placeItems: "center",
            padding: "10px 4px",
            color: "#ffffff",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: 11,
            letterSpacing: ".08em",
            whiteSpace: "nowrap",
            textShadow: "0 1px 2px rgba(0,0,0,.5)",
          }}
        >
          <span>{variant.index % 3 === 0 ? sublabel : label}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * The disclosure line.
 *
 * Every control in this system is consent-based, and consent means the viewer
 * is actually told: what is marked, what is logged, and how to get an
 * accessible copy. It is written as one calm sentence rather than a warning
 * banner — the point is that the viewer knows, not that they feel policed.
 */
function ProtectionNotice({
  grant,
  allowDownload,
  allowExport,
  allowCopyText,
  accessibleRequestHref,
}: {
  grant: ShieldGrantDTO;
  allowDownload: boolean;
  allowExport: boolean;
  allowCopyText: boolean;
  accessibleRequestHref: string;
}) {
  const permitted = [
    allowDownload ? "download" : null,
    allowExport ? "print or export" : null,
    allowCopyText ? "copy text" : null,
  ].filter(Boolean) as string[];

  return (
    <div style={{ fontSize: 12.5, color: "#9aa6c8", lineHeight: 1.6 }}>
      <p style={{ margin: "0 0 6px" }}>
        <span
          style={{
            display: "inline-block",
            width: 7,
            height: 7,
            borderRadius: 999,
            background: "#22d3ee",
            boxShadow: "0 0 10px rgba(34,211,238,.8)",
            marginRight: 8,
          }}
        />
        This view is watermarked to you and traced as <code style={{ color: "#67e8f9" }}>{grant.watermark.tracerCode}</code>.
        View, copy, export and share events are logged, and this browser is remembered so unusual
        access patterns can be spotted.
      </p>
      <p style={{ margin: "0 0 6px" }}>
        {permitted.length > 0 ? `You may ${permitted.join(", ")}.` : "This item is view-only."}{" "}
        Preview closes after {grant.policy.renderTtlSeconds}s.
      </p>
      <p style={{ margin: 0 }}>
        <a href={accessibleRequestHref} style={{ color: "#9fc4ff" }}>
          Request an accessible or unmarked copy
        </a>
      </p>
    </div>
  );
}

const SR_ONLY = {
  position: "absolute",
  width: 1,
  height: 1,
  padding: 0,
  margin: -1,
  overflow: "hidden",
  clip: "rect(0,0,0,0)",
  whiteSpace: "nowrap",
  border: 0,
} as const;
