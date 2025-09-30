"""
Base Django settings shared across environments.
"""

from __future__ import annotations

import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialise environment reader and optionally load a .env file.
env = environ.Env()
_env_file = os.environ.get("DJANGO_ENV_FILE", BASE_DIR / ".env")
if _env_file:
    _wrapped_path = Path(_env_file)
    if _wrapped_path.exists():
        environ.Env.read_env(_wrapped_path)

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-secret-key")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
SITE_ID = env.int("DJANGO_SITE_ID", default=1)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.humanize",
    "accounts",
    "dealers",
    "listings",
    "dashboard",
    "guides",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = env("DJANGO_LANGUAGE_CODE", default="en-us")
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = env("DJANGO_STATIC_URL", default="/static/")
STATIC_ROOT = env("DJANGO_STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
STATICFILES_DIRS: list[Path] = [p for p in [BASE_DIR / "static"] if p.exists()]

MEDIA_URL = env("DJANGO_MEDIA_URL", default="/media/")
MEDIA_ROOT = env("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media"))
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_SESSION_TOKEN = env("AWS_SESSION_TOKEN", default="")
AWS_DEFAULT_REGION = env("AWS_DEFAULT_REGION", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
AWS_S3_SIGNATURE_VERSION = env("AWS_S3_SIGNATURE_VERSION", default="s3v4")
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": env("AWS_S3_CACHE_CONTROL", default="max-age=86400"),
}
AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=False)
AWS_S3_FILE_OVERWRITE = env.bool("AWS_S3_FILE_OVERWRITE", default=False)

USE_S3_MEDIA = env.bool("DJANGO_USE_S3_MEDIA", default=False)

if USE_S3_MEDIA:
    DEFAULT_FILE_STORAGE = env(
        "DJANGO_DEFAULT_FILE_STORAGE",
        default="storages.backends.s3boto3.S3Boto3Storage",
    )
    if AWS_STORAGE_BUCKET_NAME:
        default_domain = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
        if AWS_S3_CUSTOM_DOMAIN:
            MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
        else:
            MEDIA_URL = f"https://{default_domain}/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="EV Marketplace <no-reply@example.com>")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)

SITE_BASE_URL = env("SITE_BASE_URL", default="")
FEATURE_SAVED_SEARCHES = env.bool("FEATURE_SAVED_SEARCHES", default=False)
FEATURE_WATCHLISTS = env.bool("FEATURE_WATCHLISTS", default=False)
SES_ENABLED = env.bool("SES_ENABLED", default=False)
SES_VERIFIED_FROM_EMAIL = env("SES_VERIFIED_FROM_EMAIL", default="")
INQUIRY_RATE_LIMIT_PER_MINUTE = env.int("INQUIRY_RATE_LIMIT_PER_MINUTE", default=5)
CAPTCHA_PROVIDER = env("CAPTCHA_PROVIDER", default="none")
CAPTCHA_SITE_KEY = env("CAPTCHA_SITE_KEY", default="")
CAPTCHA_SECRET_KEY = env("CAPTCHA_SECRET_KEY", default="")
ENABLE_ANALYTICS = env.bool("ENABLE_ANALYTICS", default=False)

LOGIN_REDIRECT_URL = env("DJANGO_LOGIN_REDIRECT_URL", default="/")
LOGOUT_REDIRECT_URL = env("DJANGO_LOGOUT_REDIRECT_URL", default="/")
LOGIN_URL = "account_login"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="optional")
ACCOUNT_ADAPTER = env("DJANGO_ACCOUNT_ADAPTER", default="allauth.account.adapter.DefaultAccountAdapter")
SOCIALACCOUNT_ADAPTER = env(
    "DJANGO_SOCIALACCOUNT_ADAPTER",
    default="allauth.socialaccount.adapter.DefaultSocialAccountAdapter",
)
SOCIALACCOUNT_EMAIL_VERIFICATION = ACCOUNT_EMAIL_VERIFICATION
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
    "first_name",
    "last_name",
    "role",
]
ACCOUNT_FORMS = {
    "signup": "accounts.forms.SignupForm",
}
ACCOUNT_RATE_LIMITS = {
    "login_failed": env("ACCOUNT_RATE_LIMIT_LOGIN_FAILED", default="5/5m"),
}

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID", default=""),
            "secret": env("GOOGLE_CLIENT_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "offline"},
    }
}





