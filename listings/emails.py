from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.core.mail import send_mail

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .models import Inquiry

logger = logging.getLogger(__name__)


def build_inquiry_email(inquiry: "Inquiry") -> tuple[str, str, list[str]]:
    listing = inquiry.listing
    recipient = listing.seller.email if listing.seller and listing.seller.email else ""
    subject = f"New inquiry for {listing.title or listing}"
    message_lines = [
        "A new inquiry was submitted for your listing on EV Marketplace.",
        "",  # blank line
        f"Listing: {listing.title or listing}",
        f"Location: {listing.city}, {listing.get_province_display() if listing.province else ''}",
        "",
        "From:",
        f"Name: {inquiry.name}",
        f"Email: {inquiry.email}",
        f"Phone: {inquiry.phone_number or 'N/A'}",
        "",
        "Message:",
        inquiry.message,
    ]
    message = "\n".join(message_lines)
    recipients = [recipient] if recipient else []
    return subject, message, recipients


def send_inquiry_notification(inquiry: "Inquiry") -> tuple[bool, dict[str, Any]]:
    subject, message, recipients = build_inquiry_email(inquiry)
    if not recipients:
        error = "Listing seller does not have an email address configured."
        logger.warning(error)
        return False, {"error": error}

    if getattr(settings, "SES_ENABLED", False):
        return _send_with_ses(subject, message, recipients)
    return _send_with_backend(subject, message, recipients)


def _send_with_backend(subject: str, message: str, recipients: list[str]) -> tuple[bool, dict[str, Any]]:
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
    except Exception as exc:  # pragma: no cover - backend specific
        logger.warning("Error sending inquiry email via Django backend", exc_info=exc)
        return False, {"error": str(exc), "backend": settings.EMAIL_BACKEND}
    return True, {"backend": settings.EMAIL_BACKEND}


def _send_with_ses(subject: str, message: str, recipients: list[str]) -> tuple[bool, dict[str, Any]]:
    region = getattr(settings, "AWS_DEFAULT_REGION", "us-east-1") or "us-east-1"
    source = getattr(settings, "SES_VERIFIED_FROM_EMAIL", "") or settings.DEFAULT_FROM_EMAIL
    session = boto3.session.Session()
    client = session.client("ses", region_name=region)
    try:
        response = client.send_email(
            Source=source,
            Destination={"ToAddresses": recipients},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": message, "Charset": "UTF-8"}},
            },
            ReplyToAddresses=[settings.DEFAULT_FROM_EMAIL],
        )
    except (ClientError, BotoCoreError, ValueError) as exc:
        logger.warning("SES send_email failed", exc_info=exc)
        return False, {"error": str(exc), "service": "ses"}

    message_id = response.get("MessageId")
    metadata: dict[str, Any] = {"service": "ses"}
    if message_id:
        metadata["message_id"] = message_id
    return True, metadata
