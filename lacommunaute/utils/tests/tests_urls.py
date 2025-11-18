import sys

import pytest
from django.urls import NoReverseMatch, clear_url_caches, reverse

from lacommunaute.utils.urls import add_url_params, clean_next_url


@pytest.fixture(autouse=True)
def _clear_url_caches():
    clear_url_caches()
    # The module content depends on the settings, force tests to reimport it.
    sys.modules.pop("config.urls", None)


def test_django_urls_prod(settings):
    settings.DEBUG = False
    with pytest.raises(NoReverseMatch):
        reverse("djdt:render_panel")


@pytest.mark.parametrize(
    "url, expected", [(None, "/"), ("http://www.unallowed.com", "/"), ("/", "/"), ("/topics/", "/topics/")]
)
def test_clean_next_url(url, expected):
    assert clean_next_url(url) == expected


def test_add_url_params():
    # Test copied from les-emplois.
    # TODO: Move code to itoutils when it's available for django projects
    base_url = "http://localhost/test?next=/siae/search%3Fdistance%3D100%26city%3Dstrasbourg-67"

    url_test = add_url_params(base_url, {"test": "value"})
    assert url_test == "http://localhost/test?next=%2Fsiae%2Fsearch%3Fdistance%3D100%26city%3Dstrasbourg-67&test=value"

    url_test = add_url_params(base_url, {"mypath": "%2Fvalue%2Fpath"})

    assert url_test == (
        "http://localhost/test?next=%2Fsiae%2Fsearch%3Fdistance%3D100%26city%3Dstrasbourg-67"
        "&mypath=%252Fvalue%252Fpath"
    )

    url_test = add_url_params(base_url, {"mypath": None})

    assert url_test == "http://localhost/test?next=%2Fsiae%2Fsearch%3Fdistance%3D100%26city%3Dstrasbourg-67"

    url_test = add_url_params(base_url, {"mypath": ""})

    assert url_test == "http://localhost/test?next=%2Fsiae%2Fsearch%3Fdistance%3D100%26city%3Dstrasbourg-67&mypath="
