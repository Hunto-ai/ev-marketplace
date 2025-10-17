# Codex Session Notes

Use this file to sync the next Codex session quickly. Update as work progresses.

## Immediate Objectives (MVP Realignment)

1. **Moderation & Trust**
   - Enforce that only `Listing.status="active"` is visible publicly (tests included).
   - Inquiry: add rate limiting per (IP, listing), captcha hook, and audit log entry.

2. **Inquiry SES Relay**
   - Replace email stub with AWS SES (env-driven).
   - Persist send status/error log on Inquiry.
   - Add seller dashboard “Notifications” to view inquiries.

3. **Dealer Public Pages**
   - `/dealers/<slug>/` showing DealerProfile (name, city/province, blurb, site) and their active inventory.
   - Link dealer profile from listing detail/cards.

4. **Guides & SEO**
   - Markdown-driven guides (Buyer’s Checklist, Charging 101, Winter Range).
   - Add XML sitemap, robots.txt, canonical URLs, analytics hook.

5. **Seeds & QA**
   - Seed ~20 ModelSpec rows + a few demo listings (`manage.py seed_models`).
   - Tests for moderation visibility, inquiry flow + SES (mocked), dealer page render, sitemap presence.
6. **CI & QA Wiring**
   - GitHub Actions workflow runs lint, security, accessibility (axe CLI), sqlite, and Postgres jobs on push/PR (Postgres seeds via `manage.py seed_models` before checks/tests).
   - Branch strategy documented: `develop` (staging) and `main` (production) require all CI checks and Terraform plan status before merge.
   - TODO: Expand the accessibility check to hit running pages (Playwright) and layer in performance/lighthouse smoke runs once environments stabilize.


## Out of Scope for MVP
- Saved searches (implemented, but keep behind FEATURE_SAVED_SEARCHES=false)
- Watchlists/favorites
- Message centre
- VIN/accident integrations
- Payments/monetization
- Upload progress UI, stale-original cleanup, S3 lifecycle
- Infrastructure build-out (Terraform, Redis/SQS, observability)

# Feature flags
FEATURE_SAVED_SEARCHES=false
FEATURE_WATCHLISTS=false

# Inquiry safety
INQUIRY_RATE_LIMIT_PER_MINUTE=5
CAPTCHA_PROVIDER=none          # options: none|turnstile|hcaptcha
CAPTCHA_SITE_KEY=
CAPTCHA_SECRET_KEY=

# SES (Email relay)
SES_ENABLED=false
SES_FROM_EMAIL=no-reply@your-domain.com
AWS_REGION=us-east-1



## Repo Snapshot (2025-09-29)
- Django 5 project with settings split (`config/settings/base|local|production`) and `.env` loader (django-environ).
- Custom accounts app (email login + role capture) with django-allauth configured for email + Google OAuth placeholders.
- Listings domain complete: `DealerProfile`, `ModelSpec`, `Listing`, `Photo`, `Inquiry` plus admin tooling, status helpers, and HTMX-friendly querysets.
- Seller dashboard delivers listing CRUD, moderation, and presigned S3 uploads (10-photo cap enforced, storage keys persisted) with Celery stub for post-processing.
- Public catalogue live: `/listings/` index with multi-select filters (make/province/drivetrain/charge type/year/price/keyword) + saved searches, improved pagination, and detail pages with gallery/specs + HTMX inquiry form writing to DB and emailing sellers (via stub).
- Background plumbing: Celery app (`config/celery.py`), django-storages toggles, AWS env vars in settings, and `CONNECTOR_TODO.md` cataloguing production credentials/connectors still required.

## Recent Progress
- Added saved search creation/deletion with persisted filters and recent list in the catalogue.
- Upgraded catalogue pagination with first/last controls and compact numbered page links that respect active filters.
- Enabled multi-select filters (make/province/drivetrain/charge type) on the public catalogue with responsive form UX.
- Public listing templates now consume Celery-generated derivatives for card/detail imagery with responsive srcsets.
- Implemented Celery-driven photo derivative processing (thumbnail/display) with metadata persisted on `Photo` records.
- Added schema.org Vehicle JSON-LD markup on listing detail pages and regression tests for coverage.
- Hardened presigned photo upload flow and callback to enforce limits, persist storage keys, and queue `listings.process_listing_photo` (stub).
- Added inquiry form experience (form class, HTMX partials, seller email stub, metadata capture) with coverage in `listings.tests.PublicListingViewsTests`.
- Expanded README with fresh progress snapshot, refined roadmap, and pointer to the production connector checklist.
- Introduced `CONNECTOR_TODO.md` documenting all outstanding secrets/integration tasks (RDS, Redis, S3, SES, OAuth, observability, Terraform, CI/CD).

