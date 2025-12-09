import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission

from lacommunaute.users.admin import EmailLastSeenAdmin
from lacommunaute.users.apps import sync_groups_and_perms
from lacommunaute.users.models import EmailLastSeen


def test_permissions_on_email_last_seen(db):
    email_last_seen_admin = EmailLastSeenAdmin(EmailLastSeen, AdminSite())
    assert not email_last_seen_admin.has_add_permission(None)
    assert not email_last_seen_admin.has_change_permission(None)
    assert not email_last_seen_admin.has_delete_permission(None)


@pytest.mark.usefixtures("db")
class TestSyncGroupAndPerms:
    def test_readonly_group_permissions(self):
        ro_group = Group.objects.get(name="readonly")
        assert all(
            perm_codename.startswith("view_")
            for perm_codename in ro_group.permissions.values_list("codename", flat=True)
        )

    def test_clears_existing_permissions(self):
        ro_group = Group.objects.get(name="readonly")
        p = Permission.objects.get(codename="add_forum")
        ro_group.permissions.add(p)
        sync_groups_and_perms()
        assert p not in ro_group.permissions.all()
