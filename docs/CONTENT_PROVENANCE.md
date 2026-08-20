# ClearGlass Content Provenance

## Purpose

This subsystem marks ClearGlass text so copied material can carry a machine-detectable origin signal. It is a provenance mechanism, not an XSS, CSRF, authentication, authorization, DRM, or anti-scraping control.

The implementation deliberately separates two trust levels:

1. **Signed build/server watermark** — Node tooling encodes metadata and an HMAC-SHA-256 signature using `CG_WATERMARK_SECRET`. The secret must never be shipped to browser JavaScript or committed to Git.
2. **Public browser marker** — `assets/js/content-provenance.js` can add an unsigned zero-width source marker to rendered content. It identifies likely origin but cannot prove authenticity because anyone can reproduce an unsigned marker.

GitHub Pages is static hosting. It cannot safely mint per-user signed watermarks at request time. If ClearGlass later needs recipient-specific forensic attribution, generate the marked text behind a trusted server/API and keep signing keys there.

## Method comparison

| Method | Mechanism | Copy/paste survival | Main weakness | Use here |
|---|---|---:|---|---|
| Zero-width encoding | U+200B/U+200C bit stream inside framed markers | Good for ordinary plain-text copy/paste | Unicode normalization/sanitization can strip it | Implemented |
| Synonym substitution | Deterministic lexical choices encode bits | Better against Unicode stripping | Paraphrasing destroys signal; hard to avoid semantic drift | Not automated |
| Syntactic substitution | Controlled punctuation/structure choices | Can survive basic formatting | Editing/paraphrasing destroys signal; style changes can be detectable | Not automated |
| External content fingerprint | Store cryptographic hash/minhash of canonical text | No hidden characters required | Detects similarity, not embedded provenance | Recommended companion control |

## Signed Node workflow

Build first:

```bash
npm ci
npm run build
```

Set a secret through the environment or your CI secret store. Do not place it in a source file:

```bash
export CG_WATERMARK_SECRET='replace-with-a-long-random-secret'
```

Embed a signed watermark:

```bash
npm run provenance -- embed input.txt output.txt blog/article-id
```

Detect and verify:

```bash
npm run provenance -- detect copied.txt
```

Strip ClearGlass framed markers:

```bash
npm run provenance -- strip copied.txt clean.txt
```

The embedder inserts redundant copies at several word boundaries. Extraction deduplicates identical copies. This improves partial-copy survival but does not make the marker resistant to deliberate removal.

## Browser workflow

Load `/assets/js/content-provenance.js`, then opt in a content region:

```html
<script src="/assets/js/content-provenance.js"></script>
<script>
  ClearGlassProvenance.applyPublicAttribution('article', 'blog/article-id');
</script>
```

The browser helper contains no secret. Use `ClearGlassProvenance.extract(text)` for inspection and `ClearGlassProvenance.strip(text)` to remove framed markers.

Do not use public browser markers as evidence that a specific person copied material. They identify content origin only. Per-user or per-session identifiers introduce privacy and governance obligations and should be implemented only behind an approved server-side design.

## Failure modes

- **Unicode sanitization:** ASCII-only conversion, aggressive sanitizers, normalization pipelines, and some publishing systems can remove zero-width characters.
- **Paraphrasing or manual retyping:** destroys zero-width, synonym, and syntactic marks.
- **Partial selection:** a copied fragment may miss every embedded marker. Redundant copies reduce, not eliminate, this risk.
- **Rich-text transformations:** some editors preserve markers; others normalize them away.
- **Encoding corruption:** broken UTF-8 handling can expose replacement glyphs or destroy the marker.
- **Search/accessibility side effects:** hidden Unicode changes raw text length and can affect text processing. Keep browser attribution opt-in and test assistive technology.
- **Forgery of unsigned markers:** public markers are reproducible and are not cryptographic evidence.
- **Secret exposure:** if `CG_WATERMARK_SECRET` leaks, signed provenance can be forged. Rotate the key and version the signing policy.

## Validation matrix

Run automated checks:

```bash
npm test
npm run typecheck
```

Then test representative production paths:

1. Render marked content in current Chrome, Safari, Firefox, and Edge.
2. Copy full and partial selections into Notepad/TextEdit, VS Code, Word, Google Docs, Slack/Teams, and email clients.
3. Run `provenance detect` on recovered plain text and record whether the signature verifies.
4. Pass samples through DOMPurify or equivalent application sanitizers used by ClearGlass.
5. Normalize samples using NFC/NFKC and test any CMS/export pipeline.
6. Reformat to ASCII-only text and confirm the expected failure is detected rather than misreported as verified provenance.
7. Test screen readers and keyboard selection to ensure no audible or navigation artifact is introduced.
8. Tamper with one or more encoded bits and confirm HMAC verification fails.
9. Verify a wrong secret returns `verified: false` and no secret returns `verified: null`.
10. Maintain a corpus of transformations and measure survival rate before treating the watermark as an operational control.

## Operational recommendation

Use this layer together with canonical URLs, visible copyright/provenance metadata, publication timestamps, signed build artifacts, server logs where appropriate, and similarity/fingerprint detection. Zero-width watermarking is useful evidence when it survives; it should never be the sole basis for attribution or enforcement.
