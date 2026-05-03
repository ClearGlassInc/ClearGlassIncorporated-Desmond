terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Optional: remote state — uncomment and fill in after first apply
  # backend "s3" {
  #   bucket         = "clearglass-tf-state-206478392741"
  #   key            = "github-runner/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "clearglass-tf-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ClearGlassInc"
      ManagedBy   = "Terraform"
      Component   = "github-runner"
    }
  }
}