## Outstanding Workstreams
1. **Moderation & Trust**: Enforce status gating, inquiry rate limits, captcha hook, and audit logging.
2. **Inquiry SES Relay**: Wire SES-backed delivery, persist send status, and surface seller notifications (feature flagged via `SES_ENABLED`).
3. **Dealer Public Pages**: Build `/dealers/<slug>/` with profile details and active inventory, link from catalogue/detail cards.
4. **Guides & SEO**: Publish Buyer's Checklist, Charging 101, Winter Range guides; add sitemap/robots/canonical URLs and analytics hook.
5. **Seeds & QA**: Implement `manage.py seed_models`, add moderation/inquiry/dealer/sitemap test coverage.
6. **Media pipeline polish**: Dashboard upload progress UI, stale-original cleanup, S3 lifecycle review (post-MVP if needed).
7. **Infrastructure & deployment**: Terraform modules, secrets population, and CI/CD expansion (track via `CONNECTOR_TODO.md`; Terraform deploy workflow now requires GitHub environment approvals + AWS/TF secrets for staging/production).

## Operational Notes
- Terraform deploy workflow runs plan on branch pushes; apply remains manual via GitHub environment approval (see README Branch & Deployment).
- `npm run test:a11y` runs the Playwright/axe smoke against the seeded demo routes (requires `python manage.py seed_models`).
- `manage.py seed_models` now seeds ModelSpec data plus `[DEMO]` DealerProfile + Listing records for QA smoke runs; strip them before production cutover.
- Saved searches remain behind `FEATURE_SAVED_SEARCHES`; leave disabled for MVP while moderation & SES priorities complete.
- Saved search submissions post to `listings:save_search` (create/update) and deletions hit `listings:delete_saved_search`; recent items surface via `saved_searches` in the catalogue context.
- `Photo.thumbnail_url` / `Photo.display_url` expose derivative-aware URLs with safe fallbacks; use in new templates/components.
- Photo derivatives (thumbnail/display) stored on `Photo.derivatives`; use for responsive image sources when front-end catches up.
- Feature toggles for S3 live in `config/settings/base.py` (`DJANGO_USE_S3_MEDIA` etc.); `.env.example` contains placeholders.
- Presigned uploads currently work locally with boto3 credentials. `listings/tasks.process_listing_photo` now generates derivatives; wire dashboard progress UI next.
- Inquiry emails use `send_mail(..., fail_silently=True)`; once SES creds are available, remove `fail_silently` or add logging.
- Production connector checklist: see `CONNECTOR_TODO.md` for all outstanding secrets and infra hooks.
- Front-end uses Pico.css; HTMX partials for inquiry located under `templates/listings/partials/`.

## Testing & Verification
- `DATABASE_URL=sqlite:///db.sqlite3 python manage.py test listings`
- `.venv\Scripts\python.exe manage.py check`
- (Use the sqlite override above until Postgres credentials exist.)

## Open Questions / Decisions Needed
- Final image processing stack (django-versatileimagefield vs custom Celery pipeline vs external service).
- Hosting/deployment target (App Runner vs ECS vs Elastic Beanstalk) and associated networking (ALB, VPC, NAT).
- Saved searches + newsletter UX expectations (frequency, opt-in).
- Observability tooling (Sentry, CloudWatch, Honeycomb?) and logging/metric retention.

## Handy Paths & References
- Public catalogue views: `listings/views.py` (`ListingListView`, `ListingDetailView`, `ListingInquiryView`).
- Inquiry templates: `templates/listings/detail.html`, `templates/listings/partials/inquiry_form.html`, `templates/listings/partials/inquiry_success.html`.
- Photo upload backend: `dashboard/views.py` (`PhotoUploadURLView`, `PhotoCallbackView`).
- Celery entry point: `config/celery.py`; photo processing task stub in `listings/tasks.py`.
- Production connector checklist: `CONNECTOR_TODO.md`.
