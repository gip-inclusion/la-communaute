from django.contrib.admin import helpers
from django.urls import reverse
from pytest_django.asserts import assertContains, assertQuerySetEqual

from lacommunaute.forum_conversation.factories import (
    AnonymousPostFactory,
    AnonymousTopicFactory,
    PostFactory,
    TopicFactory,
)
from lacommunaute.forum_conversation.models import Post, Topic
from lacommunaute.forum_moderation.models import BlockedDomainName, BlockedEmail


def test_delete_message_and_block_email(db, admin_client):
    valid_post_1 = PostFactory(topic=TopicFactory())
    valid_post_2 = AnonymousPostFactory(topic=TopicFactory())
    # detected spam
    post = PostFactory(poster__email="1@mailinator.com", topic=valid_post_1.topic)
    other_post = PostFactory(poster=post.poster, topic=TopicFactory())
    anonymous_post = AnonymousPostFactory(username="2@mailinator.com", topic=TopicFactory())

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

    assertQuerySetEqual(Post.objects.all(), [valid_post_1, valid_post_2])
    assertQuerySetEqual(Topic.objects.all(), [valid_post_1.topic, valid_post_2.topic])
    assert sorted(BlockedEmail.objects.values_list("email", flat=True)) == [
        "1@mailinator.com",
        "2@mailinator.com",
    ]


def test_delete_message_and_block_domain_name(db, admin_client):
    valid_post_1 = PostFactory(topic=TopicFactory())
    valid_post_2 = AnonymousPostFactory(topic=TopicFactory())
    # detected spam
    post = PostFactory(poster__email="1@evil_domain.com", topic=valid_post_1.topic)
    other_post = PostFactory(poster__email="2@evil_domain.com", topic=TopicFactory())
    anonymous_post = AnonymousPostFactory(username="3@very_evil_domain.com", topic=TopicFactory())

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

    assertQuerySetEqual(Post.objects.all(), [valid_post_1, valid_post_2])
    assertQuerySetEqual(Topic.objects.all(), [valid_post_1.topic, valid_post_2.topic])
    assert sorted(BlockedDomainName.objects.values_list("domain", flat=True)) == [
        "evil_domain.com",
        "very_evil_domain.com",
    ]


def test_delete_topic_and_block_author_email(db, admin_client):
    valid_topic_1 = TopicFactory()
    valid_topic_2 = AnonymousTopicFactory()
    # detected spam
    topic = TopicFactory()
    post = PostFactory(poster__email="1@mailinator.com", topic=topic)
    other_topic = TopicFactory()
    PostFactory(poster=post.poster, topic=other_topic)
    anonymous_topic = AnonymousTopicFactory()
    AnonymousPostFactory(username="2@mailinator.com", topic=anonymous_topic)

    # # Check it doesn't crash if the email is already blocked
    BlockedEmail.objects.create(email="1@mailinator.com")

    response = admin_client.post(
        reverse("admin:forum_conversation_topic_changelist"),
        {
            "action": "delete_topic_and_block_author_email",
            helpers.ACTION_CHECKBOX_NAME: [topic.pk, other_topic.pk, anonymous_topic.pk],
        },
        follow=True,
    )
    assertContains(response, "Sujets supprimés et emails bloqués 👍", html=True)

    assertQuerySetEqual(Topic.objects.all(), [valid_topic_1, valid_topic_2])
    assertQuerySetEqual(Post.objects.all(), [])
    assert sorted(BlockedEmail.objects.values_list("email", flat=True)) == [
        "1@mailinator.com",
        "2@mailinator.com",
    ]


def test_delete_topic_and_block_author_domain_name(db, admin_client):
    valid_topic_1 = TopicFactory()
    valid_topic_2 = AnonymousTopicFactory()
    # detected spam
    topic = TopicFactory()
    PostFactory(poster__email="1@evil_domain.com", topic=topic)
    other_topic = TopicFactory()
    PostFactory(poster__email="2@evil_domain.com", topic=other_topic)
    anonymous_topic = AnonymousTopicFactory()
    AnonymousPostFactory(username="3@very_evil_domain.com", topic=anonymous_topic)

    # Check it doesn't crash if the domain is already blocked
    BlockedDomainName.objects.create(domain="evil_domain.com")

    response = admin_client.post(
        reverse("admin:forum_conversation_topic_changelist"),
        {
            "action": "delete_topic_and_block_author_domain_name",
            helpers.ACTION_CHECKBOX_NAME: [topic.pk, other_topic.pk, anonymous_topic.pk],
        },
        follow=True,
    )
    assertContains(response, "Sujets supprimés et noms de domaine bloqués 👍", html=True)

    assertQuerySetEqual(Topic.objects.all(), [valid_topic_1, valid_topic_2])
    assertQuerySetEqual(Post.objects.all(), [])
    assert sorted(BlockedDomainName.objects.values_list("domain", flat=True)) == [
        "evil_domain.com",
        "very_evil_domain.com",
    ]
