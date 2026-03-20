import pytest
from django.conf import settings
from django.test import RequestFactory, TestCase
from django.urls import reverse
from faker import Faker
from itoutils.urls import add_url_params
from machina.core.db.models import get_model
from machina.core.loading import get_class
from pytest_django.asserts import assertRedirects

from lacommunaute.forum_conversation.forms import PostForm
from lacommunaute.forum_conversation.models import CertifiedPost, Topic
from lacommunaute.forum_conversation.views_htmx import PostListView
from lacommunaute.users.enums import EmailLastSeenKind
from lacommunaute.users.models import EmailLastSeen
from tests.forum_conversation.factories import CertifiedPostFactory, PostFactory, TopicFactory
from tests.forum_upvote.factories import UpVoteFactory
from tests.notification.factories import NotificationFactory
from tests.users.factories import UserFactory


faker = Faker(settings.LANGUAGE_CODE)

TopicReadTrack = get_model("forum_tracking", "TopicReadTrack")
ForumReadTrack = get_model("forum_tracking", "ForumReadTrack")
PermissionHandler = get_class("forum_permission.handler", "PermissionHandler")


class TopicContentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = TopicFactory()
        cls.user = cls.topic.poster
        cls.url = reverse(
            "forum_conversation_extension:showmore_topic",
            kwargs={
                "forum_pk": cls.topic.forum.pk,
                "forum_slug": cls.topic.forum.slug,
                "pk": cls.topic.pk,
                "slug": cls.topic.slug,
            },
        )

    def test_topic_doesnt_exist(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "forum_conversation_extension:showmore_posts",
                kwargs={
                    "forum_pk": self.topic.forum.pk,
                    "forum_slug": self.topic.forum.slug,
                    "pk": self.topic.pk + 1,
                    "slug": self.topic.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_topic_content(self):
        post = PostFactory(topic=self.topic, poster=self.user)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertContains(response, post.content, status_code=200)
        self.assertEqual(1, ForumReadTrack.objects.count())


class TopicCertifiedPostViewTest(TestCase):
    def test_get_topic_certified_post(self):
        topic = TopicFactory(with_certified_post=True)
        user = topic.poster
        url = reverse(
            "forum_conversation_extension:showmore_certified",
            kwargs={
                "forum_pk": topic.forum.pk,
                "forum_slug": topic.forum.slug,
                "pk": topic.pk,
                "slug": topic.slug,
            },
        )
        self.client.force_login(user)

        response = self.client.get(url)

        self.assertContains(response, topic.certified_post.post.content, status_code=200)
        self.assertEqual(1, ForumReadTrack.objects.count())


class PostListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = TopicFactory(with_post=True)
        cls.user = cls.topic.poster
        cls.kwargs = {
            "forum_pk": cls.topic.forum.pk,
            "forum_slug": cls.topic.forum.slug,
            "pk": cls.topic.pk,
            "slug": cls.topic.slug,
        }
        cls.url = reverse(
            "forum_conversation_extension:showmore_posts",
            kwargs=cls.kwargs,
        )

    def test_topic_doesnt_exist(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "forum_conversation_extension:showmore_posts",
                kwargs={
                    "forum_pk": self.topic.forum.pk,
                    "forum_slug": self.topic.forum.slug,
                    "pk": self.topic.pk + 1,
                    "slug": self.topic.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_list_of_posts(self):
        posts = PostFactory.create_batch(2, topic=self.topic, poster=self.user)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertNotContains(
            response, self.topic.first_post.content, status_code=200
        )  # original post content excluded
        self.assertContains(response, posts[0].content)
        self.assertContains(response, posts[1].content)
        self.assertContains(response, posts[0].poster_display_name)
        self.assertIsInstance(response.context["form"], PostForm)
        self.assertEqual(1, ForumReadTrack.objects.count())
        self.assertEqual(response.context["next_url"], self.topic.get_absolute_url())

    def test_get_list_of_posts_posted_by_anonymous_user(self):
        username = faker.email()
        post = PostFactory(topic=self.topic, poster=None, username=username)
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertContains(response, post.poster_display_name, status_code=200)

    def test_get_list_of_posts_linked_to_annonce_topic(self):
        post = PostFactory(topic=self.topic, poster=self.user)
        self.topic.type = Topic.TOPIC_ANNOUNCE
        self.topic.save()

        request = RequestFactory().get(self.url)
        request.user = self.user
        request.forum_permission_handler = PermissionHandler()

        view = PostListView()
        view.request = request
        view.kwargs = self.kwargs

        response = view.get(request)
        self.assertNotContains(
            response, self.topic.first_post.content, status_code=200
        )  # original post content excluded
        self.assertContains(response, post.content)

    def test_upvote_annotations(self):
        post = PostFactory(topic=self.topic, poster=self.user)

        request = RequestFactory().get(self.url)
        request.user = self.user
        request.forum_permission_handler = PermissionHandler()

        view = PostListView()
        view.request = request
        view.kwargs = self.kwargs

        response = view.get(request)
        self.assertContains(
            response, '<i class="ri-notification-2-line me-1" aria-hidden="true"></i><span>0</span>', status_code=200
        )

        UpVoteFactory(content_object=post, voter=UserFactory())
        UpVoteFactory(content_object=post, voter=self.user)

        response = view.get(request)
        self.assertContains(
            response, '<i class="ri-notification-2-fill me-1" aria-hidden="true"></i><span>2</span>', status_code=200
        )

    def test_certified_post_highlight(self):
        post = PostFactory(topic=self.topic, poster=self.user)
        self.client.force_login(self.user)

        response = self.client.get(self.url)
        self.assertNotContains(response, "Certifié par la Plateforme de l'Inclusion", status_code=200)

        CertifiedPostFactory(topic=self.topic, post=post, user=self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Certifié par la Plateforme de l'Inclusion", status_code=200)

    def test_get_marks_notifications_read(self):
        self.client.force_login(self.user)

        notification = NotificationFactory(recipient=self.user.email, post=self.topic.first_post)
        self.assertIsNone(notification.sent_at)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        notification.refresh_from_db()
        self.assertEqual(str(notification.created), str(notification.sent_at))


class PostFeedCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = TopicFactory(with_post=True)
        cls.user = cls.topic.poster
        cls.url = reverse(
            "forum_conversation_extension:post_create",
            kwargs={
                "forum_pk": cls.topic.forum.pk,
                "forum_slug": cls.topic.forum.slug,
                "pk": cls.topic.pk,
                "slug": cls.topic.slug,
            },
        )
        cls.content = faker.paragraph(nb_sentences=5)

    def test_get_method_unallowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_topic_doesnt_exist(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "forum_conversation_extension:post_create",
                kwargs={
                    "forum_pk": self.topic.forum.pk,
                    "forum_slug": self.topic.forum.slug,
                    "pk": self.topic.pk + 1,
                    "slug": self.topic.slug,
                },
            ),
            data={},
        )

        self.assertEqual(response.status_code, 404)

    def test_create_post_as_authenticated_user_forbidden(self, *args):
        self.client.force_login(self.user)

        response = self.client.post(self.url, data={"content": self.content})
        assert response.status_code == 403

        self.topic.refresh_from_db()
        assert self.topic.posts.count() == 1


class TestPostFeedCreateView:
    @pytest.mark.parametrize("logged", [True, False])
    def test_email_last_seen_is_updated_forbidden(self, client, db, logged):
        topic = TopicFactory(with_post=True)
        url = reverse(
            "forum_conversation_extension:post_create",
            kwargs={
                "forum_pk": topic.forum.pk,
                "forum_slug": topic.forum.slug,
                "pk": topic.pk,
                "slug": topic.slug,
            },
        )
        data = {"content": faker.paragraph(nb_sentences=5)}

        if logged:
            client.force_login(topic.poster)
        else:
            data["username"] = "bobby@lapointe.fr"

        response = client.post(url, data=data)
        if logged:
            assert response.status_code == 403
        else:
            assertRedirects(response, add_url_params(reverse("users:login"), {"next": url}))

        email = topic.poster.email if logged else data["username"]
        assert not EmailLastSeen.objects.filter(email=email, last_seen_kind=EmailLastSeenKind.POST).exists()


# vincentporte : not to futur self, rewrite it in pytest style
class CertifiedPostViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = TopicFactory(with_post=True)
        cls.user = cls.topic.poster
        cls.url = reverse(
            "forum_conversation_extension:certify",
            kwargs={
                "forum_pk": cls.topic.forum.pk,
                "forum_slug": cls.topic.forum.slug,
                "pk": cls.topic.pk,
                "slug": cls.topic.slug,
            },
        )
        cls.form_data = {"post_pk": cls.topic.last_post.pk}

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_post_instance_doesnt_exist(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={"post_pk": 9999})
        self.assertEqual(response.status_code, 404)

    def test_certify_without_permission(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)
        self.assertEqual(response.status_code, 403)

    def test_certify_with_permission(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CertifiedPost.objects.count(), 1)
        certified_post = CertifiedPost.objects.first()
        self.assertEqual(certified_post.post, self.topic.last_post)
        self.assertEqual(certified_post.user, self.user)
        self.assertEqual(certified_post.topic, self.topic)
        self.assertEqual(ForumReadTrack.objects.count(), 1)

    def test_uncertify_with_permission(self):
        self.user.is_staff = True
        self.user.save()
        CertifiedPost(topic=self.topic, post=self.topic.last_post, user=self.user).save()
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CertifiedPost.objects.count(), 0)
        self.assertEqual(ForumReadTrack.objects.count(), 1)

    def test_rendered_content(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=self.form_data)

        self.assertContains(response, f'<div id="showmorepostsarea{self.topic.pk}">', status_code=200)
        self.assertTemplateUsed(response, "forum_conversation/partials/posts_list.html")
