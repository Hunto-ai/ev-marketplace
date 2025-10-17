# Handoff Notes

## Current State
- Terraform remote state bootstrap complete (`evmarket-tf-state` bucket, `evmarket-tf-locks` table).
- Staging workspace applied with core infrastructure (VPC, RDS Postgres 16.3, ElastiCache Redis, S3 media bucket, Parameter Store secrets). No App Runner service yet (`app_runner_enabled = false`).
- CI workflows updated:
  - `.github/workflows/build-and-publish.yml` builds/pushes Docker image to ECR (`evmarket-staging-app` or production variant) using OIDC.
  - `.github/workflows/terraform-deploy.yml` derives image tags and supports manual override; Terraform stack now parameterized via tfvars.
- Docker image now uses `docker/entrypoint.sh` (Gunicorn, collectstatic, migrate) and `gunicorn` is listed in `requirements.txt`.
- Local Terraform files/staging tfvars are not committed yet; see `terraform/staging.tfvars` for current values (App Runner disabled, placeholder image tag `staging-latest`).
- Latest `terraform plan -var-file=staging.tfvars` shows no changes.

## Open Work / Next Steps
1. Run the `Build Container` workflow on GitHub (push to `develop` or manually trigger) to publish an ECR image; note produced tag.
2. Update `terraform/staging.tfvars` with `app_runner_enabled = true` and the real `app_runner_image_tag`, then run `terraform apply -var-file=staging.tfvars` to create the App Runner service.
3. Once staging is verified, replicate for production: create `prod` workspace, copy `prod.tfvars.example`, populate real values (image tag, SES/domain info), enable App Runner, apply, and lock down IAM policies from temporary Admin access.
4. Review GitHub environment secrets to ensure Terraform workflow has required tfvars/environment values and environment protections (staging/production) before enabling automatic applies.
5. After App Runner is active, configure DNS/SSL if needed (Route53 records, ACM certificates) and update `hostname` related Terraform variables when domain is ready.
6. Commit pending repository changes (.terraform.lock.hcl, new Terraform modules, workflows, Docker updates) once validated.
7. Optional: re-enable App Runner module later by flipping `app_runner_enabled` to true in both staging and production once images exist.

## Reminders
- `evuser` currently has AdministratorAccess; tighten IAM permissions after provisioning completes.
- The Terraform apply removed App Runner artifacts to keep state clean; no service is deployed yet.
- RDS/Redis credentials are stored in Secrets Manager; connect using outputs from `terraform output` (already checked in staging).
- Keep an eye on cost-heavy resources (RDS/Redis/NAT gateway) if environments remain idle; consider shutting down staging when not in use.
