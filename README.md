# EV Marketplace MVP

## Overview
The EV Marketplace MVP is a Django 5 + HTMX application for listing electric vehicles, moderating seller activity, and publishing dealer and buyer resources. The project targets a shippable marketplace foundation with clear feature flags and an AWS-friendly deployment path.

## Front-End Style Guide
- See [STYLE_GUIDE.md](STYLE_GUIDE.md) for the shared design language, component tokens, and implementation roadmap.
- New UI work should reference the guide before introducing templates or CSS changes.

## Requirements
- Python 3.11
- pip
- Docker Desktop (optional for local containers)
- PowerShell or Make for helper scripts

## Getting Started
1. Create a virtual environment: `py -3.11 -m venv .venv`
2. Activate it: `.venv\Scripts\Activate.ps1`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy environment template: `Copy-Item .env.example .env`
5. Update `.env` with the values for your environment (see Feature Flags and Environment Variables below). For local development without Postgres running, set `DATABASE_URL=sqlite:///db.sqlite3`.
6. Run database migrations: `python manage.py migrate`
7. (Optional) Seed demo content for listings, dealers, and inquiries: `python manage.py seed_models`
8. Start the dev server: `python manage.py runserver`

## MVP Scope (Ship This)
- **Listings** – seller CRUD with up to 10 photos, status flow `draft → pending → active → sold`, automatic JSON-LD for detail pages.
- **Catalogue** – server-side filters (make/model/year/price/km/province/drivetrain/DC fast charge type/heat pump) and keyword search.
- **Listing detail** – gallery, EV spec panel (battery specs, DCFC type, onboard AC kW, heat pump), inquiry form, canonical URLs.
- **Trust & safety** – admin approval gating, inquiry rate limiting, captcha hook, SES email relay with delivery status logging.
- **Dealer experience** – public dealer profile pages with active inventory; dealer filter integration in the catalogue.
- **Content & SEO** – three markdown-driven guides (Buyer’s Checklist, Charging 101, Winter Range), XML sitemap, robots.txt.

## Out of Scope (MVP)
- Saved searches / alerts (flagged off by default)
- Watchlists / favourites
- In-platform messaging
- VIN / accident integrations
- Payments / monetisation
- Media lifecycle polish (upload progress UI, stale cleanup)

## Feature Flags
| Flag | Default | Purpose |
| --- | --- | --- |
| `FEATURE_SAVED_SEARCHES` | `False` | Hide saved-search UX until moderation/SES polish is done. |
| `FEATURE_WATCHLISTS` | `False` | Placeholder for future watchlist/favourites work. |
| `SES_ENABLED` | `False` | Switch between console email backend and AWS SES delivery. |

Set these in `.env` (see `.env.example`). Keep saved searches off for MVP QA.

## Trust & Moderation
- Listings are public only when `status == active`; drafts/pending/sold remain hidden automatically.
- Inquiry submissions are rate limited per (listing, IP) using cache and respect the `INQUIRY_RATE_LIMIT_PER_MINUTE` setting.
- Captcha provider is env-configurable (`none`, `turnstile`, `hcaptcha`); verification metadata is logged on each inquiry.
- Inquiry delivery stores status (`pending → sent/failed`), timestamps, SES message IDs, and dashboards surface unread notifications.
- Seller dashboards expose notifications and mark inquiries as read when viewed.

## Guides & SEO
- Markdown content lives in `guides/content/` and renders through the guides app.
- `/guides/` lists every guide; detail pages include canonical links and updated timestamps.
- `/sitemap.xml` indexes active listings and guides; `/robots.txt` references the sitemap.

## MVP Run Checklist
1. `python manage.py migrate` then `python manage.py createsuperuser`.
2. Seed optional EV specs: `python manage.py seed_models`.
3. Create a seller, add a listing (draft → pending), approve it in `/admin/`, confirm it appears on `/listings/`.
4. Submit an inquiry on the active listing (captcha stub enabled). Ensure `Inquiry` records delivery status and metadata.
5. Toggle `SES_ENABLED=true` (with valid AWS creds) to verify SES delivery and seller notifications; otherwise confirm console backend logs the message.
6. Visit `/dealers/<slug>/` and confirm only active inventory displays.
7. Review `/guides/`, `/guides/<slug>/`, `/sitemap.xml`, `/robots.txt`, and listing JSON-LD markup.
8. Confirm saved searches UI is hidden (feature flag off).

## Testing
- Run application checks: `python manage.py check`
- Default test suite: `python manage.py test`
- Hint: when running locally or in CI, set `DATABASE_URL=sqlite:///db.sqlite3` to avoid Postgres credentials, e.g.:
  - PowerShell: `SET DATABASE_URL=sqlite:///db.sqlite3`
  - Bash: `export DATABASE_URL=sqlite:///db.sqlite3`
- Targeted suites: `python manage.py test guides dealers listings`

## Seller Dashboard Highlights
- `/dashboard/` inventory table with HTMX moderation controls.
- `/sell/` and `/dashboard/listings/create/` route to the listing form.
- Photo uploads currently use default storage; presigned S3 hooks are stubbed for future work.

## Pushing Application Updates
The production stack runs Django 5 (Python 3.11) inside a Docker image hosted on AWS App Runner, with Terraform managing infrastructure and GitHub Actions handling CI, image publishing, and automated applies. To ship manual changes:

1. **Build the image** – `docker build -t 654654601496.dkr.ecr.us-east-2.amazonaws.com/evmarket-staging-app:<tag> .` (requires Docker Desktop and AWS CLI configured for the `evuser` profile).
2. **Push to ECR** – `aws ecr get-login-password --profile evuser --region us-east-2 | docker login --username AWS --password-stdin 654654601496.dkr.ecr.us-east-2.amazonaws.com`, then `docker push 654654601496.dkr.ecr.us-east-2.amazonaws.com/evmarket-staging-app:<tag>`.
3. **Update Terraform vars** – set `app_runner_image_tag` (and any flags such as `app_runner_health_check_path`) in `terraform/staging.tfvars`.
4. **Apply Terraform** – from the `terraform/` directory run `AWS_PROFILE=evuser .\.bin\terraform.exe apply -var-file=staging.tfvars`.
5. **Verify the service** – fetch the URL with `terraform output app_runner_service_url` or `aws apprunner describe-service` and smoke test listings, guides, and inquiry flows.

GitHub Actions workflows (`build-and-publish.yml`, `terraform-deploy.yml`) perform the same build and apply steps when you prefer the automated path.

## Authentication
- Custom `accounts.User` with email login and role (`buyer`, `seller`, `dealer`, `admin`).
- [django-allauth](https://github.com/pennersr/django-allauth) powers email + Google auth; configure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
- Default redirects land on `/`; override with `DJANGO_LOGIN_REDIRECT_URL` / `DJANGO_LOGOUT_REDIRECT_URL` as needed.

## Deployment Notes
- Docker compose file runs the stack locally (optional).
- Terraform modules under `terraform/` prepare AWS scaffolding (populate credentials before use).
- See `CONNECTOR_TODO.md` for the production integration checklist.

## Reference Commands
- Format (future): `python -m black`
- Lint (future): `python -m flake8`
- Static type checks (future): `python -m mypy`
- Collect static: `python manage.py collectstatic`
