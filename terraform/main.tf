terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for infrastructure resources"
  type        = string
  default     = "us-east-1"
}

# TODO: add modules/resources for networking, database, cache, storage, and application hosting.
