import hashlib

import pytest
from django.conf import settings
from itoutils.django.testing import assertSnapshotQueries

from lacommunaute.users.models import EmailLastSeen
from lacommunaute.users.utils import soft_delete_users
from tests.forum_conversation.factories import AnonymousTopicFactory, TopicFactory
from tests.users.factories import EmailLastSeenFactory, UserFactory


@pytest.fixture(name="soft_deletable_email_last_seen")
def fixture_soft_deletable_email_last_seen(db):
    return


def test_soft_delete(db):
    email_last_seen = EmailLastSeenFactory(soft_deletable=True)
    expected_hash = hashlib.sha256(
        f"{email_last_seen.email}-{settings.EMAIL_LAST_SEEN_HASH_SALT}".encode("utf-8")
    ).hexdigest()

    soft_delete_users([email_last_seen])

    email_last_seen.refresh_from_db()
    assert email_last_seen.deleted_at is not None
    assert email_last_seen.email == f"email-anonymise-{email_last_seen.pk}@{settings.COMMU_FQDN}"
    assert email_last_seen.email_hash == expected_hash


def test_soft_delete_user(db):
    user = UserFactory()
    email_last_seen = EmailLastSeenFactory(email=user.email, soft_deletable=True)

    undesired_user = UserFactory()
    undesired_user_email = undesired_user.email
    undesired_user_first_name = undesired_user.first_name
    undesired_user_last_name = undesired_user.last_name

    soft_delete_users([email_last_seen])

    user.refresh_from_db()
    assert user.email == f"email-anonymise-{email_last_seen.pk}@{settings.COMMU_FQDN}"
    assert user.first_name == "Anonyme"
    assert user.last_name == "Anonyme"

    undesired_user.refresh_from_db()
    assert undesired_user.email == undesired_user_email
    assert undesired_user.first_name == undesired_user_first_name
    assert undesired_user.last_name == undesired_user_last_name


def test_soft_delete_post(db):
    anonymous_post = AnonymousTopicFactory(with_post=True).first_post
    email_last_seen = EmailLastSeen.objects.get()

    undesired_posts = [AnonymousTopicFactory(with_post=True).first_post, TopicFactory(with_post=True).first_post]
    undesired_usernames = [post.username for post in undesired_posts]

    soft_delete_users([email_last_seen])

    anonymous_post.refresh_from_db()
    assert anonymous_post.username == f"email-anonymise-{email_last_seen.pk}@{settings.COMMU_FQDN}"

    for post in undesired_posts:
        post.refresh_from_db()
        assert post.username in undesired_usernames


def test_soft_delete_queries(db, snapshot):
    AnonymousTopicFactory.create_batch(3, with_post=True)

    users = UserFactory.create_batch(3)
    for user in users:
        EmailLastSeenFactory(email=user.email, soft_deletable=True)

    with assertSnapshotQueries(snapshot):
        soft_delete_users(EmailLastSeen.objects.all())
