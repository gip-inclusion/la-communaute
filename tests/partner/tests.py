from django.urls import reverse

from tests.testing import parse_response


def test_partner_detailview(client, db, snapshot):
    response = client.get(
        reverse("partner:detail", args=("les-cidff-centres-dinformation-sur-les-droits-des-femmes-et-des-familles",))
    )
    assert response.status_code == 200
    assert parse_response(response, selector="main", replace_img_src=True) == snapshot


def test_partner_detailview_with_forums(client, db, snapshot):
    response = client.get(reverse("partner:detail", args=("1-jeune-1-solution",)))
    assert response.status_code == 200
    assert parse_response(response, selector="main", replace_img_src=True) == snapshot


def test_listview(client, db, snapshot):
    response = client.get(reverse("partner:list"))
    assert response.status_code == 200
    assert parse_response(response, selector="#partner-list", replace_img_src=True) == snapshot
