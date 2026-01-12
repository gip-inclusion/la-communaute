import pytest
from django.urls import reverse

from tests.partner.factories import PartnerFactory
from tests.users.factories import StaffUserFactory, UserFactory


@pytest.fixture(name="partner")
def partner_fixture():
    return PartnerFactory(for_snapshot=True)


@pytest.fixture(name="url")
def url_fixture(partner):
    return reverse("partner:update", kwargs={"pk": partner.id, "slug": partner.slug})


@pytest.mark.parametrize("user_factory,status_code", [(None, 302), (UserFactory, 403), (StaffUserFactory, 200)])
def test_user_passes_test_mixin(client, db, url, user_factory, status_code):
    if user_factory:
        client.force_login(user_factory())
    response = client.get(url)
    assert response.status_code == status_code


def test_view(db, admin_client, url, partner):
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.context["title"] == f"Modifier la page {partner.name}"
    assert response.context["back_url"] == reverse("partner:detail", kwargs={"pk": partner.pk, "slug": partner.slug})
    assert list(response.context["form"].fields.keys()) == ["name", "short_description", "description", "logo", "url"]


def test_post_partner(db, admin_client, url, partner):
    data = {
        "name": "Test",
        "short_description": "Short description",
        "description": "# Titre\ndescription",
        "url": "https://www.example.com",
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    partner.refresh_from_db()
    assert response.url == reverse("partner:detail", kwargs={"pk": partner.pk, "slug": partner.slug})
    assert partner.description.rendered == "<h1>Titre</h1>\n\n<p>description</p>"
