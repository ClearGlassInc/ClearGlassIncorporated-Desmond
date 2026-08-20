variable "account_id" {
  type        = string
  description = "Cloudflare account ID."
  validation {
    condition     = can(regex("^[0-9a-fA-F]{32}$", var.account_id))
    error_message = "account_id must be a 32-character Cloudflare hexadecimal identifier."
  }
}

variable "zone_id" {
  type        = string
  description = "Cloudflare zone ID."
  validation {
    condition     = can(regex("^[0-9a-fA-F]{32}$", var.zone_id))
    error_message = "zone_id must be a 32-character Cloudflare hexadecimal identifier."
  }
}

variable "zone_name" {
  type        = string
  description = "Apex zone name."
  default     = "clearglassinc.com"
  validation {
    condition     = can(regex("^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$", var.zone_name))
    error_message = "zone_name must be a DNS name without a scheme or path."
  }
}

variable "public_hostname" {
  type        = string
  description = "Public hostname protected by the edge."
  default     = "www.clearglassinc.com"
  validation {
    condition     = can(regex("^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$", var.public_hostname))
    error_message = "public_hostname must be a DNS hostname without a scheme or path."
  }
}

variable "api_hostname" {
  type        = string
  description = "Optional future dynamic API hostname. Empty disables API-specific Terraform rules."
  default     = ""
  validation {
    condition     = var.api_hostname == "" || can(regex("^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$", var.api_hostname))
    error_message = "api_hostname must be empty or a DNS hostname without a scheme or path."
  }
}

variable "admin_hostname" {
  type        = string
  description = "Optional future administrative hostname. Empty disables admin-specific Terraform rules."
  default     = ""
  validation {
    condition     = var.admin_hostname == "" || can(regex("^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$", var.admin_hostname))
    error_message = "admin_hostname must be empty or a DNS hostname without a scheme or path."
  }
}

variable "policy_version" {
  type        = string
  description = "Provider deployment policy version recorded with plans and audit evidence."
  default     = "2.0.0"
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+$", var.policy_version))
    error_message = "policy_version must be a semantic version such as 2.0.0."
  }
}

variable "rollout_stage" {
  type        = string
  description = "Reviewed deployment stage governing active provider features and terminal actions."
  default     = "disabled"
  validation {
    condition     = contains(["disabled", "observe", "challenge", "enforce"], var.rollout_stage)
    error_message = "rollout_stage must be disabled, observe, challenge, or enforce."
  }
}

variable "promotion_evidence_sha256" {
  type        = string
  description = "SHA-256 of the reviewed observation report supporting challenge/enforce promotion."
  default     = ""
  validation {
    condition     = var.promotion_evidence_sha256 == "" || can(regex("^[0-9a-f]{64}$", var.promotion_evidence_sha256))
    error_message = "promotion_evidence_sha256 must be empty or a lowercase SHA-256 digest."
  }
}

variable "observation_window_start" {
  type        = string
  description = "RFC3339 start of the evidence window supporting a challenge/enforce promotion."
  default     = ""
}

variable "observation_window_end" {
  type        = string
  description = "RFC3339 end of the evidence window supporting a challenge/enforce promotion."
  default     = ""
}

variable "deployment_owner" {
  type        = string
  description = "Accountable owner for an enabled provider configuration."
  default     = ""
  validation {
    condition     = var.deployment_owner == "" || can(regex("^[A-Za-z0-9][A-Za-z0-9 ._@/-]{1,127}$", var.deployment_owner))
    error_message = "deployment_owner must be empty or a conventional 2-128 character identity."
  }
}

variable "deployment_change_ticket" {
  type        = string
  description = "Approved change/incident reference for an enabled provider configuration."
  default     = ""
  validation {
    condition     = var.deployment_change_ticket == "" || can(regex("^[A-Za-z0-9][A-Za-z0-9._:/-]{1,127}$", var.deployment_change_ticket))
    error_message = "deployment_change_ticket must be empty or a conventional 2-128 character reference without whitespace."
  }
}

variable "configuration_rationale" {
  type        = string
  description = "Reason for the current provider rollout stage and feature selection."
  default     = "Safe repository baseline; no provider mutation enabled."
}

variable "enable_custom_waf" {
  type        = bool
  description = "Create custom WAF rules. Leave false for the first plan until phase ownership/action support is confirmed."
  default     = false
}

variable "enable_managed_waf" {
  type        = bool
  description = "Execute Cloudflare Managed Ruleset when zone plan and phase ownership are confirmed."
  default     = false
}

variable "enable_rate_limits" {
  type        = bool
  description = "Create route rate-limit rules. Disabled by default for an observation-first rollout."
  default     = false
}

variable "enable_security_headers" {
  type        = bool
  description = "Create response-header transform rules."
  default     = false
}

variable "csp_mode" {
  type        = string
  description = "CSP response mode. Enforcement is allowed only after reviewed report evidence in the enforce rollout stage."
  default     = "report-only"
  validation {
    condition     = contains(["report-only", "enforce"], var.csp_mode)
    error_message = "csp_mode must be report-only or enforce."
  }
}

