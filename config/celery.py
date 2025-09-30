"""Celery application configuration for the EV Marketplace project."""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("evthing")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self, *args, **kwargs):  # pragma: no cover - developer helper
    print(f"Celery debug task executed with request: {self.request!r}")
