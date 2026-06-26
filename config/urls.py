from django.conf import settings
from django.contrib.flatpages import views
from django.urls import include, path, re_path

from lacommunaute.documentation import urls as documentation_urls
from lacommunaute.pages import urls as pages_urls
from lacommunaute.partner import urls as partner_urls
from lacommunaute.search import urls as search_urls


urlpatterns = [
    path("", include(pages_urls)),
    path("documentation/", include(documentation_urls)),
    path("search/", include(search_urls)),
    path("partenaires/", include(partner_urls)),
]

urlpatterns += [
    re_path(r"^(?P<url>.*/)$", views.flatpage),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
