import re

from django.urls import reverse
from itoutils.django.testing import assertSnapshotQueries

from tests.forum.factories import CategoryForumFactory, ForumFactory
from tests.testing import parse_response_to_soup


def _sub_svg_suffix(content):
    return re.sub(r"\.\w+\.svg", ".svg", content)


def test_page_title_header_footer(db, client, snapshot):
    response = client.get(reverse("pages:home"))
    assert response.status_code == 200

    assert str(parse_response_to_soup(response, selector="title")) == snapshot(name="homepage_title")

    header = _sub_svg_suffix(str(parse_response_to_soup(response, selector="header")))
    assert header == snapshot(name="homepage_header")

    footer = _sub_svg_suffix(str(parse_response_to_soup(response, selector="footer")))
    assert footer == snapshot(name="homepage_footer")


def test_queries(db, client, snapshot):
    with assertSnapshotQueries(snapshot):
        client.get(reverse("pages:home"))


def test_updated_forum_short_description(client, db, snapshot):
    parent = CategoryForumFactory()
    forum = ForumFactory(
        name="84, rue Georges",
        short_description="C'était partout, dans le monde entier, des centaines ou des milliers de millions de gens "
        "s'ignorant les uns les autres, séparés par des murs de haine et de mensonges, et cependant presque exactement"
        " les mêmes, des gens qui n'avaient jamais appris à penser, mais qui emmagasinaient dans leurs cœurs, leurs ve"
        "ntres et leurs muscles, la force qui, un jour, bouleverserait le monde.",
        parent=parent,
    )

    response = client.get(reverse("pages:home"))
    content = parse_response_to_soup(response, selector="#updated_forums", replace_in_href=[forum])
    assert str(content) == snapshot(name="truncated_encoded_short_description")
