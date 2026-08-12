# Provider Adapter Boundary

The provider-neutral control intent lives in `../policies/baseline.json`. The Terraform files one directory above are the Cloudflare reference adapter only. Do not copy vendor field names, managed-rule IDs, bot scores, or evaluation phases into the neutral policy.

| Neutral control | Cloudflare reference | Fastly | AWS | Azure |
|---|---|---|---|---|
| managed CDN/DDoS | CDN + managed DDoS | Fastly CDN/DDoS | CloudFront + Shield | Front Door |
| managed/custom WAF | WAF Managed Rules + Rulesets | Next-Gen WAF/VCL | AWS WAF web ACL | Front Door WAF policy |
| bot classification | Bot Management/SBFM/scoped custom rule | bot signals/Next-Gen WAF | Bot Control managed group | Bot Manager ruleset |
| IP reputation/lists | managed signals + account IP Lists | edge ACLs/signals | managed reputation lists + IP sets | managed rules + IP match |
| rate limiting | `http_ratelimit` ruleset | edge rate counters | rate-based rules | rate-limit custom rules |
| geo/ASN | country/ASN fields | GeoIP/ASN ACL | country labels; ASN via maintained IP sets | geo match; ASN via maintained IP sets |
| headers/cache | Transform + Cache Rules | VCL/Compute | response headers/cache policy | Rules Engine |
| private static origin | R2/Workers/private-capable origin | private backend/auth | S3 Origin Access Control | Storage Private Link |
| logs | Logpush | real-time log streaming | WAF/CloudFront logs | diagnostic settings |

`provider-mapping.example.json` is a review template, not deployed configuration. A new adapter must preserve rule identifiers, staged rollout, exceptions, expiry, logging/privacy requirements, and the prohibition on broad default-deny behavior. Provider and DNS credentials remain manual protected-environment inputs.
