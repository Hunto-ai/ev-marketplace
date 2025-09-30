from __future__ import annotations

from dataclasses import asdict
from typing import Any

import markdown
from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from .registry import Guide, get_guide, get_guides


def build_canonical_url(request, path: str) -> str:
    base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
    if base:
        return f"{base}{path}"
    return request.build_absolute_uri(path)


class GuideListView(TemplateView):
    template_name = "guides/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        guides = get_guides()
        context.update(
            {
                "guides": guides,
                "canonical_url": build_canonical_url(self.request, reverse("guides:list")),
            }
        )
        return context


class GuideDetailView(TemplateView):
    template_name = "guides/detail.html"

    def get_guide(self) -> Guide:
        slug = self.kwargs.get("slug")
        guide = get_guide(slug)
        if not guide:
            raise Http404("Guide not found")
        return guide

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        guide = self.get_guide()
        raw_markdown = guide.read()
        guide_html = markdown.markdown(
            raw_markdown,
            extensions=["extra", "toc"],
            output_format="html5",
        )
        context.update(
            {
                "guide": guide,
                "guide_html": guide_html,
                "canonical_url": build_canonical_url(
                    self.request, reverse("guides:detail", args=[guide.slug])
                ),
                "updated_at": guide.last_modified,
            }
        )
        return context
