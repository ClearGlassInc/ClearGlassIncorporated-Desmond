# ─────────────────────────────────────────────────────────────────────────────
# ClearGlassInc — Auto-Scaling Self-Hosted GitHub Actions Runners on AWS
# Account : 206478392741   Region: us-east-1   Scope: org (ClearGlassInc)
#
# Module: philips-labs/github-runner/aws
#   - Webhook Lambda receives GitHub job events
#   - Scale-up Lambda launches EC2 spot runners on demand
#   - Scale-down Lambda terminates idle runners (scales to zero)
#   - Runners register themselves, run the job, then terminate
# ─────────────────────────────────────────────────────────────────────────────

# ── Network: use the default VPC (no cost, always present) ──────────────────
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "defaultForAz"
    values = ["true"]
  }
}

# ── Webhook secret (auto-generated, stored in SSM by the module) ─────────────
resource "random_password" "webhook_secret" {
  length  = 32
  special = false
}

# ── AMI: latest Amazon Linux 2 for runners ──────────────────────────────────
data "aws_ami" "runner" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-kernel-5*-x86_64-gp2"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
}

# ── GitHub Actions Runner Module ─────────────────────────────────────────────
module "github_runner" {
  source  = "philips-labs/github-runner/aws"
  version = "~> 5.0"

  aws_region    = var.aws_region
  vpc_id        = data.aws_vpc.default.id
  subnet_ids    = data.aws_subnets.default.ids

  prefix = "clearglass"

  # GitHub App credentials (populated by bootstrap.sh via SSM / env vars)
  github_app = {
    key_base64     = var.github_app_key_base64
    id             = var.github_app_id
    webhook_secret = random_password.webhook_secret.result
  }

  # ── Runner configuration ──────────────────────────────────────────────────
  runners = {
    clearglass = {
      # Identify runners in GitHub UI
      runner_extra_labels = ["clearglass", "linux", "x64", "aws-spot"]

      # OS / arch
      runner_os   = "linux"
      runner_arch = "x64"

      # Org-level: all ClearGlassInc repos share this pool
      enable_organization_runners = true

      # Spot instances — up to 90% cheaper than on-demand
      instance_types = var.runner_instance_types
      market_options = "spot"

      # Scale-to-zero: no idle runners when queue is empty
      idle_config = []

      # Terminate runners after they've been idle this many minutes
      minimum_running_time_in_minutes = 5

      # Hard cap (prevents runaway costs)
      runners_maximum_count = var.runner_max_instances

      # AMI
      ami_filter = {
        name  = ["amzn2-ami-kernel-5*-x86_64-gp2"]
        state = ["available"]
      }
      ami_owners = ["amazon"]

      # EBS root volume
      block_device_mappings = [{
        device_name           = "/dev/xvda"
        delete_on_termination = true
        volume_size           = var.runner_volume_size_gb
        volume_type           = "gp3"
        encrypted             = true
        iops                  = null
        throughput            = null
        snapshot_id           = null
      }]

      # Run as non-root
      runner_run_as = "ec2-user"

      # User-data: install full ClearGlassInc toolchain on each runner
      userdata_template = "${path.module}/runner-userdata.sh"

      # IAM extras: allow SSM Session Manager (no SSH needed)
      role_runner_arn = null  # module creates default role
    }
  }

  # ── Webhook Lambda settings ────────────────────────────────────────────────
  webhook_lambda_s3_key    = null
  webhook_lambda_s3_bucket = null

  # ── Scale-up/down Lambda settings ─────────────────────────────────────────
  runners_lambda_s3_key    = null
  runners_lambda_s3_bucket = null

  # ── Tags ──────────────────────────────────────────────────────────────────
  tags = {
    Environment = var.environment
    Owner       = "ClearGlassInc"
    AccountID   = var.aws_account_id
  }
}
