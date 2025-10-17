variable "project_slug" {
  type = string
}

variable "environment" {
  type = string
}

variable "cidr_block" {
  type    = string
  default = "10.20.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

variable "create_nat_gateway" {
  type    = bool
  default = true
}
