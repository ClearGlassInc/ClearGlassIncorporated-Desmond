/**
 * VEILGUARD — protected asset registry.
 *
 * Classification lives with the asset, not with the route, so a new surface
 * that renders an existing asset inherits its protection automatically instead
 * of having to remember to re-declare it.
 *
 * In production this is backed by the control plane's catalog. It is a static
 * map here so the storefront has a real, reviewable inventory to run against
 * in dev and in tests, and so the default for an unknown identifier is a
 * *deny*, not an accidental publish.
 */

import type { Capability, Classification } from "./policy";

export type ProtectedAsset = {
  assetId: string;
  title: string;
  classification: Classification;
  /** Capabilities this specific asset withholds regardless of tier. */
  denyCapabilities?: readonly Capability[];
  /** Shown in the watermark, so a leaked frame explains its own context. */
  contextLabel: string;
  /** Source for the render. Relative paths resolve against the storefront. */
  source: string;
  /** Alt text — protection must never cost a screen-reader user the content. */
  alt: string;
};

const ASSETS: readonly ProtectedAsset[] = [
  {
    assetId: "concept-draft-atlas",
    title: "Atlas — concept draft",
    classification: "restricted",
    contextLabel: "Concept draft — pre-release, do not distribute",
    source: "/veilguard/samples/atlas-concept.svg",
    alt: "Early concept sketch for the Atlas interface, showing a layered panel arrangement.",
  },
  {
    assetId: "workflow-map-q3",
    title: "Q3 workflow map",
    classification: "confidential",
    denyCapabilities: ["copy_text"],
    contextLabel: "Proprietary workflow — confidential",
    source: "/veilguard/samples/workflow-map.svg",
    alt: "Diagram of the Q3 operating workflow from intake through governed approval to execution.",
  },
  {
    assetId: "brand-kit-preview",
    title: "Brand kit preview",
    classification: "internal",
    contextLabel: "Internal brand kit",
    source: "/veilguard/samples/brand-kit.svg",
    alt: "Brand kit preview showing the logo lockup, type scale, and the core colour ramp.",
  },
  {
    assetId: "press-hero",
    title: "Press hero image",
    classification: "public",
    contextLabel: "Approved for press use",
    source: "/veilguard/samples/press-hero.svg",
    alt: "Approved press image: the ClearGlass wordmark over a lit glass panel.",
  },
];

const BY_ID = new Map(ASSETS.map((asset: ProtectedAsset) => [asset.assetId, asset]));

/** Unknown identifiers resolve to null — callers must treat that as a denial. */
export function findProtectedAsset(assetId: string): ProtectedAsset | null {
  return BY_ID.get(assetId) ?? null;
}

export function listProtectedAssets(): readonly ProtectedAsset[] {
  return ASSETS;
}