variable "csp_report_uri" {
  type        = string
  description = "Optional HTTPS CSP collector URI on the protected API hostname. Runtime rendering restricts it to /api/security/csp-report."
  default     = ""
  validation {
    condition = var.csp_report_uri == "" || can(regex(
      "^https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?/api/security/csp-report$",
      var.csp_report_uri
    ))
    error_message = "csp_report_uri must be empty or an HTTPS /api/security/csp-report URL without query or fragment."
  }
}

variable "enable_logpush" {
  type        = bool
  description = "Create firewall-events Logpush job. Requires a validated destination."
  default     = false
}

variable "enable_geo_asn_rules" {
  type        = bool
  description = "Enable country/ASN enforcement. Must remain false unless explicitly approved."
  default     = false
}

variable "enable_emergency_mode" {
  type        = bool
  description = "Enable temporary high-security mode. Must be reverted promptly after incident containment."
  default     = false
}

variable "custom_waf_actions" {
  type        = map(string)
  description = "Per-rule staged actions. Keeping rules independent avoids promoting every custom detection at once. 'log' may require an Enterprise plan."
  default = {
    unexpected_method = "log"
    path_probe        = "log"
    suspicious_ua     = "log"
    request_size      = "log"
    request_body      = "log"
  }
  validation {
    condition = (
      length(setsubtract(toset(keys(var.custom_waf_actions)), toset([
        "unexpected_method", "path_probe", "suspicious_ua", "request_size", "request_body"
      ]))) == 0 &&
      alltrue([for action in values(var.custom_waf_actions) : contains(["log", "managed_challenge", "block"], action)])
    )
    error_message = "custom_waf_actions contains an unknown rule key or unsupported action."
  }
}

variable "managed_waf_override_action" {
  type        = string
  description = "Override for Cloudflare Managed/OWASP rules. Start with log where the plan supports it."
  default     = "log"
  validation {
    condition     = contains(["log", "managed_challenge", "block"], var.managed_waf_override_action)
    error_message = "managed_waf_override_action must be log, managed_challenge, or block."
  }
}

variable "rate_limit_actions" {
  type        = map(string)
  description = "Per-route rate-limit actions. Webhooks must never receive a browser challenge. 'log' may require an Enterprise plan."
  default = {
    static_assets  = "log"
    html           = "log"
    login          = "log"
    password_reset = "log"
    search         = "log"
    contact_form   = "log"
    api            = "log"
    admin          = "log"
    webhook        = "log"
  }
  validation {
    condition = (
      length(setsubtract(toset(keys(var.rate_limit_actions)), toset([
        "static_assets", "html", "login", "password_reset", "search",
        "contact_form", "api", "admin", "webhook"
      ]))) == 0 &&
      alltrue([for action in values(var.rate_limit_actions) : contains(["log", "managed_challenge", "block"], action)]) &&
      lookup(var.rate_limit_actions, "webhook", "log") != "managed_challenge"
    )
    error_message = "rate_limit_actions contains an unknown route/action, or assigns managed_challenge to webhooks."
  }
}

variable "rate_limit_characteristics" {
  type        = map(list(string))
  description = "Provider-native counter keys by route. Defaults are per-IP/per-colo for Cloudflare non-Enterprise compatibility; identity, token, country, ASN, or bot-score fields require plan and privacy review."
  default = {
    static_assets  = ["ip.src", "cf.colo.id"]
    html           = ["ip.src", "cf.colo.id"]
    login          = ["ip.src", "cf.colo.id"]
    password_reset = ["ip.src", "cf.colo.id"]
    search         = ["ip.src", "cf.colo.id"]
    contact_form   = ["ip.src", "cf.colo.id"]
    api            = ["ip.src", "cf.colo.id"]
    admin          = ["ip.src", "cf.colo.id"]
    webhook        = ["ip.src", "cf.colo.id"]
  }
  validation {
    condition = (
      length(setsubtract(toset(keys(var.rate_limit_characteristics)), toset([
        "static_assets", "html", "login", "password_reset", "search",
        "contact_form", "api", "admin", "webhook"
      ]))) == 0 &&
      alltrue([for fields in values(var.rate_limit_characteristics) : length(fields) > 0 && length(fields) <= 5])
    )
    error_message = "rate_limit_characteristics contains an unknown route or an empty/excessive characteristic list."
  }
}

variable "trusted_ipv4_cidrs" {
  type        = list(string)
  description = "Explicit trusted IPv4 CIDRs. Keep minimal."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.trusted_ipv4_cidrs : can(cidrhost(cidr, 0)) && !strcontains(cidr, ":")])
    error_message = "trusted_ipv4_cidrs must contain IPv4 CIDR notation."
  }
}

variable "trusted_ipv6_cidrs" {
  type        = list(string)
  description = "Explicit trusted IPv6 CIDRs. Keep minimal."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.trusted_ipv6_cidrs : can(cidrhost(cidr, 0)) && strcontains(cidr, ":")])
    error_message = "trusted_ipv6_cidrs must contain IPv6 CIDR notation."
  }
}

