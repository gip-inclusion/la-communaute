import json

from django.utils import timezone

from lacommunaute.users.models import User
from tests.users.factories import UserFactory


def assert_call_content(call, expected_data):
    # the order doesn't matter
    data = json.loads(call.request.content.decode())
    assert sorted(data, key=lambda d: d["id"]) == sorted(expected_data, key=lambda d: d["id"])


class TestUserSync:
    def test_sync_on_model_save_new_instance(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        with django_capture_on_commit_callbacks(execute=True):
            user = UserFactory()

        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
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
            ],
        )

    def test_sync_on_model_save_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user.email = "another@email.com"
            user.last_login = timezone.now()
            user.save()
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
                {
                    "id": str(user.pk),
                    "kind": "",
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": "another@email.com",
                    "phone": "",
                    "last_login": user.last_login.isoformat(),
                    "auth": "PRO_CONNECT",
                },
            ],
        )

    def test_no_sync_on_model_save_no_changed_data(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user.save()
        assert mock_nexus_api.calls == []

    def test_no_sync_on_model_save_non_tracked_field(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user.username = "toto"
            user.save()
        assert mock_nexus_api.calls == []

    def test_delete_on_model_save(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        with django_capture_on_commit_callbacks(execute=True):
            user_1 = UserFactory(is_active=False)
            user_2 = UserFactory(email="")

        [call_1, call_2] = mock_nexus_api.calls
        assert call_1.request.method == "DELETE"
        assert call_1.request.url == "http://nexus/api/users"
        assert_call_content(call_1, [{"id": str(user_1.pk)}])
        assert call_2.request.method == "DELETE"
        assert call_2.request.url == "http://nexus/api/users"
        assert_call_content(call_2, [{"id": str(user_2.pk)}])

    def test_delete_on_model_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user = UserFactory()
        user_id = user.pk

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_id)}])

    def test_sync_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            User.objects.order_by("pk").update(first_name="John")
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
                {
                    "id": str(user_1.pk),
                    "kind": "",
                    "first_name": "John",
                    "last_name": user_1.last_name,
                    "email": user_1.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "PRO_CONNECT",
                },
                {
                    "id": str(user_2.pk),
                    "kind": "",
                    "first_name": "John",
                    "last_name": user_2.last_name,
                    "email": user_2.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "PRO_CONNECT",
                },
            ],
        )

    def test_delete_on_manager_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            User.objects.order_by("pk").update(is_active=False)
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_1.pk)}, {"id": str(user_2.pk)}])

    def test_delete_on_manager_delete(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            User.objects.order_by("pk").delete()
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_1.pk)}, {"id": str(user_2.pk)}])

    def test_sync_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user_1.first_name = "John"
            user_2.first_name = "Not John"
            User.objects.bulk_update([user_1, user_2], ["first_name"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "POST"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(
            call,
            [
                {
                    "id": str(user_1.pk),
                    "kind": "",
                    "first_name": "John",
                    "last_name": user_1.last_name,
                    "email": user_1.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "PRO_CONNECT",
                },
                {
                    "id": str(user_2.pk),
                    "kind": "",
                    "first_name": "Not John",
                    "last_name": user_2.last_name,
                    "email": user_2.email,
                    "phone": "",
                    "last_login": None,
                    "auth": "PRO_CONNECT",
                },
            ],
        )

    def test_delete_on_manager_bulk_update(self, db, django_capture_on_commit_callbacks, mock_nexus_api):
        user_1 = UserFactory()
        user_2 = UserFactory()

        with django_capture_on_commit_callbacks(execute=True):
            user_1.is_active = False
            user_2.is_active = False
            User.objects.bulk_update([user_1, user_2], ["is_active"])
        [call] = mock_nexus_api.calls
        assert call.request.method == "DELETE"
        assert call.request.url == "http://nexus/api/users"
        assert_call_content(call, [{"id": str(user_1.pk)}, {"id": str(user_2.pk)}])
