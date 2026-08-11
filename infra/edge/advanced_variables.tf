variable "enable_bot_management" {
  type        = bool
  description = "Manage Cloudflare Super Bot Fight Mode/Bot Management settings. Default off because another Terraform state may already own the zone setting and plan availability varies."
  default     = false
}

variable "bot_definitely_automated_action" {
  type        = string
  description = "Action for traffic Cloudflare classifies as definitely automated."
  default     = "managed_challenge"
  validation {
    condition     = contains(["allow", "managed_challenge", "block"], var.bot_definitely_automated_action)
    error_message = "bot_definitely_automated_action must be allow, managed_challenge, or block."
  }
}

variable "bot_likely_automated_action" {
  type        = string
  description = "Action for traffic Cloudflare classifies as likely automated."
  default     = "managed_challenge"
  validation {
    condition     = contains(["allow", "managed_challenge", "block"], var.bot_likely_automated_action)
    error_message = "bot_likely_automated_action must be allow, managed_challenge, or block."
  }
}

variable "enable_bot_score_rule" {
  type        = bool
  description = "Enable the plan-specific Bot Management score rule in the custom WAF phase. Off until field availability and phase ownership are confirmed."
  default     = false
}

variable "bot_score_threshold" {
  type        = number
  description = "Challenge/log unverified traffic with a Bot Management score below this value."
  default     = 10
  validation {
    condition     = var.bot_score_threshold >= 1 && var.bot_score_threshold <= 29
    error_message = "bot_score_threshold must be between 1 and 29."
  }
}

variable "bot_score_action" {
  type        = string
  description = "Staged action for the optional Bot Management score rule."
  default     = "log"
  validation {
    condition     = contains(["log", "managed_challenge", "block"], var.bot_score_action)
    error_message = "bot_score_action must be log, managed_challenge, or block."
  }
}

variable "monitoring_ipv4_cidrs" {
  type        = list(string)
  description = "Known monitoring-service IPv4 CIDRs exempted from generic bot challenges and edge rate limits, but not from managed exploit inspection."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.monitoring_ipv4_cidrs : can(cidrhost(cidr, 0)) && !strcontains(cidr, ":")])
    error_message = "monitoring_ipv4_cidrs must contain IPv4 CIDR notation."
  }
}

variable "monitoring_ipv6_cidrs" {
  type        = list(string)
  description = "Known monitoring-service IPv6 CIDRs exempted from generic bot challenges and edge rate limits, but not from managed exploit inspection."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.monitoring_ipv6_cidrs : can(cidrhost(cidr, 0)) && strcontains(cidr, ":")])
    error_message = "monitoring_ipv6_cidrs must contain IPv6 CIDR notation."
  }
}

variable "internal_automation_ipv4_cidrs" {
  type        = list(string)
  description = "Approved internal-automation IPv4 CIDRs exempted from generic bot challenges and edge rate limits. Keep minimal and reviewed."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.internal_automation_ipv4_cidrs : can(cidrhost(cidr, 0)) && !strcontains(cidr, ":")])
    error_message = "internal_automation_ipv4_cidrs must contain IPv4 CIDR notation."
  }
}

variable "internal_automation_ipv6_cidrs" {
  type        = list(string)
  description = "Approved internal-automation IPv6 CIDRs exempted from generic bot challenges and edge rate limits. Keep minimal and reviewed."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.internal_automation_ipv6_cidrs : can(cidrhost(cidr, 0)) && strcontains(cidr, ":")])
    error_message = "internal_automation_ipv6_cidrs must contain IPv6 CIDR notation."
  }
}

variable "deny_ipv4_cidrs" {
  type        = list(string)
  description = "Confirmed-abuse IPv4 CIDRs for explicit deny rules. Never populate solely from an unverified reputation signal."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.deny_ipv4_cidrs : can(cidrhost(cidr, 0)) && !strcontains(cidr, ":")])
    error_message = "deny_ipv4_cidrs must contain IPv4 CIDR notation."
  }
}

variable "deny_ipv6_cidrs" {
  type        = list(string)
  description = "Confirmed-abuse IPv6 CIDRs for explicit deny rules. Never populate solely from an unverified reputation signal."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.deny_ipv6_cidrs : can(cidrhost(cidr, 0)) && strcontains(cidr, ":")])
    error_message = "deny_ipv6_cidrs must contain IPv6 CIDR notation."
  }
}

variable "quarantine_ipv4_cidrs" {
  type        = list(string)
  description = "Temporary IPv4 quarantine CIDRs challenged rather than permanently denied. Requires a future quarantine_expires_at."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.quarantine_ipv4_cidrs : can(cidrhost(cidr, 0)) && !strcontains(cidr, ":")])
    error_message = "quarantine_ipv4_cidrs must contain IPv4 CIDR notation."
  }
}

