from django.contrib.admin import helpers
from django.urls import reverse
from pytest_django.asserts import assertContains

from lacommunaute.forum_conversation.factories import AnonymousPostFactory, PostFactory, TopicFactory
from lacommunaute.forum_conversation.models import Post
from lacommunaute.forum_moderation.models import BlockedDomainName, BlockedEmail


def test_delete_message_and_block_email(db, admin_client):
    # detected spam
    post = PostFactory(poster__email="1@mailinator.com", topic=TopicFactory())
    other_post = PostFactory(poster=post.poster, topic=TopicFactory())
    anonymous_post = AnonymousPostFactory(username="2@mailinator.com", topic=TopicFactory())
    # valid posts
    PostFactory(topic=TopicFactory())
    AnonymousPostFactory(topic=TopicFactory())

    # Check it doesn't crash if the email is already blocked
    BlockedEmail.objects.create(email="1@mailinator.com")

    response = admin_client.post(
        reverse("admin:forum_conversation_post_changelist"),
        {
            "action": "delete_message_and_block_email",
            helpers.ACTION_CHECKBOX_NAME: [post.pk, other_post.pk, anonymous_post.pk],
        },
        follow=True,
    )
    assertContains(response, "Messages supprimés et emails bloqués 👍", html=True)

    assert Post.objects.count() == 2
    assert sorted(BlockedEmail.objects.values_list("email", flat=True)) == [
        "1@mailinator.com",
        "2@mailinator.com",
    ]


def test_delete_message_and_block_domain_name(db, admin_client):
    # detected spam
    post = PostFactory(poster__email="1@evil_domain.com", topic=TopicFactory())
    other_post = PostFactory(poster__email="2@evil_domain.com", topic=TopicFactory())
    anonymous_post = AnonymousPostFactory(username="3@very_evil_domain.com", topic=TopicFactory())
    # valid posts
    PostFactory(topic=TopicFactory())
    AnonymousPostFactory(topic=TopicFactory())

    # Check it doesn't crash if the domain is already blocked
    BlockedDomainName.objects.create(domain="evil_domain.com")

    response = admin_client.post(
        reverse("admin:forum_conversation_post_changelist"),
        {
            "action": "delete_message_and_block_domain_name",
            helpers.ACTION_CHECKBOX_NAME: [post.pk, other_post.pk, anonymous_post.pk],
        },
        follow=True,
    )
    assertContains(response, "Messages supprimés et noms de domaine bloqués 👍", html=True)

    assert Post.objects.count() == 2
    assert sorted(BlockedDomainName.objects.values_list("domain", flat=True)) == [
        "evil_domain.com",
        "very_evil_domain.com",
    ]
