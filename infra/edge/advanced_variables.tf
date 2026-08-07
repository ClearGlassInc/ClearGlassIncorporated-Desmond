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

variable "deny_ipv4_cidrs" {
  type        = list(string)
  description = "Confirmed-abuse IPv4 CIDRs for explicit deny rules. Never populate solely from an unverified reputation signal."
  default     = []
}

variable "deny_ipv6_cidrs" {
  type        = list(string)
  description = "Confirmed-abuse IPv6 CIDRs for explicit deny rules. Never populate solely from an unverified reputation signal."
  default     = []
}

variable "quarantine_ipv4_cidrs" {
  type        = list(string)
  description = "Temporary IPv4 quarantine CIDRs challenged rather than permanently denied. Requires a future quarantine_expires_at."
  default     = []
}

variable "quarantine_ipv6_cidrs" {
  type        = list(string)
  description = "Temporary IPv6 quarantine CIDRs challenged rather than permanently denied. Requires a future quarantine_expires_at."
  default     = []
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
}

variable "challenge_asns" {
  type        = list(number)
  description = "ASNs to managed-challenge, enforced only when geo/ASN controls are enabled."
  default     = []
}

check "temporary_quarantine_has_future_expiry" {
  assert {
    condition = length(concat(var.quarantine_ipv4_cidrs, var.quarantine_ipv6_cidrs)) == 0 ? true : (
      can(timecmp(var.quarantine_expires_at, plantimestamp())) ? timecmp(var.quarantine_expires_at, plantimestamp()) > 0 : false
    )
    error_message = "Temporary quarantine CIDRs require quarantine_expires_at to be a valid RFC3339 timestamp later than the current Terraform plan time."
  }
}