variable "quarantine_ipv6_cidrs" {
  type        = list(string)
  description = "Temporary IPv6 quarantine CIDRs challenged rather than permanently denied. Requires a future quarantine_expires_at."
  default     = []
  validation {
    condition     = alltrue([for cidr in var.quarantine_ipv6_cidrs : can(cidrhost(cidr, 0)) && strcontains(cidr, ":")])
    error_message = "quarantine_ipv6_cidrs must contain IPv6 CIDR notation."
  }
}

variable "quarantine_expires_at" {
  type        = string
  description = "RFC3339 expiry for temporary quarantine lists. Empty only when quarantine lists are empty."
  default     = ""
}

variable "denied_asns" {
  type        = list(number)
  description = "Explicit confirmed-abuse ASNs, enforced only when geo/ASN controls are enabled."
  default     = []
  validation {
    condition     = alltrue([for asn in var.denied_asns : asn >= 1 && asn <= 4294967295 && asn == floor(asn)])
    error_message = "denied_asns must contain integer ASNs in the valid 32-bit range."
  }
}

variable "challenge_asns" {
  type        = list(number)
  description = "ASNs to managed-challenge, enforced only when geo/ASN controls are enabled."
  default     = []
  validation {
    condition     = alltrue([for asn in var.challenge_asns : asn >= 1 && asn <= 4294967295 && asn == floor(asn)])
    error_message = "challenge_asns must contain integer ASNs in the valid 32-bit range."
  }
}

variable "geo_exception_countries" {
  type        = list(string)
  description = "Country-code exceptions to explicitly enabled deny/challenge rules. Does not create a broad allow rule."
  default     = []
  validation {
    condition     = alltrue([for country in var.geo_exception_countries : can(regex("^[A-Za-z]{2}$", country))])
    error_message = "geo_exception_countries must contain two-letter country codes."
  }
}

variable "enable_provider_reputation_rules" {
  type        = bool
  description = "Enable provider threat-score and named-list reputation rules after Cloudflare plan/field/list availability is confirmed."
  default     = false
}

variable "provider_threat_score_threshold" {
  type        = number
  description = "Provider threat score at which to log/challenge traffic. Never used as a permanent deny signal by this module."
  default     = 20
  validation {
    condition     = var.provider_threat_score_threshold >= 1 && var.provider_threat_score_threshold <= 100
    error_message = "provider_threat_score_threshold must be between 1 and 100."
  }
}

variable "provider_reputation_action" {
  type        = string
  description = "Action for provider reputation signals; block is deliberately unavailable because reputation alone is not verified abuse."
  default     = "log"
  validation {
    condition     = contains(["log", "managed_challenge"], var.provider_reputation_action)
    error_message = "provider_reputation_action must be log or managed_challenge."
  }
}

variable "anonymous_network_ip_list_name" {
  type        = string
  description = "Optional pre-existing Cloudflare IP List name for reviewed anonymous proxy/VPN sources. List creation and stewardship are manual/provider-side."
  default     = ""
  validation {
    condition     = var.anonymous_network_ip_list_name == "" || can(regex("^[a-z][a-z0-9_]{0,49}$", var.anonymous_network_ip_list_name))
    error_message = "anonymous_network_ip_list_name must be empty or a valid Cloudflare IP List name."
  }
}

variable "tor_exit_ip_list_name" {
  type        = string
  description = "Optional pre-existing Cloudflare IP List name for Tor exit nodes. Default handling is log-only and route sensitivity must be reviewed."
  default     = ""
  validation {
    condition     = var.tor_exit_ip_list_name == "" || can(regex("^[a-z][a-z0-9_]{0,49}$", var.tor_exit_ip_list_name))
    error_message = "tor_exit_ip_list_name must be empty or a valid Cloudflare IP List name."
  }
}

variable "enable_origin_auth_header" {
  type        = bool
  description = "Inject a shared origin-auth header only for configured API/admin origins. GitHub Pages cannot validate this control."
  default     = false
}

variable "origin_auth_header_name" {
  type        = string
  description = "Request header overwritten by the edge and validated at each dynamic origin."
  default     = "X-ClearGlass-Edge-Origin"
  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9-]{1,62}$", var.origin_auth_header_name))
    error_message = "origin_auth_header_name must be a conventional HTTP header name."
  }
}

variable "origin_auth_header_value" {
  type        = string
  description = "High-entropy shared origin-auth value. Stored only in protected CI secrets and encrypted Terraform state."
  default     = ""
  sensitive   = true
}

variable "emergency_expires_at" {
  type        = string
  description = "RFC3339 expiry for emergency mode. Required when enabled and limited to 24 hours from plan time."
  default     = ""
}

variable "emergency_owner" {
  type        = string
  description = "Named operator accountable for the temporary emergency rule."
  default     = ""
}

