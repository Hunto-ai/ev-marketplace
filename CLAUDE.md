# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EV Marketplace MVP** - A Django 5 + HTMX application for listing electric vehicles with seller moderation, dealer profiles, and buyer resources. The system emphasizes trust & safety with admin approval workflows, rate limiting, and AWS SES email relay.

## Essential Commands

### Development Setup
```powershell
# Create and activate virtual environment
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Setup environment and database
Copy-Item .env.example .env
# Edit .env - set DATABASE_URL=sqlite:///db.sqlite3 for local dev
python manage.py migrate
python manage.py seed_models  # Seed demo data (listings, dealers, inquiries)
python manage.py createsuperuser
```

### Running the Application
```powershell
python manage.py runserver  # Dev server at http://localhost:8000
```

### Testing
```powershell
# Run all tests (use SQLite for speed)
$env:DATABASE_URL = "sqlite:///db.sqlite3"
python manage.py test

# Run specific app tests
python manage.py test listings dealers guides

# Application checks
python manage.py check

# Accessibility tests (requires server running)
npm install
npm run test:a11y
```

### PowerShell Task Helper
```powershell
# Use tasks.ps1 for common operations
.\tasks.ps1 -Task install    # Install dependencies
.\tasks.ps1 -Task migrate    # Run migrations
.\tasks.ps1 -Task run        # Start server
.\tasks.ps1 -Task test       # Run tests
```

### Docker Development
```bash
docker compose up  # Runs web + postgres + redis
```

### Linting & Formatting (CI)
```bash
ruff check .
black --check .
isort --check-only .
bandit -r . -x .venv  # Security scan
```

## Architecture

### Apps Structure
- **accounts** - Custom User model with roles (buyer, seller, dealer, admin) + django-allauth integration
- **listings** - Core EV listing CRUD with photo management, status workflow (draft → pending → approved → archived), inquiry system
- **dealers** - Dealer profiles with public pages showing active inventory
- **dashboard** - Seller-facing CRUD interface with HTMX-powered moderation controls and notifications
- **guides** - Markdown-driven content pages (buyer guides, charging info) with SEO
- **config** - Django settings split (base/local/production), URL routing, WSGI

### Key Models
- **User** (accounts) - email-based auth, roles: `buyer`, `seller`, `dealer`, `admin`
- **Listing** (listings) - EV listings with status flow, photos (max 10), EV-specific fields (battery, DCFC type, heat pump)
- **Photo** (listings) - Image management with derivatives (thumbnail, display), primary photo auto-selection
- **Inquiry** (listings) - Contact form submissions with delivery status tracking, rate limiting metadata
- **DealerProfile** (dealers) - Public dealer pages with slug-based URLs
- **ModelSpec** (listings) - Seed EV specs for pre-filling listing forms

### Status Workflow
Listings follow: `DRAFT` → `PENDING_REVIEW` → `APPROVED` (public) / `REJECTED` / `ARCHIVED`
- Only `APPROVED` listings appear in public catalogue
- Status transitions update timestamps (`approved_at`, `published_at`, `rejected_at`)
- Dashboard provides seller view; admin panel handles moderation

### Trust & Safety Features
- **Inquiry rate limiting** - Per (listing, IP) cache-based throttling via `INQUIRY_RATE_LIMIT_PER_MINUTE`
- **Captcha integration** - Configurable providers: `none`, `turnstile`, `hcaptcha`
- **SES email relay** - Hides seller emails; toggleable via `SES_ENABLED` flag
- **Delivery tracking** - Inquiry model stores SES message IDs, delivery status, timestamps
- **Admin approval gating** - Listings require moderation before going public

### HTMX Patterns
- Dashboard listing table with inline moderation actions (approve/reject/archive)
- Partial templates return updated rows/sections (`partials/*.html`)
- Inquiry form uses HTMX for async submission with inline success/error feedback
- Status badges update via HTMX responses

### SEO & Content
- XML sitemap (`/sitemap.xml`) - active listings + guides
- Robots.txt (`/robots.txt`) references sitemap
- Canonical URLs via `SITE_BASE_URL` setting
- JSON-LD schema.org/Vehicle markup on listing detail pages
- Markdown guides in `guides/content/` with slug-based routing

## Settings & Configuration

### Settings Split
- **base.py** - Shared config (apps, middleware, templates, auth, feature flags)
- **local.py** - Development (DEBUG=True, console email backend)
- **production.py** - Production overrides (S3 storage, SES, security headers)

Default settings module: `config.settings.local` (see manage.py:9, Dockerfile:8)

### Critical Environment Variables
```bash
# Database - Use SQLite for tests/local dev
DATABASE_URL=sqlite:///db.sqlite3  # Or postgres://...

# Feature flags (keep OFF for MVP)
FEATURE_SAVED_SEARCHES=False
FEATURE_WATCHLISTS=False
SES_ENABLED=False  # Use console email in dev

# Trust & Safety
INQUIRY_RATE_LIMIT_PER_MINUTE=5
CAPTCHA_PROVIDER=none  # or turnstile/hcaptcha

# Auth (optional Google OAuth)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# AWS (for production S3/SES)
DJANGO_USE_S3_MEDIA=False
AWS_STORAGE_BUCKET_NAME=
SES_VERIFIED_FROM_EMAIL=
```

### Authentication
- django-allauth handles email + Google OAuth
- Custom signup form captures role selection
- Login redirects to `/` (configurable via `DJANGO_LOGIN_REDIRECT_URL`)
- `accounts.User` uses email as username (no separate username field)

## Front-End

### Style System
See [STYLE_GUIDE.md](STYLE_GUIDE.md) for comprehensive design tokens and component patterns.

