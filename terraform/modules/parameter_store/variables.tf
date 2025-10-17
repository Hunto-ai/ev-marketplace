variable "path_prefix" {
  type = string
}

variable "parameters" {
  type = map(object({
    value       = string
    type        = optional(string, "SecureString")
    description = optional(string, "")
    overwrite   = optional(bool, true)
  }))
  default = {}
}

variable "tags" {
  type    = map(string)
  default = {}
}
