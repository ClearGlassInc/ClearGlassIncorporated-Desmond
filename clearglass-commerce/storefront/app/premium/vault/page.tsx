/**
 * /premium/vault — the shielded content vault.
 *
 * Sits behind the storefront's existing premium gate (see `middleware.ts`), so
 * this page only ever renders for an authenticated session. The gate is the
 * outer perimeter; everything VEILGUARD does happens *inside* it, on the
 * assumption that a valid session is not the same thing as a trusted one.
 *
 * The page itself stays a server component and ships no asset sources — the
 * client receives nothing until it has been issued a grant.
 */

import { listProtectedAssets, type ProtectedAsset } from "@/lib/veilguard/registry";
import { VaultViewer } from "@/lib/veilguard/client/VaultViewer";

export const metadata = {
  title: "Shielded vault · ClearGlass",
  description: "Watermarked, traced, ephemeral previews of protected ClearGlass content.",
};

export default function VaultPage() {
  const items = listProtectedAssets().map((asset: ProtectedAsset) => ({
    assetId: asset.assetId,
    title: asset.title,
    classification: asset.classification,
  }));

  return (
    <section style={{ display: "grid", gap: 20 }}>
      <header>
        <p
          style={{
            margin: "0 0 6px",
            fontSize: 11,
            letterSpacing: ".22em",
            textTransform: "uppercase",
            color: "#67e8f9",
          }}
        >
          VEILGUARD · shielded vault
        </p>
        <h1 style={{ margin: "0 0 10px", fontSize: 30, lineHeight: 1.2 }}>Protected content</h1>
        <p style={{ margin: 0, color: "#9aa6c8", lineHeight: 1.7, maxWidth: 640 }}>
          Each item opens in a secure preview: capped resolution, a watermark tied to you and this
          session, and a window that closes on its own. What you are allowed to do with an item
          depends on its classification, your plan, and how this session is behaving right now.
        </p>
      </header>

      <VaultViewer items={items} />
    </section>
  );
}
