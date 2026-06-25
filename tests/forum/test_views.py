import pytest
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import truncatechars_html
from django.test import RequestFactory, TestCase
from django.urls import reverse
from faker import Faker
from itoutils.django.testing import assertSnapshotQueries
from machina.core.loading import get_class
from pytest_django.asserts import assertContains
from taggit.models import Tag

from lacommunaute.forum.models import Forum
from lacommunaute.forum.views import ForumView
from lacommunaute.forum_conversation.enums import Filters
from lacommunaute.forum_conversation.forms import PostForm
from lacommunaute.forum_conversation.models import Topic
from tests.forum.factories import CategoryForumFactory, ForumFactory
from tests.forum_conversation.factories import CertifiedPostFactory, PostFactory, TopicFactory
from tests.testing import parse_response_to_soup, reset_model_sequence_fixture
from tests.users.factories import UserFactory


faker = Faker()

PermissionHandler = get_class("forum_permission.handler", "PermissionHandler")
remove_perm = get_class("forum_permission.shortcuts", "remove_perm")


class ForumViewQuerysetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.forum = ForumFactory()
        cls.view = ForumView()
        cls.view.kwargs = {"pk": cls.forum.pk}
        cls.view.request = RequestFactory().get("/")
        cls.view.request.user = cls.user

    def test_exclude_not_approved_posts(self):
        TopicFactory(forum=self.forum, poster=self.user, approved=False)
        self.assertFalse(self.view.get_queryset())

    def test_ordering_topics_on_last_post(self):
        old_topic = TopicFactory(forum=self.forum, poster=self.user)
        new_topic = TopicFactory(forum=self.forum, poster=self.user)

        PostFactory(topic=old_topic, poster=self.user)
        PostFactory(topic=new_topic, poster=self.user)

        qs = self.view.get_queryset()
        self.assertEqual(qs.first(), new_topic)
        self.assertEqual(qs.last(), old_topic)

        PostFactory(topic=old_topic, poster=self.user)
        self.assertEqual(qs.first(), old_topic)
        self.assertEqual(qs.last(), new_topic)

    def test_pagination(self):
        self.assertEqual(10, self.view.paginate_by)


