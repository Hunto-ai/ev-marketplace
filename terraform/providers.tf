terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = var.project_slug
      Stack   = "ev-marketplace"
    }
  }
}

provider "aws" {
  alias  = "acm"
  region = var.acm_certificate_region
}

provider "random" {}
