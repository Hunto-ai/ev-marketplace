variable "project_slug" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "allowed_cidr_blocks" {
  type    = list(string)
  default = []
}

variable "database_name" {
  type = string
}

variable "database_username" {
  type = string
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "instance_class" {
  type = string
}

variable "engine_version" {
  type    = string
  default = "16.3"
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "backup_retention_period" {
  type    = number
  default = 7
}
