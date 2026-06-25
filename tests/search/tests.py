import urllib.parse

import pytest
from django.core.management import call_command
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains


@pytest.fixture(name="search_url")
def search_url_fixture():
    return reverse("search:index")


@pytest.fixture(autouse=1)
def refresh_search_index(db):
    call_command("rebuild_index")


def test_search(client, db, search_url):
    query = ["Tout", "savoir", "sur"]
    response = client.get(search_url, {"q": " ".join(query)})

    for word in query:
        if word in ["Tout", "savoir"]:  # Stop words are ignored, thus not highlighted.
            assertContains(response, f'<span class="highlighted">{word}</span>')
        else:
            assertNotContains(response, f'<span class="highlighted">{word}</span>')


def test_search_with_no_query(client, db, search_url):
    response = client.get(search_url)
    assertContains(response, '<input type="search" name="q"')


def test_empty_search(client, db, search_url):
    response = client.get(search_url, {"q": ""})
    assertContains(response, '<input type="search" name="q"')


def test_search_with_no_results(client, db, search_url):
    response = client.get(search_url, {"q": "anticonstitutionnellement"})
    assertContains(response, "Aucun résultat")


def test_search_with_non_unicode_characters(client, db, search_url):
    encoded_char = urllib.parse.quote("\x1f")
    response = client.get(search_url, {"q": encoded_char})
    assertContains(response, "Aucun résultat")


def test_pagination_perserves_get_params(client, db, search_url):
    response = client.get(search_url, data={"q": "IAE"})
    assertContains(
        response,
        f'<a href="{search_url}?q=IAE&amp;page=2" class="page-link">2</a>',
        count=1,
    )
