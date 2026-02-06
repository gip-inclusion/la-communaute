import json

from django.core.management import call_command
from django.utils import timezone
from freezegun import freeze_time

from lacommunaute.nexus.management.commands.populate_metabase_nexus import create_table, get_connection
from tests.users.factories import UserFactory


@freeze_time()
def test_populate_metabase_nexus(db):
    user = UserFactory()

    create_table()
    call_command("populate_metabase_nexus")

    with get_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        assert rows == [
            (
                "la-communauté",
                str(user.pk),
                f"la-communauté--{user.pk}",
                user.last_name,
                user.first_name,
                user.email,
                "",
                user.last_login,
                user.get_identity_provider_display(),
                "N/A",
                timezone.now(),
            ),
        ]


def test_full_sync(db, mock_nexus_api):
    user = UserFactory()
    UserFactory(is_active=False)
    UserFactory(email="")
    UserFactory(is_staff=True)
    mock_nexus_api.reset()

    call_command("nexus_full_sync")

    [call_init, call_sync_users, call_completed] = mock_nexus_api.calls

    assert call_init.request.method == "POST"
    assert call_init.request.url == "http://nexus/api/sync-start"
    started_at = call_init.response.json()["started_at"]
    assert call_sync_users.request.method == "POST"
    assert call_sync_users.request.url == "http://nexus/api/users"
    assert json.loads(call_sync_users.request.content.decode()) == [
        {
            "id": str(user.pk),
            "kind": "",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": "",
            "last_login": None,
            "auth": "PRO_CONNECT",
        },
    ]
    assert call_completed.request.method == "POST"
    assert call_completed.request.url == "http://nexus/api/sync-completed"
    assert json.loads(call_completed.request.content.decode()) == {"started_at": started_at}
