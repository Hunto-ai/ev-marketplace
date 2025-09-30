"""Production settings."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403

DEBUG = False

if SECRET_KEY == "insecure-secret-key":
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set for production")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must include deployment hosts")

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

try:
    DATABASES["default"] = env.db("DATABASE_URL")
except Exception as exc:  # pragma: no cover - fail fast in prod
    raise ImproperlyConfigured("DATABASE_URL must be configured for production") from exc

CACHES = {
    "default": env.cache(
        "DJANGO_CACHE_URL",
        default="locmem://",
    )
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=True)
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=DEFAULT_FROM_EMAIL)
SERVER_EMAIL = env("SERVER_EMAIL", default=SERVER_EMAIL)

EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)

DEFAULT_FILE_STORAGE = env(
    "DJANGO_DEFAULT_FILE_STORAGE",
    default="django.core.files.storage.FileSystemStorage",
)

STATICFILES_STORAGE = env(
    "DJANGO_STATICFILES_STORAGE",
    default="django.contrib.staticfiles.storage.StaticFilesStorage",
)
