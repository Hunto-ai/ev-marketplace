# Progress Log

## 2025-09-30

### Implemented
- Inquiry safety guardrails: per-listing/IP rate limiting, captcha verification, delivery status tracking, SES relay wiring.
- Seller notifications: dashboard badge plus notifications view with unread tracking and delivery metadata.
- Dealer public presence: `/dealers/` index, dealer detail pages, and dealer-aware catalogue filtering/cards.
- Content & SEO: Markdown-driven guides, canonical URLs, combined listings/guides sitemap, and robots.txt endpoint.

### Assumptions & Notes
- `FEATURE_SAVED_SEARCHES` remains `False`; saved-search UX hidden until post-MVP.
- Captcha provider defaults to `none` in development; provide `turnstile` or `hcaptcha` keys before enabling.
- SES runs in sandbox mode unless production credentials are supplied; with `SES_ENABLED=False` email uses console backend.
- Tests should run with `DATABASE_URL=sqlite:///db.sqlite3` for local/CI unless Postgres credentials are available.
## 2025-09-30 (session close)
- Added Markdown-driven guides, sitemap/robots wiring, dealer filters, canonical URLs, README/.env refresh, and enforcement tests (SQLite-based).
- Session closed, next bot should pick up from CI wiring.

## 2025-09-30 (CI & QA)

### Implemented
- Locked Terraform deploys behind GitHub environment approvals (`staging`/`production`) and documented the manual apply flow.
- Updated `.github/workflows/ci.yml` with lint, security, Playwright + axe accessibility smoke, sqlite, and Postgres jobs.
- Added `package.json`, Playwright config/specs, and seeded demo routes for accessibility smoke coverage.
- Expanded `manage.py seed_models` with `[DEMO]` dealers, listings, and representative inquiries/events for dashboard QA.

### Tests
- `.venv/Scripts/python.exe manage.py test` with `DATABASE_URL=sqlite:///db.sqlite3`.
- `.venv/Scripts/python.exe manage.py seed_models`.
- `npm run test:a11y` (after `python manage.py runserver`).

### Next Up
- Populate GitHub environment secrets (AWS/Terraform) and required reviewers ahead of first deploy.
- Grow the Playwright suite to cover authenticated seller paths and JSON-LD assertions.
- Add seeded demo notifications/inbox read states once dashboard moderation polish lands.

