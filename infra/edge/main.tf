terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "= 4.40.0"
    }
  }
}

provider "cloudflare" {
  # Authentication is read from CLOUDFLARE_API_TOKEN.
  # Never place provider credentials in Terraform files or committed tfvars.
}

locals {
  provider_mutation_enabled = anytrue([
    var.enable_custom_waf,
    var.enable_managed_waf,
    var.enable_bot_management,
    var.enable_bot_score_rule,
    var.enable_provider_reputation_rules,
    var.enable_rate_limits,
    var.enable_security_headers,
    var.enable_logpush,
    var.enable_geo_asn_rules,
    var.enable_origin_auth_header,
    var.enable_enterprise_body_size_rule,
    var.enable_emergency_mode,
  ])

  host_scope       = "http.host eq \"${var.public_hostname}\""
  api_host_scope   = var.api_hostname != "" ? "http.host eq \"${var.api_hostname}\"" : "false"
  admin_host_scope = var.admin_hostname != "" ? "http.host eq \"${var.admin_hostname}\"" : "false"

  protected_hostnames = distinct(compact([
    var.public_hostname,
    var.api_hostname,
    var.admin_hostname,
  ]))
  protected_host_scope = format(
    "(%s)",
    join(" or ", [for host in local.protected_hostnames : format("http.host eq \"%s\"", host)])
  )
  dynamic_host_scope = length(compact([var.api_hostname, var.admin_hostname])) > 0 ? format(
    "(%s)",
    join(" or ", [for host in compact([var.api_hostname, var.admin_hostname]) : format("http.host eq \"%s\"", host)])
  ) : "false"

  verified_bot = "cf.client.bot"

  trusted_ip_cidrs = concat(var.trusted_ipv4_cidrs, var.trusted_ipv6_cidrs)
  trusted_ip_expr = length(local.trusted_ip_cidrs) > 0 ? format(
    "ip.src in {%s}",
    join(" ", local.trusted_ip_cidrs)
  ) : "false"

  monitoring_ip_cidrs = concat(var.monitoring_ipv4_cidrs, var.monitoring_ipv6_cidrs)
  monitoring_ip_expr = length(local.monitoring_ip_cidrs) > 0 ? format(
    "ip.src in {%s}",
    join(" ", local.monitoring_ip_cidrs)
  ) : "false"

  automation_ip_cidrs = concat(var.internal_automation_ipv4_cidrs, var.internal_automation_ipv6_cidrs)
  automation_ip_expr = length(local.automation_ip_cidrs) > 0 ? format(
    "ip.src in {%s}",
    join(" ", local.automation_ip_cidrs)
  ) : "false"

  bot_challenge_exempt_ip_expr = "(${local.trusted_ip_expr} or ${local.monitoring_ip_expr} or ${local.automation_ip_expr})"

  static_asset_expr = "(${local.host_scope} and http.request.method in {\"GET\" \"HEAD\"} and (http.request.uri.path matches \"(?i)\\\\.(?:css|js|mjs|json|png|jpe?g|gif|webp|svg|ico|woff2?|ttf|otf|map|xml|txt|pdf)$\"))"
  html_expr         = "(${local.host_scope} and http.request.method in {\"GET\" \"HEAD\"} and not (${local.static_asset_expr}))"
  login_path_expr   = "(http.request.uri.path eq \"/login\" or starts_with(http.request.uri.path, \"/api/login\") or starts_with(http.request.uri.path, \"/api/auth/\"))"
  reset_path_expr   = "(lower(http.request.uri.path) contains \"reset\")"
  search_path_expr  = "(http.request.uri.path eq \"/search\" or starts_with(http.request.uri.path, \"/api/search\"))"
  form_path_expr    = "(http.request.uri.path eq \"/contact\" or starts_with(http.request.uri.path, \"/api/contact\"))"
  api_path_expr     = "starts_with(http.request.uri.path, \"/api/\")"
  admin_path_expr   = "starts_with(http.request.uri.path, \"/admin\")"
  webhook_path_expr = "(starts_with(http.request.uri.path, \"/webhooks\") or starts_with(http.request.uri.path, \"/api/webhook\"))"

  login_expr   = "(${local.api_host_scope} and ${local.login_path_expr})"
  reset_expr   = "(${local.api_host_scope} and ${local.reset_path_expr})"
  search_expr  = "(${local.api_host_scope} and ${local.search_path_expr})"
  form_expr    = "(${local.api_host_scope} and ${local.form_path_expr})"
  api_expr     = "(${local.api_host_scope} and ${local.api_path_expr})"
  admin_expr   = "(${local.admin_host_scope} and ${local.admin_path_expr})"
  webhook_expr = "(${local.api_host_scope} and ${local.webhook_path_expr})"

  csp_inventory = jsondecode(file("${path.module}/csp-inventory.json"))
  csp_sources   = local.csp_inventory.csp_sources

  # The committed inventory is derived from the exact Pages artifact. The edge
  # policy remains Report-Only until browser telemetry and route owners approve
  # enforcement; the application still owns route-specific CSP exceptions.
  csp = join(" ", [
    "default-src ${join(" ", local.csp_sources["default-src"])};",
    "base-uri ${join(" ", local.csp_sources["base-uri"])};",
    "object-src ${join(" ", local.csp_sources["object-src"])};",
    "frame-ancestors ${join(" ", local.csp_sources["frame-ancestors"])};",
    "form-action ${join(" ", local.csp_sources["form-action"])};",
    "script-src ${join(" ", local.csp_sources["script-src"])};",
    "style-src ${join(" ", local.csp_sources["style-src"])};",
    "font-src ${join(" ", local.csp_sources["font-src"])};",
    "img-src ${join(" ", local.csp_sources["img-src"])};",
    "media-src ${join(" ", local.csp_sources["media-src"])};",
    "connect-src ${join(" ", local.csp_sources["connect-src"])};",
    "frame-src ${join(" ", local.csp_sources["frame-src"])};",
    "manifest-src ${join(" ", local.csp_sources["manifest-src"])};",
    "worker-src ${join(" ", local.csp_sources["worker-src"])};",
    "upgrade-insecure-requests"
  ])
}
