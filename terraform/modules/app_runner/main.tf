locals {
  name_prefix = "${var.project_slug}-${var.environment}"
}

resource "aws_security_group" "apprunner" {
  name        = "${local.name_prefix}-apprunner"
  description = "App Runner VPC connector egress"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = var.egress_cidr_blocks
  }

  tags = {
    Name = "${local.name_prefix}-apprunner"
  }
}

resource "aws_apprunner_vpc_connector" "this" {
  vpc_connector_name = "${local.name_prefix}-connector"
  subnets            = var.private_subnet_ids
  security_groups    = [aws_security_group.apprunner.id]
}

resource "aws_iam_role" "service" {
  name = "${local.name_prefix}-apprunner-service-role"

  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role" "instance" {
  name = "${local.name_prefix}-apprunner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "service_ecr" {
  role       = aws_iam_role.service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

resource "aws_iam_role_policy" "additional" {
  count  = var.additional_policy_json == "" ? 0 : 1
  name   = "${local.name_prefix}-apprunner-extra"
  role   = aws_iam_role.instance.id
  policy = var.additional_policy_json
}

resource "aws_apprunner_auto_scaling_configuration_version" "this" {
  auto_scaling_configuration_name = "${local.name_prefix}-asg"
  max_concurrency                 = 100
  max_size                        = max(var.desired_count, 2)
  min_size                        = var.desired_count
}

resource "aws_apprunner_service" "this" {
  service_name = replace("${local.name_prefix}-web", "_", "-")

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.service.arn
    }

    image_repository {
      image_identifier      = "${var.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
        runtime_environment_variables = var.environment_variables
        runtime_environment_secrets = var.environment_secrets
      }
    }
    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu              = format("%0.f", var.cpu * 1024)
    memory           = format("%0.f", var.memory * 1024)
    instance_role_arn = aws_iam_role.instance.arn
  }

  health_check_configuration {
    path                = var.health_check_path
    protocol            = "HTTP"
    healthy_threshold   = 1
    unhealthy_threshold = 5
    interval            = 10
    timeout             = 5
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.this.arn
    }
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.this.arn
}

output "service_arn" {
  value = aws_apprunner_service.this.arn
}

output "service_url" {
  value = aws_apprunner_service.this.service_url
}

output "security_group_id" {
  value = aws_security_group.apprunner.id
}

output "service_role_arn" {
  value = aws_iam_role.service.arn
}
