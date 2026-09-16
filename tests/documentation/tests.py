from django.urls import reverse

from tests.testing import parse_response


def test_index(client, db, snapshot):
    response = client.get(reverse("documentation:index"))
    assert parse_response(response, "#main") == snapshot


def test_category(client, db, snapshot):
    url = reverse("documentation:category", args=("evaluer-et-développer-les-compétences",))
    response = client.get(url)
    assert parse_response(response, "#main") == snapshot(name="no_filter")

    response = client.get(url + "?tag=formations")
    assert parse_response(response, "#main") == snapshot(name="with_filter")


def test_card(client, db, snapshot):
    url = reverse("documentation:card", args=("les-certificats-cléa",))
    response = client.get(url)
    assert parse_response(response, "#main") == snapshot
