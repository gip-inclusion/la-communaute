import itertools
import logging

from django.apps import AppConfig
from django.db.models.base import transaction
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)

PERMS_READ = {"view"}


class UserConfig(AppConfig):
    name = "lacommunaute.users"

    def ready(self):
        post_migrate.connect(sync_groups_and_perms, sender=self)


def group_perms():
    from django.contrib.flatpages import models as flatpages_models
    from django.contrib.redirects import models as redirects_models
    from machina.core.db.models import get_model
    from taggit import models as tags

    from lacommunaute.event import models as event_models
    from lacommunaute.forum import models as forum_models
    from lacommunaute.forum_conversation import models as forum_conversation_models
    from lacommunaute.forum_member import models as forum_member_models
    from lacommunaute.forum_moderation import models as forum_moderation_models
    from lacommunaute.partner import models as partner_models
    from lacommunaute.surveys import models as surveys_models
    from lacommunaute.users import models as user_models

    return {
        "readonly": {
            event_models.Event: PERMS_READ,
            flatpages_models.FlatPage: PERMS_READ,
            forum_conversation_models.CertifiedPost: PERMS_READ,
            forum_conversation_models.Post: PERMS_READ,
            forum_conversation_models.Topic: PERMS_READ,
            forum_member_models.ForumProfile: PERMS_READ,
            forum_moderation_models.BlockedEmail: PERMS_READ,
            forum_moderation_models.BlockedDomainName: PERMS_READ,
            forum_moderation_models.BlockedPost: PERMS_READ,
            get_model("forum_polls", "TopicPoll"): PERMS_READ,
            forum_models.Forum: PERMS_READ,
            partner_models.Partner: PERMS_READ,
            redirects_models.Redirect: PERMS_READ,
            surveys_models.DSP: PERMS_READ,
            surveys_models.Recommendation: PERMS_READ,
            tags.Tag: PERMS_READ,
            user_models.User: PERMS_READ,
        },
    }


def to_perm_codenames(model, perms_set):
    return [f"{perm}_{model._meta.model_name}" for perm in perms_set]


def sync_groups_and_perms(**kwargs):
    from django.contrib.auth.models import Group, Permission

    for group_name, raw_permissions in group_perms().items():
        with transaction.atomic():
            group, created = Group.objects.select_for_update(of=["self"]).get_or_create(name=group_name)
            if created:
                logger.info(f"Created group “{group_name}”")
            existing_permissions = set(group.permissions.all())
            all_codenames = itertools.chain.from_iterable(
                to_perm_codenames(model, perms) for model, perms in raw_permissions.items()
            )
            spec_permissions = set(Permission.objects.filter(codename__in=all_codenames))
            perms_to_add = spec_permissions - existing_permissions
            perms_to_remove = existing_permissions - spec_permissions
            for permission in perms_to_add:
                group.permissions.add(permission)
                logger.info(f"Added permission {permission.codename} to group “{group_name}”")
            for permission in perms_to_remove:
                group.permissions.remove(permission)
                logger.info(f"Removed permission {permission.codename} from group “{group_name}”")
