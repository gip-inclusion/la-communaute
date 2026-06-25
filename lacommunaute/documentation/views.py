from django.http import Http404
from django.views.generic import TemplateView

from lacommunaute.documentation.helpers import CARDS, CATEGORIES, get_cards
from lacommunaute.partner.helpers import PARTNERS


class DocumentationIndexView(TemplateView):
    template_name = "documentation/index.html"

    def get_context_data(self, **kwargs):
        return {"categories": CATEGORIES}


class DocumentationCategoryView(TemplateView):
    def get_template_names(self):
        if self.request.META.get("HTTP_HX_REQUEST"):
            return ["documentation/partials/cards_list.html"]
        return ["documentation/category.html"]

    def setup(self, request, *args, slug, **kwargs):
        super().setup(request, *args, slug, **kwargs)
        self.slug = slug
        try:
            [self.category] = [category for category in CATEGORIES if category["slug"] == self.slug]
        except ValueError:
            raise Http404

    def get_context_data(self, **kwargs):
        tags = []
        tag_filter = self.request.GET.get("tag") or None
        cards = []

        tag_slug = set()
        for card in get_cards(self.slug):
            # Only keep the cards from this category
            if card["category_slug"] != self.slug:
                continue

            keep = False
            for tag in card["tags"] or []:
                # List all tags from this category
                if tag["slug"] not in tag_slug:
                    tag_slug.add(tag["slug"])
                    tags.append(tag)
                # filter based on tag
                if tag_filter and tag["slug"] == tag_filter:
                    keep = True
            if tag_filter and keep is False:
                continue
            cards.append(card)

        return {
            "category": self.category,
            "cards": cards,
            "tags": tags,
            "active_tag_slug": tag_filter,
        }


class DocumentationCardView(TemplateView):
    template_name = "documentation/card.html"

    def setup(self, request, *args, slug, **kwargs):
        super().setup(request, *args, slug, **kwargs)
        self.slug = slug
        try:
            self.card = CARDS[self.slug]
            [self.category] = [category for category in CATEGORIES if category["slug"] == self.card["category_slug"]]
        except (KeyError, ValueError):
            raise Http404

    def get_context_data(self, **kwargs):
        return {
            "card": self.card,
            "category": self.category,
            "sibling_cards": get_cards(self.category["slug"]),
            "partner": PARTNERS[self.card["partner"]] if self.card["partner"] else None,
        }
