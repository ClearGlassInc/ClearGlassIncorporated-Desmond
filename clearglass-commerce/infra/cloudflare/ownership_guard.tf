# RETIRED OWNER GUARD
#
# `infra/edge` is the sole target owner for zone-level edge resources. Keeping
# this configuration in the repository is necessary while historical state is
# inventoried and detached, but an ordinary plan/apply must fail before it can
# race or overwrite the authoritative state.
variable "allow_legacy_edge_stack_mutation" {
  type        = bool
  description = "Emergency migration-only escape hatch. Requires an approved rollback/import procedure and must never be committed true."
  default     = false
}

resource "terraform_data" "retired_edge_stack_guard" {
  lifecycle {
    precondition {
      condition     = var.allow_legacy_edge_stack_mutation
      error_message = "This legacy Cloudflare stack is frozen. Use infra/edge and the protected state-import workflow. Do not create a second zone-phase owner."
    }
  }
}
