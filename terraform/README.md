# Terraform Infrastructure

This directory contains the infrastructure-as-code for deploying EV Marketplace on AWS App Runner. The stack is workspace-aware (`staging`, `prod`) and provisions the shared network, data stores, container registry, App Runner service, and supporting AWS services.

## Layout

```
terraform/
??? backend.tf                # Remote state (S3 + DynamoDB)
??? bootstrap/                # One-time state backend provisioning
??? main.tf                   # Root module wiring
??? providers.tf
??? variables.tf
??? modules/
?   ??? app_runner/
?   ??? ecr/
?   ??? network/
?   ??? parameter_store/
?   ??? rds/
?   ??? redis/
?   ??? s3_media/
?   ??? ses/
??? README.md (this file)
```

## One-Time Bootstrap

1. Configure AWS credentials with permissions to create S3 + DynamoDB resources.
2. `cd terraform/bootstrap`
3. `terraform init && terraform apply`

The bootstrap run creates:
- S3 bucket `${project_slug}-tf-state`
- DynamoDB table `${project_slug}-tf-locks`

Update `terraform/backend.tf` if you pick a different slug/region.

## Environment Workspaces

The root configuration expects Terraform workspaces:

```
cd terraform
terraform init
terraform workspace new staging   # first-time only
terraform workspace new prod      # first-time only
```

Use `staging` for the MVP environment and `prod` for production. The backend stores state under `env/<workspace>/terraform.tfstate`.

## Required Variables

Most defaults suit a fresh deployment, but supply the following before `terraform apply`:

| Variable | Purpose |
| --- | --- |
| `aws_region` | Primary AWS region (defaults to `us-east-2`). |
| `app_runner_image_tag` | ECR image tag to deploy (set by CI once images are published). |
| `ses_email_identity` | Domain/email identity to verify in SES (set `enable_ses=true`). |
| `hosted_zone_id` | Route53 zone ID backing `ses_email_identity` or CloudFront. |
| `media_bucket_force_destroy` | Only use `true` outside production. |

Provide overrides through `terraform.tfvars`, `staging.tfvars`, or CLI `-var` flags.

## Outputs

- `app_runner_service_url` ? Managed HTTPS endpoint for the web app.
- `media_bucket` ? S3 bucket for user uploads/static assets.
- `database_endpoint` ? RDS hostname (credentials stored in Secrets Manager + SSM).
- `redis_endpoint` ? Redis endpoint when enabled.

## Next Steps

1. Populate `terraform.tfvars` with domain names, SES identities, and App Runner image tags.
2. Run `terraform plan` in the `staging` workspace to review the full stack.
3. Once infrastructure is provisioned, integrate the CI pipeline to build/push containers to ECR and apply Terraform automatically.

> Tip: keep `enable_ses=false` until DNS records are created, otherwise the apply will pause waiting for verification.
