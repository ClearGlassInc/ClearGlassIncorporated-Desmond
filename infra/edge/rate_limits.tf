# One zone-level http_ratelimit entry point. If the existing commerce stack owns
# this phase for the same zone, migrate/import before enabling this resource.

resource "cloudflare_ruleset" "rate_limits" {
  count = var.enable_rate_limits ? 1 : 0

  zone_id     = var.zone_id
  name        = "ClearGlass perimeter rate limits"
  description = "Static-site and optional dynamic-origin rate limits."
  kind        = "zone"
  phase       = "http_ratelimit"

  rules {
    ref         = "rl_static_assets"
    description = "Static assets per IP/minute"
    expression  = "${local.static_asset_expr} and not (${local.verified_bot}) and not (${local.bot_challenge_exempt_ip_expr})"
    action      = lookup(var.rate_limit_actions, "static_assets", "log")
    ratelimit {
      characteristics     = lookup(var.rate_limit_characteristics, "static_assets", ["ip.src", "cf.colo.id"])
      period              = 60
      requests_per_period = var.static_asset_requests_per_minute
      mitigation_timeout  = var.mitigation_timeout_seconds
    }
  }

  rules {
    ref         = "rl_html_documents"
    description = "HTML/document requests per IP/minute"
    expression  = "${local.html_expr} and not (${local.verified_bot}) and not (${local.bot_challenge_exempt_ip_expr})"
    action      = lookup(var.rate_limit_actions, "html", "log")
    ratelimit {
      characteristics     = lookup(var.rate_limit_characteristics, "html", ["ip.src", "cf.colo.id"])
      period              = 60
      requests_per_period = var.html_requests_per_minute
      mitigation_timeout  = var.mitigation_timeout_seconds
    }
  }

  dynamic "rules" {
    for_each = var.api_hostname != "" ? [1] : []
    content {
      ref         = "rl_login"
      description = "Login/authentication attempts per IP/minute"
      expression  = "(${local.login_expr} and http.request.method in {\"POST\" \"PUT\"} and not (${local.bot_challenge_exempt_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "login", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "login", ["ip.src", "cf.colo.id"])
        period              = 60
        requests_per_period = var.login_requests_per_minute
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }

  dynamic "rules" {
    for_each = var.api_hostname != "" ? [1] : []
    content {
      ref         = "rl_password_reset"
      description = "Password reset initiation per IP/10 minutes"
      expression  = "(${local.reset_expr} and http.request.method in {\"POST\" \"PUT\"} and not (${local.bot_challenge_exempt_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "password_reset", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "password_reset", ["ip.src", "cf.colo.id"])
        period              = 600
        requests_per_period = var.reset_requests_per_10_minutes
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }

  dynamic "rules" {
    for_each = var.api_hostname != "" ? [1] : []
    content {
      ref         = "rl_search"
      description = "Search requests per IP/minute"
      expression  = "(${local.search_expr} and http.request.method in {\"GET\" \"POST\"} and not (${local.bot_challenge_exempt_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "search", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "search", ["ip.src", "cf.colo.id"])
        period              = 60
        requests_per_period = var.search_requests_per_minute
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }

  dynamic "rules" {
    for_each = var.api_hostname != "" ? [1] : []
    content {
      ref         = "rl_contact_form"
      description = "Contact/form submissions per IP/10 minutes"
      expression  = "(${local.form_expr} and http.request.method eq \"POST\" and not (${local.bot_challenge_exempt_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "contact_form", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "contact_form", ["ip.src", "cf.colo.id"])
        period              = 600
        requests_per_period = var.form_requests_per_10_minutes
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }

  dynamic "rules" {
    for_each = var.api_hostname != "" ? [1] : []
    content {
      ref         = "rl_api"
      description = "General API requests per IP/minute"
      expression  = "(${local.api_expr} and not (${local.login_path_expr}) and not (${local.reset_path_expr}) and not (${local.search_path_expr}) and not (${local.form_path_expr}) and not (${local.webhook_path_expr}) and not (${local.bot_challenge_exempt_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "api", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "api", ["ip.src", "cf.colo.id"])
        period              = 60
        requests_per_period = var.api_requests_per_minute
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }

  dynamic "rules" {
    for_each = var.admin_hostname != "" ? [1] : []
    content {
      ref         = "rl_admin"
      description = "Administrative requests per IP/minute"
      expression  = "(${local.admin_host_scope} and not (${local.bot_challenge_exempt_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "admin", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "admin", ["ip.src", "cf.colo.id"])
        period              = 60
        requests_per_period = var.admin_requests_per_minute
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }

  dynamic "rules" {
    for_each = var.api_hostname != "" ? [1] : []
    content {
      ref         = "rl_webhook"
      description = "Webhook requests per source/minute; never uses a browser challenge"
      expression  = "(${local.webhook_expr} and http.request.method eq \"POST\" and not (${local.trusted_ip_expr}))"
      action      = lookup(var.rate_limit_actions, "webhook", "log")
      ratelimit {
        characteristics     = lookup(var.rate_limit_characteristics, "webhook", ["ip.src", "cf.colo.id"])
        period              = 60
        requests_per_period = var.webhook_requests_per_minute
        mitigation_timeout  = var.mitigation_timeout_seconds
      }
    }
  }
}
