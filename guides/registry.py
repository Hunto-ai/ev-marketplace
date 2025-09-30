from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from typing import Iterable, List

from django.utils import timezone

BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Guide:
    slug: str
    title: str
    description: str
    filename: Path

    @property
    def last_modified(self) -> datetime:
        try:
            ts = self.filename.stat().st_mtime
        except FileNotFoundError:
            return timezone.now()
        dt = datetime.fromtimestamp(ts, tz=dt_timezone.utc)
        return dt.astimezone(timezone.get_default_timezone())

    def read(self) -> str:
        return self.filename.read_text(encoding="utf-8")


GUIDES: List[Guide] = [
    Guide(
        slug="buyers-checklist",
        title="EV Buyer's Checklist",
        description="Everything to review before signing for your next EV.",
        filename=BASE_DIR / "content" / "buyers-checklist.md",
    ),
    Guide(
        slug="charging-101",
        title="Charging 101",
        description="Understand connectors, charging speeds, and home setup essentials.",
        filename=BASE_DIR / "content" / "charging-101.md",
    ),
    Guide(
        slug="winter-range",
        title="Maximizing Winter Range",
        description="Practical steps to keep range steady through Canadian winters.",
        filename=BASE_DIR / "content" / "winter-range.md",
    ),
]


def get_guides() -> List[Guide]:
    return GUIDES


def get_guide(slug: str) -> Guide | None:
    for guide in GUIDES:
        if guide.slug == slug:
            return guide
    return None