variable "emergency_change_ticket" {
  type        = string
  description = "Incident/change reference authorizing emergency mode."
  default     = ""
}

variable "max_uri_bytes" {
  type        = number
  description = "Observe/challenge requests whose raw URI exceeds this byte length. Tune from legitimate traffic before blocking."
  default     = 16384
  validation {
    condition     = var.max_uri_bytes >= 4096
    error_message = "max_uri_bytes must be at least 4096 to avoid an unsafe low limit."
  }
}

variable "max_query_bytes" {
  type        = number
  description = "Observe/challenge requests whose raw query string exceeds this byte length."
  default     = 8192
  validation {
    condition     = var.max_query_bytes >= 2048
    error_message = "max_query_bytes must be at least 2048 to avoid an unsafe low limit."
  }
}

variable "max_single_header_value_bytes" {
  type        = number
  description = "Observe/challenge requests containing an individual header value larger than this threshold."
  default     = 8192
  validation {
    condition     = var.max_single_header_value_bytes >= 2048
    error_message = "max_single_header_value_bytes must be at least 2048."
  }
}

variable "enable_enterprise_body_size_rule" {
  type        = bool
  description = "Enable body-size/truncation custom-rule fields that require the applicable Cloudflare plan."
  default     = false
}

variable "max_request_body_bytes" {
  type        = number
  description = "Maximum request body byte threshold when the plan-specific body-size rule is enabled."
  default     = 1048576
  validation {
    condition     = var.max_request_body_bytes >= 65536
    error_message = "max_request_body_bytes must be at least 65536."
  }
}

check "temporary_quarantine_has_future_expiry" {
  assert {
    condition = length(concat(var.quarantine_ipv4_cidrs, var.quarantine_ipv6_cidrs)) == 0 ? true : (
      can(timecmp(var.quarantine_expires_at, plantimestamp())) ? timecmp(var.quarantine_expires_at, plantimestamp()) > 0 : false
    )
    error_message = "Temporary quarantine CIDRs require quarantine_expires_at to be a valid RFC3339 timestamp later than the current Terraform plan time."
  }
}

check "protected_hostnames_are_distinct" {
  assert {
    condition = length(distinct(compact([
      var.public_hostname,
      var.api_hostname,
      var.admin_hostname,
      ]))) == length(compact([
      var.public_hostname,
      var.api_hostname,
      var.admin_hostname,
    ]))
    error_message = "public_hostname, api_hostname, and admin_hostname must not duplicate one another."
  }
}

check "protected_hostnames_belong_to_zone" {
  assert {
    condition = alltrue([
      for hostname in compact([var.public_hostname, var.api_hostname, var.admin_hostname]) :
      lower(hostname) == lower(var.zone_name) || endswith(lower(hostname), ".${lower(var.zone_name)}")
    ])
    error_message = "Every public, API, and admin hostname must belong to zone_name."
  }
}

check "geo_and_asn_sets_do_not_conflict" {
  assert {
    condition = (
      length(setintersection(toset([for c in var.denied_countries : upper(c)]), toset([for c in concat(var.allowed_countries, var.geo_exception_countries) : upper(c)]))) == 0 &&
      length(setintersection(toset([for c in var.challenge_countries : upper(c)]), toset([for c in var.geo_exception_countries : upper(c)]))) == 0 &&
      length(setintersection(toset(var.denied_asns), toset(var.trusted_asns))) == 0 &&
      length(setintersection(toset(var.challenge_asns), toset(var.trusted_asns))) == 0
    )
    error_message = "Denied/challenged countries or ASNs must not overlap explicit trusted/exception sets."
  }
}

check "origin_auth_is_dynamic_only_and_configured" {
  assert {
    condition = !var.enable_origin_auth_header ? true : (
      length(compact([var.api_hostname, var.admin_hostname])) > 0 &&
      length(var.origin_auth_header_value) >= 32
    )
    error_message = "Origin authentication requires an API/admin hostname and an origin_auth_header_value of at least 32 characters. It cannot be applied to GitHub Pages."
  }
}

check "emergency_mode_is_time_bounded" {
  assert {
    condition = !var.enable_emergency_mode ? true : (
      trimspace(var.emergency_owner) != "" &&
      trimspace(var.emergency_change_ticket) != "" &&
      (can(timecmp(var.emergency_expires_at, plantimestamp())) ? (
        timecmp(var.emergency_expires_at, plantimestamp()) > 0 &&
        timecmp(var.emergency_expires_at, timeadd(plantimestamp(), "24h")) <= 0
      ) : false)
    )
    error_message = "Emergency mode requires owner, change ticket, and a valid RFC3339 expiry within the next 24 hours."
  }
}

