# Partial S3 backend configuration. Store the real file as the base64-encoded
# EDGE_TF_BACKEND_CONFIG_B64 GitHub environment secret; never commit credentials.
# Use a different key for staging and production.

bucket       = "REPLACE_WITH_VERSIONED_PRIVATE_STATE_BUCKET"
key          = "clearglass/edge/staging/terraform.tfstate"
region       = "ca-central-1"
encrypt      = true
use_lockfile = true

# For an operator-approved S3-compatible service, add its documented `endpoints`
# and validation flags here. The CI gate still requires locking; a backend that
# cannot provide reliable state locking is not accepted for provider mutation.
