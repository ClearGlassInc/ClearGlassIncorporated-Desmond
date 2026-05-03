output "webhook_url" {
  description = "Paste this URL into your GitHub App's webhook settings"
  value       = module.github_runner.webhook.endpoint
}

output "webhook_secret_ssm_path" {
  description = "SSM path holding the webhook secret (for GitHub App config)"
  value       = "/clearglass/github-runner/webhook-secret"
}

output "runner_role_arn" {
  description = "IAM role ARN assumed by EC2 runner instances"
  value       = module.github_runner.runner_role.arn
}

output "scale_up_lambda_arn" {
  description = "Lambda that launches new runners"
  value       = module.github_runner.runners.lambda_scale_up.arn
}

output "scale_down_lambda_arn" {
  description = "Lambda that terminates idle runners"
  value       = module.github_runner.runners.lambda_scale_down.arn
}

output "one_line_summary" {
  description = "Quick-reference summary"
  value = join("\n", [
    "──────────────────────────────────────────",
    "  ClearGlassInc GitHub Runner — LIVE",
    "  Account : 206478392741 (us-east-1)",
    "  Org     : ClearGlassInc",
    "  Labels  : self-hosted, linux, x64, aws-spot, clearglass",
    "  Webhook : ${module.github_runner.webhook.endpoint}",
    "──────────────────────────────────────────",
  ])
}
