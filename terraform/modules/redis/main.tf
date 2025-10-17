locals {
  name_prefix = "${var.project_slug}-${var.environment}"
}

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis"
  description = "Redis access"
  vpc_id      = var.vpc_id

  dynamic "ingress" {
    for_each = length(var.allowed_security_group_ids) > 0 ? var.allowed_security_group_ids : []
    content {
      description              = "Redis"
      from_port                = 6379
      to_port                  = 6379
      protocol                 = "tcp"
      security_groups          = [ingress.value]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-redis"
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis-subnets"
  subnet_ids = var.subnet_ids
}

resource "random_password" "auth" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "redis" {
  name = "${var.project_slug}/${var.environment}/redis"
}

resource "aws_secretsmanager_secret_version" "redis" {
  secret_id     = aws_secretsmanager_secret.redis.id
  secret_string = jsonencode({
    auth_token = random_password.auth.result
    host       = aws_elasticache_replication_group.redis.primary_endpoint_address
    port       = 6379
  })
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = replace("${local.name_prefix}-redis", "_", "-")
  description           = "${local.name_prefix} redis"
  engine                = "redis"
  engine_version        = var.engine_version
  node_type             = var.node_type
  num_cache_clusters    = var.num_cache_nodes
  parameter_group_name  = var.parameter_group_name
  subnet_group_name             = aws_elasticache_subnet_group.redis.name
  security_group_ids            = [aws_security_group.redis.id]
  maintenance_window            = "sun:05:00-sun:06:00"
  port                          = 6379
  auth_token                    = random_password.auth.result
  at_rest_encryption_enabled    = true
  transit_encryption_enabled    = true
  automatic_failover_enabled    = var.num_cache_nodes > 1
  apply_immediately             = true
}

output "primary_endpoint" {
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "security_group_id" {
  value = aws_security_group.redis.id
}

output "secret_arn" {
  value = aws_secretsmanager_secret.redis.arn
}

output "auth_token" {
  value     = random_password.auth.result
  sensitive = true
}

output "redis_url" {
  value     = format("rediss://:%s@%s:6379/0", random_password.auth.result, aws_elasticache_replication_group.redis.primary_endpoint_address)
  sensitive = true
}

