from django.urls import reverse
from pytest_django.asserts import assertContains

from tests.forum_conversation.factories import AnonymousPostFactory, TopicFactory


def test_detail_view_for_anonymous_post(db, admin_client):
    post = AnonymousPostFactory(topic=TopicFactory(approved=False), approved=False)
    response = admin_client.get(reverse("forum_moderation:queued_post", kwargs={"pk": post.pk}))
    assertContains(response, post.poster_display_name)
    assertContains(response, post.topic.subject)


def test_detail_view_with_authenticated_post(db, admin_client):
    topic = TopicFactory(approved=False, with_post=True)
    response = admin_client.get(reverse("forum_moderation:queued_post", kwargs={"pk": topic.first_post.pk}))
    assertContains(response, topic.subject)
    assertContains(response, topic.first_post.poster_display_name)
