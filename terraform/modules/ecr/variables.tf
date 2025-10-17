variable "project_slug" {
  type = string
}

variable "environment" {
  type = string
}

variable "image_mutability" {
  type    = string
  default = "MUTABLE"
}

variable "lifecycle_policy" {
  type    = string
  default = ""
}
