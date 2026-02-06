from itoutils.django.nexus.management.base_full_sync import BaseNexusFullSyncCommand

from lacommunaute.nexus.sync import serialize_user
from lacommunaute.users.models import User


class Command(BaseNexusFullSyncCommand):
    user_serializer = staticmethod(serialize_user)

    def sync_memberships(self):
        pass  # No structure here

    def sync_structures(self):
        pass  # No structure here

    def get_users_queryset(self):
        return User.objects.filter(is_active=True).exclude(email="").exclude(is_staff=True)
