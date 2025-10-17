locals {
  name = replace("${var.project_slug}-${var.environment}-app", "_", "-")
}

resource "aws_ecr_repository" "app" {
  name                 = local.name
  image_tag_mutability = var.image_mutability

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "this" {
  count      = var.lifecycle_policy == "" ? 0 : 1
  repository = aws_ecr_repository.app.name
  policy     = var.lifecycle_policy
}

output "repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "repository_arn" {
  value = aws_ecr_repository.app.arn
}

output "repository_name" {
  value = aws_ecr_repository.app.name
}
