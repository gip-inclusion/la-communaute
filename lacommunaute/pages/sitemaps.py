from django.contrib.flatpages.models import FlatPage
from django.contrib.sitemaps import Sitemap
from django.db.models.base import Model
from django.urls import reverse

from lacommunaute.documentation.helpers import CARDS, CATEGORIES
from lacommunaute.partner.helpers import PARTNERS


class PagesSitemap(Sitemap):
    def items(self):
        return FlatPage.objects.filter(registration_required=False).order_by("title")

    def location(self, obj: Model) -> str:
        return super().location(obj).replace("/flatpages/", "/")

    def changefreq(self, obj: Model) -> str:
        return "weekly"


class DocumentationCategorySitemap(Sitemap):
    def items(self):
        return CATEGORIES

    def location(self, obj: Model) -> str:
        return reverse("documentation:category", kwargs={"slug": obj["slug"]})


class DocumentationCardSitemap(Sitemap):
    def items(self):
        return list(CARDS.values())

    def location(self, obj: Model) -> str:
        return reverse("documentation:card", kwargs={"slug": obj["slug"]})


class PartnerSitemap(Sitemap):
    def items(self):
        return list(PARTNERS.values())

    def location(self, obj: Model) -> str:
        return reverse("partner:detail", kwargs={"slug": obj["slug"]})
