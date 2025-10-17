locals {
  workspace      = terraform.workspace == "default" ? "staging" : terraform.workspace
  environment    = local.workspace == "prod" ? "production" : local.workspace
  short_env      = local.environment == "production" ? "prod" : local.environment
  name_prefix    = "${var.project_slug}-${local.environment}"
  vpc_cidr_block = "10.20.0.0/16"
}

module "network" {
  source              = "./modules/network"
  project_slug        = var.project_slug
  environment         = local.environment
  cidr_block          = local.vpc_cidr_block
  create_nat_gateway  = true
}

module "rds" {
  source                 = "./modules/rds"
  project_slug           = var.project_slug
  environment            = local.environment
  vpc_id                 = module.network.vpc_id
  subnet_ids             = module.network.private_subnet_ids
  allowed_cidr_blocks    = [module.network.cidr_block]
  database_name          = var.database_name
  database_username      = var.database_username
  allocated_storage      = var.database_allocated_storage
  instance_class         = var.database_instance_class
  multi_az               = local.environment == "production"
  backup_retention_period = local.environment == "production" ? 14 : 3
}

module "redis" {
  count                      = var.enable_redis ? 1 : 0
  source                     = "./modules/redis"
  project_slug               = var.project_slug
  environment                = local.environment
  vpc_id                     = module.network.vpc_id
  subnet_ids                 = module.network.private_subnet_ids
  allowed_cidr_blocks        = [module.network.cidr_block]
  node_type                  = var.redis_node_type
  num_cache_nodes            = var.redis_num_cache_nodes
  allowed_security_group_ids = []
}

module "s3_media" {
  source             = "./modules/s3_media"
  project_slug       = var.project_slug
  environment        = local.environment
  force_destroy      = var.media_bucket_force_destroy && local.environment != "production"
  enable_cloudfront  = var.enable_cloudfront
  custom_domain      = var.domain_name
  hosted_zone_id     = var.hosted_zone_id
}

module "ecr" {
  source        = "./modules/ecr"
  project_slug  = var.project_slug
  environment   = local.environment
}

module "ses" {
  count          = var.enable_ses && var.ses_email_identity != "" ? 1 : 0
  source         = "./modules/ses"
  domain         = var.ses_email_identity
  hosted_zone_id = var.hosted_zone_id
}

resource "random_password" "django_secret" {
  length  = 50
  special = true
}

locals {
  database_url = module.rds.connection_string
  redis_url    = var.enable_redis ? module.redis[0].redis_url : ""
  env_parameter_tags = {
    Project     = var.project_slug
    Environment = local.environment
  }
  base_parameters = {
    "DJANGO_SETTINGS_MODULE" = {
      value       = "config.settings.production"
      description = "Django settings module"
      type        = "String"
    }
    "DJANGO_SECRET_KEY" = {
      value = random_password.django_secret.result
    }
    "DJANGO_ALLOWED_HOSTS" = {
      value       = "*"
      description = "Update with concrete hostnames"
      type        = "String"
    }
    "DJANGO_DEBUG" = {
      value       = local.environment == "production" ? "False" : "True"
      type        = "String"
    }
    "DATABASE_URL" = {
      value = local.database_url
    }
    "AWS_STORAGE_BUCKET_NAME" = {
      value = module.s3_media.bucket_name
      type  = "String"
    }
    "AWS_DEFAULT_REGION" = {
      value = var.aws_region
      type  = "String"
    }
    "DJANGO_USE_S3_MEDIA" = {
      value = "True"
      type  = "String"
    }
    "SES_ENABLED" = {
      value = var.enable_ses ? "True" : "False"
      type  = "String"
    }
  }
  redis_parameters = var.enable_redis ? {
    "REDIS_URL" = {
      value = local.redis_url
    }
    "CELERY_BROKER_URL" = {
      value = local.redis_url
    }
    "CELERY_RESULT_BACKEND" = {
      value = local.redis_url
    }
  } : {}
}

module "ssm_parameters" {
  source       = "./modules/parameter_store"
  path_prefix  = "${var.parameter_store_path_prefix}/${local.environment}"
  parameters   = merge(local.base_parameters, local.redis_parameters)
  tags         = local.env_parameter_tags
}

locals {
  apprunner_env_vars = {
    "PYTHONUNBUFFERED"           = "1"
    "DJANGO_SETTINGS_MODULE"     = "config.settings.production"
    "DJANGO_SECURE_SSL_REDIRECT" = local.environment == "production" ? "True" : "False"
    "DJANGO_SESSION_COOKIE_SECURE" = local.environment == "production" ? "True" : "False"
    "DJANGO_CSRF_COOKIE_SECURE"    = local.environment == "production" ? "True" : "False"
  }
  apprunner_secrets = {
    "DJANGO_SECRET_KEY"    = module.ssm_parameters.parameter_arns["DJANGO_SECRET_KEY"]
    "DATABASE_URL"         = module.ssm_parameters.parameter_arns["DATABASE_URL"]
    "DJANGO_ALLOWED_HOSTS" = module.ssm_parameters.parameter_arns["DJANGO_ALLOWED_HOSTS"]
  }
  apprunner_optional_secrets = var.enable_redis ? {
    "REDIS_URL"             = module.ssm_parameters.parameter_arns["REDIS_URL"]
    "CELERY_BROKER_URL"     = module.ssm_parameters.parameter_arns["CELERY_BROKER_URL"]
    "CELERY_RESULT_BACKEND" = module.ssm_parameters.parameter_arns["CELERY_RESULT_BACKEND"]
    "DJANGO_CACHE_URL"      = module.ssm_parameters.parameter_arns["REDIS_URL"]
  } : {}
}

locals {
  apprunner_additional_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ParameterStoreAccess"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = values(module.ssm_parameters.parameter_arns)
      },
      {
        Sid    = "SecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = concat([module.rds.secret_arn], var.enable_redis ? [module.redis[0].secret_arn] : [])
      }
    ]
  })
}

module "app_runner" {
  count                 = var.app_runner_enabled ? 1 : 0
  source                = "./modules/app_runner"
  project_slug          = var.project_slug
  environment           = local.environment
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  repository_url        = module.ecr.repository_url
  image_tag             = var.app_runner_image_tag
  cpu                   = var.app_runner_cpu
  memory                = var.app_runner_memory
  desired_count         = var.app_runner_desired_count
  health_check_path     = var.app_runner_health_check_path
  environment_variables = merge(local.apprunner_env_vars, var.enable_ses && var.ses_email_identity != "" ? { "SES_VERIFIED_FROM_EMAIL" = var.ses_email_identity } : {})
  environment_secrets   = merge(local.apprunner_secrets, local.apprunner_optional_secrets)
  additional_policy_json = local.apprunner_additional_policy
}

output "app_runner_service_url" {
  value = var.app_runner_enabled && length(module.app_runner) > 0 ? module.app_runner[0].service_url : ""
}

output "media_bucket" {
  value = module.s3_media.bucket_name
}

output "database_endpoint" {
  value = module.rds.endpoint
}

output "redis_endpoint" {
  value = var.enable_redis ? module.redis[0].primary_endpoint : ""
}
