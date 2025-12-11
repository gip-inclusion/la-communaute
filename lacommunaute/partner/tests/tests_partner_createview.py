import pytest
from django.urls import reverse

from lacommunaute.partner.models import Partner
from lacommunaute.users.factories import StaffUserFactory, UserFactory


@pytest.fixture(name="url")
def url_fixture():
    return reverse("partner:create")


@pytest.mark.parametrize("user_factory,status_code", [(None, 302), (UserFactory, 403), (StaffUserFactory, 200)])
def test_user_passes_test_mixin(client, db, url, user_factory, status_code):
    if user_factory:
        client.force_login(user_factory())
    response = client.get(url)
    assert response.status_code == status_code


def test_view(db, admin_client, url):
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.context["title"] == "Créer une nouvelle page partenaire"
    assert response.context["back_url"] == reverse("partner:list")
    assert list(response.context["form"].fields.keys()) == ["name", "short_description", "description", "logo", "url"]


def test_post_partner(db, admin_client, url):
    data = {
        "name": "Test",
        "short_description": "Short description",
        "description": "# Titre\ntext",
        "url": "https://www.example.com",
    }
    response = admin_client.post(url, data)
    assert response.status_code == 302

    partner = Partner.objects.get()
    assert response.url == reverse("partner:detail", kwargs={"pk": partner.pk, "slug": partner.slug})
    assert partner.description.raw == "# Titre\ntext"
