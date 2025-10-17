# Project: EV Marketplace MVP

## Tech Stack
- Python 3.11
- Django 5 + Django REST Framework
- HTMX for interactivity
- Postgres (AWS RDS)
- Storage: S3 (via django-storages)
- Email: AWS SES (env-gated)
- Background jobs: Celery + SQS (or Redis broker locally)
- Cache: Redis (ElastiCache)
- Deploy: AWS App Runner (Docker) or Elastic Beanstalk
- IaC: Terraform

## MVP Scope (Ship This)
1. Public catalogue with filters (make, model, year, price, km, province, drivetrain, DC fast-charge type, heat pump) + keyword search.
2. Listing detail page:
   - Photo gallery
   - EV spec panel (battery warranty, EPA/NRCan range, DCFC type/kW, onboard AC kW, heat pump)
   - Contact seller form (SES relay when enabled; otherwise console/stub)
   - schema.org/Vehicle JSON-LD
3. Seller dashboard (CRUD listings + photos, max 10) with status flow (draft → pending → active → sold).
4. Dealer profile pages (public) with inventory grid.
5. Admin moderation (approve/reject; only **active** listings are public).
6. Static guides (markdown-driven): Buyer’s Checklist, Charging 101, Winter Range.
7. SEO baseline: XML sitemap, robots.txt, canonical URLs. (Analytics optional)

## Out of Scope for MVP (Defer)
- Saved searches / alerts (feature-flagged OFF)
- Watchlists / favorites
- In-platform messaging
- VIN / accident integrations
- Payments/monetization
- Upload progress UI, S3 lifecycle policies (non-blocking polish)
- Full infra build-out (Terraform/observability) beyond what’s needed to run

## Feature Flags
- `FEATURE_SAVED_SEARCHES` (default: false)
- `FEATURE_WATCHLISTS` (default: false)
- `SES_ENABLED` (default: false) – toggles real SES vs console/stub email

## Data Model
- **User** (extends AbstractUser; role: buyer|seller|dealer|admin)
- **DealerProfile** (FK User; name, city/province, site, blurb, slug)
- **Listing** (seller FK, title, description, make, model, trim, year, price, km, province/city, drivetrain, EV fields, status)
- **Photo** (FK Listing; original key; derivative URLs/metadata)
- **Inquiry** (FK Listing; name, email, message, meta; delivery status/log)
- **ModelSpec** (seeded EV trims/specs for defaults/tooltips)
> **Removed from MVP:** SavedSearch (keep any code behind `FEATURE_SAVED_SEARCHES`).

## Conventions
- Apps: `accounts`, `listings`, `dealers`, `dashboard`, `guides`, `public`, `api`
- DRF endpoints under `/api/` (minimal for MVP)
- Templates: Django + HTMX partials; CSRF on all forms
- Photos: S3 (presigned) in prod; local storage ok for dev
- Moderation: only `active` listings appear in public catalogue
- Email relay: hides seller email; SES when `SES_ENABLED=true`, else console
- Nightly sitemap via Celery (or on-demand management command in dev)

## Tasks = Definition of Done
- [ ] User can sign up/login (email; Google optional)
- [ ] Seller can create a listing with ≤10 photos; submit → pending → admin approves → public
- [ ] Buyers can browse/search/filter listings
- [ ] Listing detail shows EV spec panel + JSON-LD
- [ ] Contact seller persists Inquiry and sends email (SES if enabled)
- [ ] Dealer public page lists dealer info + active inventory
- [ ] Guides render from markdown; sitemap/robots present

## Acceptance Tests (Minimum)
- Visibility: draft/pending/sold are hidden; active is public
- Inquiry: rate-limited (per IP+listing), captcha hook respected, delivery status stored (SES mocked in CI)
- Dealer page renders with active inventory
- Sitemap includes public listings + guides; JSON-LD present on detail

## Non-Goals (for MVP)
- Payments/monetization
- Mobile app
- Advanced search engines (stick with Postgres FTS)
- VIN decoding / accident data
