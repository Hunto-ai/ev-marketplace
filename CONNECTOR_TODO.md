# Production Connector TODOs

Use this checklist to track integrations that still require production-ready credentials, IAM policies, or infrastructure wiring. Update each item with the correct values/notes once provisioned.

## Application Services
- [ ] **PostgreSQL (RDS)**
  - Env vars: `DATABASE_URL` (DB name/user/pass/host/port).
  - Notes: Create parameter group, enforce SSL, set connection pooling strategy (pgBouncer or RDS Proxy) for Celery & web.
- [ ] **Redis / Celery Broker (ElastiCache or Amazon MQ)**
  - Env vars: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.
  - Notes: Decide on broker (Redis vs SQS/SNS) and configure Celery beat queue if used.
- [ ] **S3 Media Storage**
  - Env vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (if temporary), `AWS_DEFAULT_REGION`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `DJANGO_USE_S3_MEDIA`.
  - Notes: Finalize bucket policies (CORS for uploads, presigned POST), lifecycle rules for originals/derivatives, and CloudFront distribution if needed.
- [ ] **SES Email Delivery**
  - Env vars: `SES_VERIFIED_FROM_EMAIL`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, optional SMTP credentials.
  - Notes: Verify domains/identities, configure feedback notifications, ensure sandbox exit.
- [ ] **Celery Background Workers**
  - Env vars: `CELERY_*` tuning, worker autoscaling config.
  - Notes: Decide on worker hosting (ECS/App Runner/EB) and add health checks.

## Authentication & Third Parties
- [ ] **Google OAuth**
  - Env vars: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
  - Notes: Register production redirect URIs, enable consent screen, add scopes if marketing features appear.
- [ ] **Admin/Superuser Bootstrap**
  - Env vars: `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` (if auto-created in deploy script).
  - Notes: Script credential rotation & secret storage (AWS Secrets Manager/Parameter Store).

## Observability & Ops
- [ ] **Error Monitoring (Sentry, etc.)**
  - Env vars: e.g., `SENTRY_DSN`.
  - Notes: Integrate logging handlers, configure release markers.
- [ ] **Metrics / Tracing (CloudWatch, Honeycomb, etc.)**
  - Env vars: tool-specific keys.
  - Notes: Ensure ALB/App Runner metrics + Celery worker telemetry captured.
- [ ] **Secrets Management**
  - Decide on AWS Secrets Manager vs Parameter Store; document mapping of secrets -> env vars.

## Infrastructure Automation
- [ ] **Terraform Variables**
  - Populate `terraform/` variable files for RDS, S3, Redis, SES, networking.
  - Notes: Add remote state backend, environment workspaces, and CI integration.
- [ ] **CI/CD Pipeline**
  - Configure GitHub Actions (or alternative) with secrets, build/test/deploy steps, Docker registry credentials.

## Security Hardening
- [ ] **Django settings overrides**
  - Env vars: `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`, `DJANGO_SECURE_HSTS_SECONDS`, etc.
  - Notes: Confirm ALB/App Runner HTTPS termination, add CSP headers.
- [ ] **Allowed Hosts / CSRF Origins**
  - Env vars: `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`.
  - Notes: Document staging vs production values.

## Future Enhancements
- [ ] **Saved Searches / Notifications**
  - Depends on background job + email connector completeness.
- [ ] **Dealer Asset Storage**
  - Additional S3 prefixes or separate bucket for logos/branding.

Update this document as environments evolve; consider splitting into environment-specific `.env.production` templates once secrets are issued.