check "custom_phase_features_have_one_owner" {
  assert {
    condition = (
      (!var.enable_bot_score_rule || var.enable_custom_waf) &&
      (!var.enable_provider_reputation_rules || var.enable_custom_waf) &&
      (!var.enable_geo_asn_rules || var.enable_custom_waf) &&
      (!var.enable_enterprise_body_size_rule || var.enable_custom_waf) &&
      (!var.enable_emergency_mode || var.enable_custom_waf)
    )
    error_message = "Bot-score, reputation, geo/ASN, body-size, and emergency custom rules require enable_custom_waf=true because they share that single zone phase."
  }
}

check "zone_wide_bot_mode_does_not_break_dynamic_clients" {
  assert {
    condition = !var.enable_bot_management ? true : (
      length(compact([var.api_hostname, var.admin_hostname])) == 0 || (
        var.bot_definitely_automated_action == "allow" &&
        var.bot_likely_automated_action == "allow"
      )
    )
    error_message = "Super Bot Fight Mode is zone-wide. With API/admin hostnames configured, keep SBFM automation actions at allow and use the scoped custom bot-score rule instead."
  }
}

check "enabled_configuration_has_change_control" {
  assert {
    condition = !local.provider_mutation_enabled ? true : (
      var.rollout_stage != "disabled" &&
      trimspace(var.deployment_owner) != "" &&
      trimspace(var.deployment_change_ticket) != "" &&
      length(trimspace(var.configuration_rationale)) >= 10
    )
    error_message = "Enabled provider features require a non-disabled rollout_stage, deployment owner, change ticket, and meaningful rationale."
  }
}

check "disabled_stage_has_no_provider_mutation" {
  assert {
    condition     = (var.rollout_stage == "disabled") == (!local.provider_mutation_enabled)
    error_message = "rollout_stage must be disabled exactly when every provider-mutating feature flag is false."
  }
}

check "observe_stage_is_nonterminating" {
  assert {
    condition = var.rollout_stage != "observe" ? true : (
      (!var.enable_custom_waf || alltrue([for action in values(var.custom_waf_actions) : action == "log"])) &&
      (!var.enable_managed_waf || var.managed_waf_override_action == "log") &&
      (!var.enable_rate_limits || alltrue([for action in values(var.rate_limit_actions) : action == "log"])) &&
      (!var.enable_bot_score_rule || var.bot_score_action == "log") &&
      (!var.enable_provider_reputation_rules || var.provider_reputation_action == "log") &&
      !var.enable_bot_management &&
      !var.enable_geo_asn_rules &&
      !var.enable_emergency_mode
    )
    error_message = "Observe stage permits only nonterminating log actions; zone-wide bot, geo/ASN, and emergency controls must remain off."
  }
}

check "terminal_actions_require_enforce_stage" {
  assert {
    condition = var.rollout_stage == "enforce" || !(
      (var.enable_custom_waf && contains(values(var.custom_waf_actions), "block")) ||
      (var.enable_custom_waf && length(concat(var.deny_ipv4_cidrs, var.deny_ipv6_cidrs)) > 0) ||
      (var.enable_managed_waf && var.managed_waf_override_action == "block") ||
      (var.enable_rate_limits && contains(values(var.rate_limit_actions), "block")) ||
      (var.enable_bot_score_rule && var.bot_score_action == "block") ||
      (var.enable_bot_management && contains([
        var.bot_definitely_automated_action,
        var.bot_likely_automated_action,
      ], "block")) ||
      (var.enable_geo_asn_rules && (length(var.denied_countries) + length(var.denied_asns)) > 0)
    )
    error_message = "Block actions and explicit deny lists require rollout_stage=enforce."
  }
}

check "challenge_actions_require_challenge_or_enforce_stage" {
  assert {
    condition = contains(["challenge", "enforce"], var.rollout_stage) || !(
      (var.enable_custom_waf && contains(values(var.custom_waf_actions), "managed_challenge")) ||
      (var.enable_managed_waf && var.managed_waf_override_action == "managed_challenge") ||
      (var.enable_rate_limits && contains(values(var.rate_limit_actions), "managed_challenge")) ||
      (var.enable_bot_score_rule && var.bot_score_action == "managed_challenge") ||
      var.enable_bot_management ||
      var.enable_geo_asn_rules ||
      var.enable_emergency_mode
    )
    error_message = "Challenge-capable actions require rollout_stage=challenge or enforce."
  }
}

check "high_impact_controls_require_enforce_stage" {
  assert {
    condition = var.rollout_stage == "enforce" || !(
      var.enable_origin_auth_header ||
      var.log_full_client_ip ||
      var.hsts_include_subdomains ||
      var.hsts_preload
    )
    error_message = "Origin authentication, full client-IP export, and expanded HSTS scope require rollout_stage=enforce and explicit change control."
  }
}
