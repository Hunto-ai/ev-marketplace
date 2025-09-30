from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"

PROVIDER_FIELD_NAMES = {
    "turnstile": "cf-turnstile-response",
    "hcaptcha": "h-captcha-response",
}


def get_provider() -> str:
    return getattr(settings, "CAPTCHA_PROVIDER", "none").strip().lower()


def get_field_name() -> str | None:
    provider = get_provider()
    return PROVIDER_FIELD_NAMES.get(provider)


def get_site_key() -> str:
    return getattr(settings, "CAPTCHA_SITE_KEY", "")


def verify_captcha(response_token: str | None, remote_ip: str | None = None) -> tuple[bool, str | None, dict[str, Any]]:
    provider = get_provider()
    if provider in ("", "none"):
        return True, None, {}
    if not response_token:
        return False, "Captcha validation failed. Please try again.", {}
    secret = getattr(settings, "CAPTCHA_SECRET_KEY", "")
    if not secret:
        logger.warning("Captcha provider '%s' missing secret key", provider)
        return False, "Captcha configuration error. Please try again later.", {}
    data = {"secret": secret, "response": response_token}
    if remote_ip:
        data["remoteip"] = remote_ip
    if provider == "turnstile":
        endpoint = TURNSTILE_VERIFY_URL
    elif provider == "hcaptcha":
        endpoint = HCAPTCHA_VERIFY_URL
    else:
        logger.error("Unsupported captcha provider: %s", provider)
        return False, "Captcha provider misconfigured.", {}
    try:
        resp = requests.post(endpoint, data=data, timeout=5)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # pragma: no cover - network errors vary
        logger.warning("Captcha verification failed: %s", exc, exc_info=exc)
        return False, "Captcha verification failed. Please retry.", {}
    success = bool(payload.get("success"))
    if not success:
        return False, "Captcha verification failed. Please retry.", payload
    return True, None, payload
