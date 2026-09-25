from django.conf import settings
from django.http import HttpResponsePermanentRedirect, QueryDict
from django.shortcuts import render


class ParkingPageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.PARKING_PAGE and not request.path.startswith("/admin/"):
            return render(request, "middleware/parking.html")
        response = self.get_response(request)
        return response


# FIXME(alaurent) Remove in a few weeks
# once searching for "communauté inclusion" gives the new domain
class RedirectToNewDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        url = _get_redirect_url(request)
        if url is None:
            return None
        return HttpResponsePermanentRedirect(url)


def _get_redirect_url(request):
    if not settings.REDIRECT_TO_NEW_DOMAIN:
        return None
    if request.get_host() == settings.NEW_DOMAIN:
        return None

    query = QueryDict(request.GET.urlencode(), mutable=True)
    return f"https://{settings.NEW_DOMAIN}{request.path}?{query.urlencode()}"
