# Project: EV Marketplace MVP

## Tech Stack
- Python 3.11
- Django 5 + Django REST Framework
- HTMX for interactivity
- Postgres (AWS RDS)
- Storage: S3 (via django-storages)
- Email: AWS SES
- Background jobs: Celery + SQS
- Cache: Redis (ElastiCache)
- Deploy: AWS App Runner (Docker) or Elastic Beanstalk
- IaC: Terraform

## Core Features
1. Public catalogue with filters (make, model, year, price, km, province, drivetrain, dc fast-charge type, heat pump).
2. Listing detail page:
   - Photo gallery
   - EV-specific spec panel (battery warranty, range, DCFC type, etc.)
   - Contact seller form (SES relay).
3. Seller dashboard (CRUD listings + photos).
4. Dealer profile pages (with inventory).
5. Admin moderation (approve/reject listings).
6. Static guides (markdown-driven).
7. Newsletter signup form.
8. SEO baseline: schema.org/Vehicle, XML sitemap, robots.txt.

## Data Model
- User (extends AbstractUser; role: buyer|seller|dealer|admin).
- DealerProfile (FK to User).
- Listing (make, model, trim, year, price, km, province, drivetrain, EV fields, status).
- Photo (FK to Listing).
- Inquiry (FK to Listing).
- SavedSearch (FK to User).
- ModelSpec (seeded EV trims/specs).

## Conventions
- Use Django apps: accounts, listings, dealers, guides, public, api.
- Use DRF for API endpoints under `/api/`.
- Templates: Django templates + HTMX partials.
- All forms validated with Django forms + CSRF.
- All listings default to `pending` until admin approval.
- Photos: uploaded to S3, max 10 per listing, generate thumbnails.
- Contact: stored in DB + emailed via SES, hide seller email.
- Add schema.org/Vehicle JSON-LD to listing detail pages.
- Sitemap auto-build nightly via Celery.

## Tasks = Definition of Done
- [ ] User can sign up/login (email + Google).
- [ ] Seller can create a listing with 5+ photos, submit → admin approval → goes public.
- [ ] Buyers can search/filter listings.
- [ ] Contact seller works with SES relay and persists inquiry.
- [ ] Admin can moderate listings via Django admin.
- [ ] Sitemap + schema.org/Vehicle exist.
- [ ] Static guide pages render from markdown.

## Non-Goals (for MVP)
- Payments/monetization.
- Mobile app.
- Advanced search engines (stick with Postgres FTS).
- VIN decoding.
