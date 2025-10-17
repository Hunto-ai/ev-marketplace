locals {
  entries = { for k, v in var.parameters : k => merge(v, {
    name = trimsuffix(var.path_prefix, "/") != "" ? "${trimsuffix(var.path_prefix, "/")}/${k}" : k
  }) }
}

resource "aws_ssm_parameter" "this" {
  for_each    = local.entries
  name        = each.value.name
  description = each.value.description
  type        = lookup(each.value, "type", "SecureString")
  value       = each.value.value
  overwrite   = lookup(each.value, "overwrite", true)
  tags        = var.tags
}

output "parameter_arns" {
  value = { for k, v in aws_ssm_parameter.this : k => v.arn }
}
