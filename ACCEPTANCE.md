# MVP Acceptance Checklist

Use this checklist to verify the EV Marketplace MVP end-to-end before release.

- [ ] Create a seller account, add a listing (draft → pending), approve it in the Django admin, and confirm it appears on `/listings/`.
- [ ] Submit an inquiry on the public listing with `SES_ENABLED=False`; verify an `Inquiry` record is created and the console backend logs the email stub.
- [ ] Toggle `SES_ENABLED=True` with valid AWS credentials; submit another inquiry and confirm delivery status, message ID, and seller dashboard notification.
- [ ] Visit `/dealers/<slug>/` for an approved dealer and confirm that only active inventory renders.
- [ ] Review `/guides/` and each `/guides/<slug>/` page for rendered markdown, canonical URLs, and updated timestamps.
- [ ] Confirm `/sitemap.xml` includes active listings and guides, and `/robots.txt` advertises the sitemap URL.
- [ ] Inspect a listing detail page for schema.org Vehicle JSON-LD markup and canonical metadata.
- [ ] Ensure `FEATURE_SAVED_SEARCHES` remains `False` and saved-search UI is hidden on the catalogue.
- [ ] Run `python manage.py test` with `DATABASE_URL=sqlite:///db.sqlite3` and confirm all tests pass.
