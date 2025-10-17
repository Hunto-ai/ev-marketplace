variable "project_slug" {
  description = "Short identifier applied to resource names and tags"
  type        = string
  default     = "evmarket"
}

variable "aws_region" {
  description = "AWS region hosting the primary stack"
  type        = string
  default     = "us-east-2"
}

variable "acm_certificate_region" {
  description = "Region for ACM certificates (us-east-1 if using CloudFront)"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Root domain for public endpoints (optional)"
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for domain validation (optional)"
  type        = string
  default     = ""
}

variable "app_runner_cpu" {
  description = "App Runner CPU in vCPU (0.25 | 0.5 | 1 | 2 | 4)"
  type        = number
  default     = 1
}

variable "app_runner_memory" {
  description = "App Runner memory in GiB (0.5 | 1 | 2 | 4 | 8 | 16)"
  type        = number
  default     = 2
}

variable "app_runner_desired_count" {
  description = "Number of App Runner instances to keep steady"
  type        = number
  default     = 2
}

variable "database_instance_class" {
  description = "Instance class for RDS Postgres"
  type        = string
  default     = "db.t4g.micro"
}

variable "database_allocated_storage" {
  description = "Database storage size in GiB"
  type        = number
  default     = 20
}

variable "database_name" {
  description = "Primary database name"
  type        = string
  default     = "evmarket"
}

variable "database_username" {
  description = "Master username for Postgres"
  type        = string
  default     = "evmarket"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes (1 for single AZ)"
  type        = number
  default     = 1
}

variable "media_bucket_force_destroy" {
  description = "Allow destroying media bucket (disable in production)"
  type        = bool
  default     = false
}

variable "ses_email_identity" {
  description = "Verified SES email or domain identity"
  type        = string
  default     = ""
}

variable "enable_redis" {
  description = "Toggle Redis provisioning"
  type        = bool
  default     = true
}

variable "enable_ses" {
  description = "Toggle SES identity provisioning"
  type        = bool
  default     = false
}

variable "enable_cloudfront" {
  description = "Toggle CloudFront distribution for media bucket"
  type        = bool
  default     = false
}

variable "app_runner_health_check_path" {
  description = "HTTP path used by App Runner for health checks"
  type        = string
  default     = "/healthz"
}

variable "app_runner_image_tag" {
  description = "Image tag to deploy from ECR"
  type        = string
  default     = "latest"
}

variable "parameter_store_path_prefix" {
  description = "SSM parameter path prefix for environment secrets"
  type        = string
  default     = "/evmarket"
}

variable "app_runner_enabled" {
  description = "Toggle creation of App Runner service"
  type        = bool
  default     = false
}
