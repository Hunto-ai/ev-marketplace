from django.conf import settings
from django.http import HttpResponse


def robots_txt(request):
    base = settings.SITE_BASE_URL.rstrip("/") if getattr(settings, "SITE_BASE_URL", "") else ""
    if not base:
        base = request.build_absolute_uri("/").rstrip("/")
    sitemap_url = f"{base}/sitemap.xml"
    content = "\n".join([
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
        "",
    ])
    return HttpResponse(content, content_type="text/plain")
