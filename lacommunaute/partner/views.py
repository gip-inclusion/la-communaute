from django.http import Http404
from django.views.generic import TemplateView

from lacommunaute.documentation.helpers import CARDS
from lacommunaute.partner.helpers import PARTNERS


class PartnerListView(TemplateView):
    template_name = "partner/list.html"

    def get_context_data(self, **kwargs):
        return {"partners": PARTNERS.values()}


class PartnerDetailView(TemplateView):
    template_name = "partner/detail.html"

    def setup(self, request, *args, slug, **kwargs):
        super().setup(request, *args, slug, **kwargs)
        self.slug = slug
        try:
            self.partner = PARTNERS[self.slug]
        except KeyError:
            raise Http404

    def get_context_data(self, **kwargs):
        cards = []

        for card in CARDS.values():
            if self.slug == card["partner"]:
                cards.append(card)

        return {
            "partner": self.partner,
            "cards": cards,
        }
