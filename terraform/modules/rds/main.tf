locals {
  name_prefix      = "${var.project_slug}-${var.environment}"
  allowed_cidrs    = length(var.allowed_cidr_blocks) > 0 ? var.allowed_cidr_blocks : ["0.0.0.0/0"]
  final_snapshot   = "${local.name_prefix}-db-final"
  subnet_group_name = "${local.name_prefix}-db-subnets"
}

resource "aws_db_subnet_group" "this" {
  name       = local.subnet_group_name
  subnet_ids = var.subnet_ids

  tags = {
    Name = local.subnet_group_name
  }
}

resource "aws_security_group" "this" {
  name        = "${local.name_prefix}-db"
  description = "Database access"
  vpc_id      = var.vpc_id

  ingress {
    description = "Postgres"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = local.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-db"
  }
}

resource "random_password" "master" {
  length  = 24
  special = false
}

resource "aws_secretsmanager_secret" "credentials" {
  name = "${var.project_slug}/${var.environment}/database"
}

resource "aws_secretsmanager_secret_version" "credentials" {
  secret_id     = aws_secretsmanager_secret.credentials.id
  secret_string = jsonencode({
    username = var.database_username
    password = random_password.master.result
    engine   = "postgres"
    host     = aws_db_instance.this.address
    dbname   = var.database_name
    port     = 5432
  })
}

resource "aws_db_instance" "this" {
  identifier                 = "${local.name_prefix}-db"
  allocated_storage          = var.allocated_storage
  engine                     = "postgres"
  engine_version             = var.engine_version
  instance_class             = var.instance_class
  db_name                    = var.database_name
  username                   = var.database_username
  password                   = random_password.master.result
  db_subnet_group_name       = aws_db_subnet_group.this.name
  vpc_security_group_ids     = [aws_security_group.this.id]
  multi_az                   = var.multi_az
  backup_retention_period    = var.backup_retention_period
  delete_automated_backups   = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = local.final_snapshot
  publicly_accessible        = false
  storage_encrypted          = true
  auto_minor_version_upgrade = true
  apply_immediately          = true
}

output "endpoint" {
  value = aws_db_instance.this.address
}

output "port" {
  value = aws_db_instance.this.port
}

output "security_group_id" {
  value = aws_security_group.this.id
}

output "secret_arn" {
  value = aws_secretsmanager_secret.credentials.arn
}

output "dbname" {
  value = var.database_name
}

output "username" {
  value = var.database_username
}

output "password" {
  value     = random_password.master.result
  sensitive = true
}

output "connection_string" {
  value     = format("postgres://%s:%s@%s:%s/%s", var.database_username, random_password.master.result, aws_db_instance.this.address, aws_db_instance.this.port, var.database_name)
  sensitive = true
}