**Stack:**
- Pico CSS base + custom `static/css/ev.css` for tokens
- HTMX for interactivity (no heavy JS framework)
- CSS custom properties namespace: `--ev-color-*`, `--ev-space-*`, `--ev-radius-*`

**Key Component Classes:**
- `.ev-card`, `.ev-card__body`, `.ev-card__media` - Listing/dealer cards
- `.ev-filter-bar` - Faceted search interface
- `.ev-dashboard`, `.ev-sidebar` - Dashboard shell
- `.ev-table`, `.ev-table-wrapper` - Data tables with actions
- `.ev-form`, `.ev-form__section` - CRUD forms
- `.ev-badge` - Status indicators (success/warning/danger)
- `.ev-alert` - Contextual messaging
- `.ev-prose` - Markdown content styling

**When editing templates:**
1. Use design system classes from STYLE_GUIDE.md
2. Avoid inline styles
3. Co-locate HTMX partials with parent templates
4. Ensure 44px touch targets and WCAG AA contrast

## Testing Strategy

### Test Database Setup
Always use `DATABASE_URL=sqlite:///db.sqlite3` for tests to avoid Postgres dependency:
```powershell
$env:DATABASE_URL = "sqlite:///db.sqlite3"
python manage.py test
```

### CI Pipeline (.github/workflows/ci.yml)
1. **Lint** - ruff, black, isort
2. **Security** - bandit scan
3. **Accessibility** - Playwright + axe-core smoke tests
4. **SQLite tests** - Fast test suite
5. **Postgres tests** - Full integration with seeded data

### Key Test Coverage
- Listing visibility (only approved listings are public)
- Status transitions and timestamp updates
- Inquiry rate limiting and captcha verification
- Dealer inventory filtering
- Photo primary selection logic
- Sitemap generation (listings + guides)

## Deployment

### Docker
```bash
# Local stack
docker compose up

# Production build uses Dockerfile with:
# - Debian 12 slim base
# - Python 3.11
# - Gunicorn via docker/entrypoint.sh
# - Settings: config.settings.production
```

### Terraform (AWS Infrastructure)
```bash
cd terraform
# Configure backend (S3 + DynamoDB)
# Populate .tfvars (staging/prod)
terraform init
terraform plan -var-file=staging.tfvars
terraform apply  # Requires GitHub environment approval
```

**Modules:**
- App Runner or Elastic Beanstalk (web tier)
- RDS Postgres
- ElastiCache Redis
- S3 (media storage)
- SES (email)

See [terraform/README.md](terraform/README.md) and [CONNECTOR_TODO.md](CONNECTOR_TODO.md) for production integration checklist.

## MVP Scope & Feature Flags

### Ship This
- Public catalogue with filters (make/model/year/price/km/province/drivetrain/DCFC/heat pump)
- Listing detail with gallery, EV specs, inquiry form, JSON-LD
- Seller dashboard (CRUD, notifications)
- Admin moderation workflow
- Dealer profile pages
- Guides (Buyer's Checklist, Charging 101, Winter Range)
- SEO baseline (sitemap, robots, canonical URLs)

### Deferred (Feature-Flagged OFF)
- Saved searches (`FEATURE_SAVED_SEARCHES=False`)
- Watchlists (`FEATURE_WATCHLISTS=False`)
- In-platform messaging
- VIN integrations
- Payments/monetization
- Advanced media lifecycle (presigned uploads, stale cleanup)

## Common Development Patterns

### Adding a New Listing Field
1. Add field to `listings.models.Listing`
2. Create migration: `python manage.py makemigrations`
3. Update `dashboard/forms.py` and `dashboard/listings/form.html`
4. Add to filter logic in `listings/views.py` if needed
5. Update listing card partial: `templates/listings/partials/listing_card.html`
6. Run tests: `python manage.py test listings`

### Creating a Management Command
```python
# listings/management/commands/my_command.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Description"

    def handle(self, *args, **options):
        # Implementation
        self.stdout.write(self.style.SUCCESS("Done"))
```

Run: `python manage.py my_command`

### Working with HTMX Partials
1. Create partial in `templates/app/partials/component.html`
2. Load in view with `render(request, "app/partials/component.html", context)`
3. Return with `hx-swap="outerHTML"` or `hx-swap="innerHTML"` attribute
4. Test manually + add Playwright coverage for critical paths

### Running Database Migrations
```powershell
# Create migration after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration plan
python manage.py showmigrations

# Rollback (use with caution)
python manage.py migrate app_name migration_name
```

## Important Conventions

- **Windows development** - Use PowerShell, respect `py -3.11` launcher, handle path separators
- **Photo limits** - Max 10 photos per listing (enforced in form validation)
- **Slug generation** - Auto-generated from title/name with collision handling (see Listing.save(), ModelSpec.save())
- **Status transitions** - Use `Listing.transition()` method to maintain timestamp consistency
- **Inquiry viewing** - Mark inquiries as viewed via `mark_viewed()` to update `seller_notified_at`
- **Seeding demo data** - `seed_models` command creates [DEMO] prefixed entities for QA
- **Static files** - Run `collectstatic` before production deploy
- **Email in dev** - Uses console backend by default; set `SES_ENABLED=True` for real delivery

## Reference Links

- [Django 5 Docs](https://docs.djangoproject.com/en/5.0/)
- [HTMX](https://htmx.org/)
- [django-allauth](https://docs.allauth.org/en/latest/)
- [Pico CSS](https://picocss.com/)
- [STYLE_GUIDE.md](STYLE_GUIDE.md) - Front-end design system
- [README.md](README.md) - Setup and MVP scope
- [PROGRESS.md](PROGRESS.md) - Implementation timeline
