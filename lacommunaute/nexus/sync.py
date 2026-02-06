import logging

from django.conf import settings
from itoutils.django.nexus.api import NexusAPIClient, NexusAPIException

from lacommunaute.users.enums import IdentityProvider


logger = logging.getLogger(__name__)


USER_TRACKED_FIELDS = [
    "id",
    "first_name",
    "last_name",
    "email",
    "last_login",
    "identity_provider",
    "is_active",
    "is_staff",
]


def serialize_user(user):
    return {
        "id": str(user.pk),
        "kind": "",
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": "",
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "auth": {
            IdentityProvider.MAGIC_LINK: "MAGIC_LINK",
            IdentityProvider.INCLUSION_CONNECT: "INCLUSION_CONNECT",
            IdentityProvider.PRO_CONNECT: "PRO_CONNECT",
        }[user.identity_provider],
    }


def sync_users(users):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().send_users([serialize_user(user) for user in users])
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to sync user")


def delete_users(user_pks):
    if settings.NEXUS_API_BASE_URL:
        try:
            NexusAPIClient().delete_users(user_pks)
        except NexusAPIException:
            pass  # The client already logged the error, we don't want to crash if we can't connect to Nexus
        except Exception:
            logger.exception("Nexus: failed to delete user")
