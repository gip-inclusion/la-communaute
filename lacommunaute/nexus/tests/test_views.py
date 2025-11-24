import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from lacommunaute.nexus import utils
from lacommunaute.users.factories import UserFactory
from lacommunaute.utils.testing import reload_module
from lacommunaute.utils.urls import add_url_params


class TestAutoLogin:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        mocker.patch("lacommunaute.nexus.views.generate_jwt", return_value="JWT")

    def test_login_required(self, db, client):
        next_url = f"https://{settings.NEXUS_ALLOWED_REDIRECT_HOSTS[0]}"
        url = reverse("nexus:auto_login", query={"next_url": next_url})
        response = client.get(url)
        assertRedirects(response, add_url_params(reverse("users:login"), {"next": url}))

    def test_nominal_case(self, db, client):
        client.force_login(UserFactory())
        for host in settings.NEXUS_ALLOWED_REDIRECT_HOSTS:
            next_url = f"https://{host}"
            url = reverse("nexus:auto_login", query={"next_url": next_url})
            response = client.get(url)
            assertRedirects(response, add_url_params(next_url, {"auto_login": "JWT"}), fetch_redirect_response=False)

    def test_missing_next_url(self, db, client):
        client.force_login(UserFactory())
        # Without next_url
        url = reverse("nexus:auto_login")
        response = client.get(url)
        assert response.status_code == 404

    def test_bad_host(self, db, client):
        client.force_login(UserFactory())
        next_url = "https://d0main.fr"
        url = reverse("nexus:auto_login", query={"next_url": next_url})
        response = client.get(url)
        assert response.status_code == 404

    @override_settings(NEXUS_AUTO_LOGIN_KEY=None)
    @reload_module(utils)
    def test_no_settings(self, db, client):
        client.force_login(UserFactory())
        next_url = f"https://{settings.NEXUS_ALLOWED_REDIRECT_HOSTS[0]}"
        url = reverse("nexus:auto_login", query={"next_url": next_url})
        response = client.get(url)
        assert response.status_code == 404
