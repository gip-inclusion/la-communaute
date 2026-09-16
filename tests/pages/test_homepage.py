import re

from django.urls import reverse

from tests.testing import parse_response


def _sub_svg_suffix(content):
    return re.sub(r"\.\w+\.svg", ".svg", content)


def test_page_title_header_footer(db, client, snapshot):
    response = client.get(reverse("pages:home"))
    assert response.status_code == 200

    assert parse_response(response, selector="title") == snapshot(name="homepage_title")

    header = _sub_svg_suffix(parse_response(response, selector="header"))
    assert header == snapshot(name="homepage_header")

    footer = _sub_svg_suffix(parse_response(response, selector="footer"))
    assert footer == snapshot(name="homepage_footer")
