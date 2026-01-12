import logging

from django.urls import reverse
from itoutils.django.nexus.token import generate_token
from pytest_django.asserts import assertRedirects

from lacommunaute.users.enums import IdentityProvider
from tests.users.factories import UserFactory


def test_middleware_for_authenticated_user(db, client, caplog):
    user = UserFactory()
    client.force_login(user)
    params = {"auto_login": generate_token(user)}
    response = client.get(reverse("search:index", query=params))
    assertRedirects(response, "/search/", fetch_redirect_response=False)


def test_middleware_for_wrong_authenticated_user(db, client, caplog):
    caplog.set_level(logging.INFO)
    user = UserFactory()
    params = {"auto_login": generate_token(user)}

    # Another user is logged in
    client.force_login(UserFactory())

    response = client.get(reverse("search:index", query=params))
    assertRedirects(
        response,
        reverse("openid_connect:authorize", query={"next": "/search/", "login_hint": user.email}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [
        "Nexus auto login: wrong user is logged in -> logging them out",
        f"Nexus auto login: {user} was found and forwarded to ProConnect",
    ]


def test_middleware_with_no_existing_user(db, client, caplog):
    caplog.set_level(logging.INFO)

    user = UserFactory.build()
    jwt = generate_token(user)
    params = {"auto_login": jwt}
    response = client.get(reverse("search:index", query=params))
    assertRedirects(
        response,
        reverse("openid_connect:authorize", query={"next": "/search/", "login_hint": user.email}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [
        f"Nexus auto login: no user found for jwt={jwt}",
        "Nexus auto login: forward to ProConnect to create account",
    ]


def test_middleware_for_unlogged_user(db, client, caplog):
    caplog.set_level(logging.INFO)

    user = UserFactory()
    params = {"auto_login": generate_token(user)}
    response = client.get(reverse("search:index", query=params))
    assertRedirects(
        response,
        reverse("openid_connect:authorize", query={"next": "/search/", "login_hint": user.email}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [f"Nexus auto login: {user} was found and forwarded to ProConnect"]

    # It also works if it's not a ProConnect user
    user.identity_provider = IdentityProvider.INCLUSION_CONNECT
    user.save()
    caplog.clear()

    response = client.get(reverse("search:index", query=params))
    assertRedirects(
        response,
        reverse("openid_connect:authorize", query={"next": "/search/", "login_hint": user.email}),
        fetch_redirect_response=False,
    )
    assert caplog.messages == [f"Nexus auto login: {user} was found and forwarded to ProConnect"]
