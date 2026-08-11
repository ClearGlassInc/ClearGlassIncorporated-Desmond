# GitHub Pages cannot validate an origin-auth header, so this transform is scoped
# exclusively to explicitly configured API/admin hostnames. Each dynamic origin
# must independently compare the overwritten header value, reject missing or
# invalid values, and disable direct public ingress wherever its platform allows.
resource "cloudflare_ruleset" "dynamic_origin_auth" {
  count = var.enable_origin_auth_header ? 1 : 0

  zone_id     = var.zone_id
  name        = "ClearGlass dynamic-origin authentication"
  description = "Overwrite the shared origin-auth header for API/admin origins."
  kind        = "zone"
  phase       = "http_request_late_transform"

  rules {
    ref         = "set_dynamic_origin_auth_header"
    description = "Set origin authentication header on configured dynamic hosts"
    expression  = local.dynamic_host_scope
    action      = "rewrite"

    action_parameters {
      headers {
        name      = var.origin_auth_header_name
        operation = "set"
        value     = var.origin_auth_header_value
      }
    }
  }
}
