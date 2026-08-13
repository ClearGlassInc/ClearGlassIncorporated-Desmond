terraform {
  # Provider mutation requires durable, encrypted, versioned state with locking.
  # CI supplies this partial S3 backend configuration from a protected GitHub
  # environment. Local syntax validation uses `terraform init -backend=false`.
  backend "s3" {}
}