variable "trusted_asns" {
  type        = list(number)
  description = "Trusted ASNs used only when geo/ASN controls are explicitly enabled."
  default     = []
  validation {
    condition     = alltrue([for asn in var.trusted_asns : asn >= 1 && asn <= 4294967295 && asn == floor(asn)])
    error_message = "trusted_asns must contain integer ASNs in the valid 32-bit range."
  }
}

variable "allowed_countries" {
  type        = list(string)
  description = "Country codes explicitly allowed by an enabled geo policy. Empty means no allow-only policy."
  default     = []
  validation {
    condition     = alltrue([for country in var.allowed_countries : can(regex("^[A-Za-z]{2}$", country))])
    error_message = "allowed_countries must contain two-letter country codes."
  }
}

variable "denied_countries" {
  type        = list(string)
  description = "Country codes denied only when geo enforcement is enabled."
  default     = []
  validation {
    condition     = alltrue([for country in var.denied_countries : can(regex("^[A-Za-z]{2}$", country))])
    error_message = "denied_countries must contain two-letter country codes."
  }
}

variable "challenge_countries" {
  type        = list(string)
  description = "Country codes challenged only when geo enforcement is enabled."
  default     = []
  validation {
    condition     = alltrue([for country in var.challenge_countries : can(regex("^[A-Za-z]{2}$", country))])
    error_message = "challenge_countries must contain two-letter country codes."
  }
}

variable "static_asset_requests_per_minute" {
  type    = number
  default = 600
  validation {
    condition     = var.static_asset_requests_per_minute >= 60 && var.static_asset_requests_per_minute <= 1000000
    error_message = "static_asset_requests_per_minute must be between 60 and 1,000,000."
  }
}

variable "html_requests_per_minute" {
  type    = number
  default = 120
  validation {
    condition     = var.html_requests_per_minute >= 30 && var.html_requests_per_minute <= 1000000
    error_message = "html_requests_per_minute must be between 30 and 1,000,000."
  }
}

variable "login_requests_per_minute" {
  type    = number
  default = 20
  validation {
    condition     = var.login_requests_per_minute >= 5 && var.login_requests_per_minute <= 100000
    error_message = "login_requests_per_minute must be between 5 and 100,000."
  }
}

variable "reset_requests_per_10_minutes" {
  type    = number
  default = 8
  validation {
    condition     = var.reset_requests_per_10_minutes >= 3 && var.reset_requests_per_10_minutes <= 100000
    error_message = "reset_requests_per_10_minutes must be between 3 and 100,000."
  }
}

variable "search_requests_per_minute" {
  type    = number
  default = 60
  validation {
    condition     = var.search_requests_per_minute >= 10 && var.search_requests_per_minute <= 1000000
    error_message = "search_requests_per_minute must be between 10 and 1,000,000."
  }
}

variable "form_requests_per_10_minutes" {
  type    = number
  default = 10
  validation {
    condition     = var.form_requests_per_10_minutes >= 3 && var.form_requests_per_10_minutes <= 100000
    error_message = "form_requests_per_10_minutes must be between 3 and 100,000."
  }
}

variable "api_requests_per_minute" {
  type    = number
  default = 120
  validation {
    condition     = var.api_requests_per_minute >= 30 && var.api_requests_per_minute <= 1000000
    error_message = "api_requests_per_minute must be between 30 and 1,000,000."
  }
}

variable "admin_requests_per_minute" {
  type    = number
  default = 60
  validation {
    condition     = var.admin_requests_per_minute >= 10 && var.admin_requests_per_minute <= 100000
    error_message = "admin_requests_per_minute must be between 10 and 100,000."
  }
}

variable "webhook_requests_per_minute" {
  type    = number
  default = 300
  validation {
    condition     = var.webhook_requests_per_minute >= 30 && var.webhook_requests_per_minute <= 1000000
    error_message = "webhook_requests_per_minute must be between 30 and 1,000,000."
  }
}

variable "mitigation_timeout_seconds" {
  type    = number
  default = 600
  validation {
    condition     = var.mitigation_timeout_seconds >= 10 && var.mitigation_timeout_seconds <= 86400
    error_message = "mitigation_timeout_seconds must be between 10 seconds and 24 hours."
  }
}

variable "hsts_include_subdomains" {
  type        = bool
  description = "Add includeSubDomains only after every subdomain is confirmed HTTPS-ready."
  default     = false
}

variable "hsts_preload" {
  type        = bool
  description = "Add HSTS preload only after includeSubDomains is approved and preload requirements are met."
  default     = false
  validation {
    condition     = !var.hsts_preload || var.hsts_include_subdomains
    error_message = "hsts_preload requires hsts_include_subdomains=true."
  }
}

variable "logpush_destination" {
  type        = string
  description = "Validated Logpush destination URI. Treat as sensitive if it embeds credentials."
  default     = ""
  sensitive   = true
}

variable "log_full_client_ip" {
  type        = bool
  description = "Include full ClientIP in exported firewall events only when incident/retention requirements justify it."
  default     = false
}
