variable "project_slug" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "repository_url" {
  type = string
}

variable "image_tag" {
  type = string
}

variable "cpu" {
  type = number
}

variable "memory" {
  type = number
}

variable "desired_count" {
  type = number
}

variable "health_check_path" {
  type = string
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "environment_secrets" {
  description = "Map of environment variable name to SSM/Secrets Manager ARN"
  type        = map(string)
  default     = {}
}

variable "egress_cidr_blocks" {
  type    = list(string)
  default = ["0.0.0.0/0"]
}

variable "additional_policy_json" {
  description = "JSON IAM policy document to attach to the App Runner role"
  type        = string
  default     = ""
}