@pytest.mark.usefixtures("unittest_compatibility")
class ForumViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.topic = TopicFactory(with_post=True)
        cls.forum = cls.topic.forum
        cls.user = cls.topic.poster
        cls.forum = cls.topic.forum

        cls.url = reverse("forum_extension:forum", kwargs={"pk": cls.forum.pk, "slug": cls.forum.slug})

    def test_context(self):
        response = self.client.get(self.url)

        loadmoretopic_url = reverse("forum_extension:forum", kwargs={"pk": self.forum.pk, "slug": self.forum.slug})

        self.assertIsInstance(response.context_data["form"], PostForm)
        self.assertEqual(response.context_data["filters"], Filters.choices)
        self.assertEqual(response.context_data["loadmoretopic_url"], loadmoretopic_url)
        self.assertEqual(response.context_data["forum"], self.forum)
        self.assertIsNone(response.context_data["rating"])
        self.assertEqual(response.context_data["active_filter"], Filters.ALL)
        self.assertEqual(list(response.context_data["active_tag"]), [])

        for filter in Filters:
            with self.subTest(filter=filter):
                response = self.client.get(self.url + f"?filter={filter.value}")
                self.assertEqual(
                    response.context_data["loadmoretopic_url"],
                    loadmoretopic_url + f"?filter={filter.value}",
                )
                self.assertEqual(response.context_data["active_filter"], filter)

        response = self.client.get(self.url + "?filter=FAKE")
        self.assertEqual(response.context_data["active_filter"], Filters.ALL)

        tag = Tag.objects.create(name="tag_1", slug="tag_1")
        response = self.client.get(self.url + f"?tag={tag.name}")
        self.assertEqual(tag, response.context_data["active_tag"])

    def test_template_name(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "forum/forum_detail.html")

        response = self.client.get(self.url, **{"HTTP_HX_REQUEST": "true"})
        self.assertTemplateUsed(response, "forum_conversation/topic_list.html")

    def test_show_comments(self):
        topic_url = reverse(
            "forum_conversation_extension:showmore_posts",
            kwargs={
                "forum_pk": self.forum.pk,
                "forum_slug": self.forum.slug,
                "pk": self.topic.pk,
                "slug": self.topic.slug,
            },
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertNotContains(response, f'<a href="{topic_url}"', status_code=200)

        PostFactory.create_batch(2, topic=self.topic, poster=self.user)
        response = self.client.get(self.url)

        self.assertContains(response, f'hx-get="{topic_url}"', status_code=200)
        self.assertContains(response, "Voir les 2 réponses")

    def test_show_more_content(self):
        topic = TopicFactory(
            with_post=True, poster=self.user, forum=self.forum, post__content=faker.paragraph(nb_sentences=100)
        )
        topic_url = reverse(
            "forum_conversation_extension:showmore_topic",
            kwargs={
                "forum_pk": topic.forum.pk,
                "forum_slug": topic.forum.slug,
                "pk": topic.pk,
                "slug": topic.slug,
            },
        )
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertContains(response, f'hx-get="{topic_url}"', status_code=200)
        self.assertContains(response, "+ voir la suite")
        self.assertEqual(response.context_data["loadmoretopic_suffix"], "topicsinforum")

    def test_poll_form(self):
        topic = TopicFactory(forum=self.forum, poster=self.user, with_post=True, with_poll_vote=True)
        poll_option = topic.poll.options.first()
        self.client.force_login(self.user)

        response = self.client.get(self.url)
        self.assertContains(response, poll_option.poll.question, status_code=200)
        self.assertContains(response, poll_option.text)

    def test_cannot_submit_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertIsInstance(response.context_data["form"], PostForm)
        self.assertNotContains(response, f'id="collapsePost{self.topic.pk}', status_code=200)

    def test_cannot_submit_post(self, *args):
        user = UserFactory()
        forum = ForumFactory()
        remove_perm("can_reply_to_topics", user, self.forum)
        url = reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug})
        self.client.force_login(user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f'id="collapsePost{self.topic.pk}')

    def test_queries(self):
        ContentType.objects.clear_cache()

        TopicFactory.create_batch(20, with_post=True)
        self.client.force_login(self.user)
        with assertSnapshotQueries(self.snapshot):
            self.client.get(self.url)

    def test_certified_post_display(self):
        topic_certified_post_url = reverse(
            "forum_conversation_extension:showmore_certified",
            kwargs={
                "forum_pk": self.forum.pk,
                "forum_slug": self.forum.slug,
                "pk": self.topic.pk,
                "slug": self.topic.slug,
            },
        )
        self.client.force_login(self.user)

        # create a post which is not certified
        post = PostFactory(topic=self.topic, poster=self.user, content=faker.paragraph(nb_sentences=100))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, truncatechars_html(post.content.rendered, 200))
        self.assertNotContains(response, topic_certified_post_url)
        self.assertNotContains(response, "Certifié par la Plateforme de l'Inclusion")

        # certify post
        CertifiedPostFactory(topic=self.topic, post=post, user=self.user)

        response = self.client.get(self.url)

        self.assertContains(response, truncatechars_html(post.content.rendered, 200), status_code=200)
        self.assertContains(response, topic_certified_post_url)
        self.assertContains(response, "Certifié par la Plateforme de l'Inclusion")

    def test_loadmoretopic_url(self):
        loadmoretopic_url = reverse(
            "forum_extension:forum",
            kwargs={"pk": self.forum.pk, "slug": self.forum.slug},
        )

        TopicFactory.create_batch(9, with_post=True, forum=self.forum)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["loadmoretopic_url"], loadmoretopic_url)

        self.assertNotContains(response, loadmoretopic_url + "?page=2")

        TopicFactory(with_post=True, forum=self.forum)
        response = self.client.get(self.url)
        self.assertContains(response, loadmoretopic_url + "?page=2", status_code=200)

        TopicFactory.create_batch(10, with_post=True, forum=self.forum)
        response = self.client.get(self.url + "?page=2")
        self.assertContains(response, loadmoretopic_url + "?page=3", status_code=200)

    def test_topic_has_tags(self):
        tag = f"tag_{faker.word()}"
        self.client.force_login(self.user)

        response = self.client.get(self.url)
        self.assertNotContains(response, tag, status_code=200)

        self.topic.tags.add(tag)
        response = self.client.get(self.url)
        self.assertContains(response, tag, status_code=200)

    def test_description_is_markdown_rendered(self):
        self.forum.description = "# title"
        self.forum.save()
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertContains(response, "<h1>title</h1>", status_code=200)

    def test_next_url_in_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["next_url"], self.url)

    def test_can_view_update_forum_link(self):
        url = reverse("forum_extension:edit_forum", kwargs={"pk": self.forum.pk, "slug": self.forum.slug})
        response = self.client.get(self.url)
        self.assertNotContains(response, url)

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertNotContains(response, url)

        self.user.is_staff = True

        self.user.save()
        response = self.client.get(self.url)
        self.assertContains(response, url)

    def test_filtered_queryset_on_tag(self):
        tag = faker.word()
        topic = TopicFactory(forum=self.forum, with_tags=[tag], with_post=True)

        with assertSnapshotQueries(self.snapshot):
            response = self.client.get(
                reverse("forum_extension:forum", kwargs={"pk": self.forum.pk, "slug": self.forum.slug}), {"tag": tag}
            )
        self.assertContains(response, topic.subject)
        self.assertNotContains(response, self.topic.subject)

    def test_queryset_for_unanswered_topics(self):
        PostFactory(topic=self.topic)
        response = self.client.get(self.url + f"?filter={Filters.NEW.value}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["paginator"].count, 0)
        self.assertEqual(response.context_data["active_filter"], Filters.NEW)

        new_topic = TopicFactory(with_post=True, forum=self.forum)

        response = self.client.get(self.url + f"?filter={Filters.NEW.value}")
        self.assertEqual(response.context_data["paginator"].count, 1)
        self.assertContains(response, new_topic.subject, status_code=200)
        self.assertEqual(response.context_data["active_filter"], Filters.NEW)

        for topic in Topic.objects.exclude(id=new_topic.id):
            with self.subTest(topic):
                self.assertNotContains(response, topic.subject)

    def test_banner_display_on_subcategory_forum(self):
        category_forum = CategoryForumFactory(with_child=True)
        forum = category_forum.get_children().first()
        response = self.client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        self.assertContains(response, forum.image.url.split("=")[0])


reset_forum_sequence = pytest.fixture(reset_model_sequence_fixture(Forum))


class TestForumViewContent:
    def test_opengraph_for_forum_with_image(self, client, db):
        forum = ForumFactory(with_image=True)
        response = client.get(forum.get_absolute_url())
        assertContains(
            response,
            f'<meta property="og:image" content="{settings.MEDIA_URL}{settings.AWS_STORAGE_BUCKET_NAME}/banner',
        )
        assertContains(
            response,
            f'<meta property="twitter:image" content="{settings.MEDIA_URL}{settings.AWS_STORAGE_BUCKET_NAME}/banner',
        )

    def test_opengraph_for_forum_wo_image(self, client, db):
        forum = ForumFactory()
        response = client.get(forum.get_absolute_url())
        assertContains(response, '<meta property="og:image" content="/static/images/logo-og-communaute')
        assertContains(response, '<meta property="og:image" content="/static/images/logo-og-communaute')


@pytest.fixture(name="forum_for_snapshot")
def forum_for_snapshot_fixture():
    return ForumFactory(
        parent=ForumFactory(name="Parent-Forum"),
        with_image=True,
        for_snapshot=True,
    )


@pytest.fixture(name="documentation_forum")
def documentation_forum_fixture():
    return ForumFactory(
        parent=CategoryForumFactory(name="Parent-Forum"),
        with_image=True,
        for_snapshot=True,
    )


class TestForumDetailContent:
    def test_template_forum_detail_share_actions(self, client, db, snapshot):
        forum = ForumFactory()
        response = client.get(forum.get_absolute_url())
        content = parse_response_to_soup(response, replace_in_href=[forum])

        assert len(content.select(f"#upvotesarea{str(forum.pk)}")) == 0
        assert len(content.select(f"#dropdownMenuSocialShare{str(forum.pk)}")) == 0

    def test_forum_detail_header_content(self, client, db, snapshot, reset_forum_sequence, forum_for_snapshot):
        response = client.get(forum_for_snapshot.get_absolute_url())
        content = parse_response_to_soup(response)

        assert str(content.select("section.s-title-01")[0]) == snapshot(name="forum_detail_heading")
        assert (
            len(
                content.select(
                    "article.textarea_cms_md",
                    string=(lambda x: x.startswith(str(forum_for_snapshot.description)[:10])),
                )
            )
            == 1
        )

        # NOTE: tests no subforum content rendered
        assert len(content.select("ul.list-group")) == 0

    def test_forum_detail_subforum_content_rendered(
        self, client, db, snapshot, reset_forum_sequence, forum_for_snapshot
    ):
        # subforum
        ForumFactory(parent=forum_for_snapshot, name="Test-Child", for_snapshot=True)

        response = client.get(forum_for_snapshot.get_absolute_url())
        content = parse_response_to_soup(response)

        subforum_content = content.select("ul.list-group")
        assert len(subforum_content) == 1
        assert str(subforum_content[0]) == snapshot(name="forum_detail_subforums")

    def test_forum_detail_foot_content(self, client, db, snapshot, reset_forum_sequence, forum_for_snapshot):
        response = client.get(forum_for_snapshot.get_absolute_url())
        content = parse_response_to_soup(response)

        assert forum_for_snapshot.is_forum
        forum_actions_block = content.select("div.forum-actions-block")
        assert len(forum_actions_block) == 1
        assert str(forum_actions_block[0]) == snapshot(name="forum_detail_forum_actions_block")


@pytest.fixture(name="documentation_category_forum_with_descendants")
def documentation_category_forum_with_descendants_fixture():
    tags = [faker.word() for _ in range(3)]
    category_forum = CategoryForumFactory()
    first_child = ForumFactory(parent=category_forum, with_tags=[tags[0]])
    second_child = ForumFactory(parent=category_forum, with_tags=[tags[0], tags[1]])
    third_child = ForumFactory(parent=category_forum, with_tags=[tags[2]])
    # forum without tags
    ForumFactory(parent=category_forum)

    # edge case: grand_child is filtered out. No actual use case to display them in the subforum list
    ForumFactory(parent=third_child, with_tags=[tags[2]])

    return category_forum, tags[0], [first_child, second_child]


@pytest.fixture(name="discussion_area_forum")
def discussion_area_forum_fixture():
    return ForumFactory(name="A Forum")


class TestBreadcrumb:
    def test_sub_discussion_area_forum(self, client, db, snapshot, discussion_area_forum):
        forum = ForumFactory(parent=discussion_area_forum, name="b")
        response = client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        assert response.status_code == 200
        content = parse_response_to_soup(response, selector="nav.c-breadcrumb")
        assert str(content) == snapshot(name="sub_discussion_area_forum")

    def test_forum(self, client, db, snapshot, discussion_area_forum):
        forum = ForumFactory()
        response = client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        assert response.status_code == 200
        content = parse_response_to_soup(response, selector="nav.c-breadcrumb")
        assert str(content) == snapshot(name="forum")

    def test_sub_forum(self, client, db, snapshot, discussion_area_forum):
        parent_forum = ForumFactory(name="B Forum")
        forum = ForumFactory(parent=parent_forum)
        response = client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        assert response.status_code == 200
        content = parse_response_to_soup(response, selector="nav.c-breadcrumb", replace_in_href=[parent_forum])
        assert str(content) == snapshot(name="sub_forum")

    def test_category_forum(self, client, db, snapshot, discussion_area_forum):
        forum = CategoryForumFactory()
        response = client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        assert response.status_code == 200
        content = parse_response_to_soup(response, selector="nav.c-breadcrumb")
        assert str(content) == snapshot(name="category_forum")

    def test_child_category_forum(self, client, db, snapshot, discussion_area_forum):
        parent_forum = CategoryForumFactory(with_child=True, name="A Category")
        forum = parent_forum.get_children().first()
        response = client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        assert response.status_code == 200
        content = parse_response_to_soup(response, selector="nav.c-breadcrumb", replace_in_href=[parent_forum])
        assert str(content) == snapshot(name="child_category_forum")

    def test_grandchild_category_forum(self, client, db, snapshot, discussion_area_forum):
        parent_forum = CategoryForumFactory(with_child=True, name="B Category")
        forum = ForumFactory(parent=parent_forum.get_children().first())
        response = client.get(reverse("forum_extension:forum", kwargs={"pk": forum.pk, "slug": forum.slug}))
        assert response.status_code == 200
        content = parse_response_to_soup(
            response,
            selector="nav.c-breadcrumb",
            replace_in_href=[parent_forum, parent_forum.get_children().first()],
        )
        assert str(content) == snapshot(name="grandchild_category_forum")
