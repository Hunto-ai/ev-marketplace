"""Local development settings."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"]
)
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
)

EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

INTERNAL_IPS = ["127.0.0.1"]

if SECRET_KEY == "insecure-secret-key":
    SECRET_KEY = "dev-secret-key"

DATABASES["default"] = env.db(
    "DATABASE_URL",
    default="postgres://evthing:password@localhost:5432/evthing",
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "local-cache",
    }
}
