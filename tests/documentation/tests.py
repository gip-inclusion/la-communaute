
from django.urls import reverse
from faker import Faker

from tests.testing import parse_response_to_soup


faker = Faker()


def test_index(client, db, snapshot):
    response = client.get(reverse("documentation:index"))
    assert str(parse_response_to_soup(response, "#main")) == snapshot


def test_category(client, db, snapshot):
    url = reverse("documentation:category", args=("evaluer-et-développer-les-compétences",))
    response = client.get(url)
    assert str(parse_response_to_soup(response, "#main")) == snapshot(name="no_filter")

    response = client.get(url + "?tag=formations")
    assert str(parse_response_to_soup(response, "#main")) == snapshot(name="with_filter")


def test_card(client, db, snapshot):
    url = reverse("documentation:card", args=("les-certificats-cléa",))
    response = client.get(url)
    assert str(parse_response_to_soup(response, "#main")) == snapshot
