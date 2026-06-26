import logging

from django.shortcuts import render
from django.views.generic.base import TemplateView


logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "pages/home.html"


def accessibilite(request):
    return render(request, "pages/accessibilite.html")


def mentions_legales(request):
    return render(request, "pages/mentions_legales.html")


def politique_de_confidentialite(request):
    return render(request, "pages/politique_de_confidentialite.html")
