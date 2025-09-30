# Terraform Infrastructure

This directory contains Terraform modules for provisioning AWS resources required by the EV Marketplace MVP (RDS, ElastiCache, SQS, SES, S3, App Runner/Elastic Beanstalk).

## Bootstrapping
1. Install Terraform >= 1.8.
2. Configure AWS credentials in your environment or via `aws configure`.
3. Run `terraform init` in each module before planning/applying.

## Layout (proposed)
- `environments/` – environment-specific stacks (dev, staging, prod).
- `modules/` – reusable components (networking, database, cache, app, storage).

Populate modules and variables as infrastructure requirements are locked in.
