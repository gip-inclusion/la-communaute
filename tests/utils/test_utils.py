from datetime import timedelta

import pytest
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.template import Context, Template
from django.template.defaultfilters import date, time
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.timesince import timesince

from lacommunaute.utils.urls import urlize
from tests.testing import parse_response_to_soup


class SettingsContextProcessorsTest(TestCase):
    @override_settings(ALLOWED_HOSTS=["allowed.com"])
    def test_disallowed_host(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(hasattr(response.wsgi_request, "htmx"))

    def test_allowed_host(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(response.wsgi_request, "htmx"))

    def test_htmx_request(self):
        headers = {"HX-Request": True}
        response = self.client.get("/", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(response.wsgi_request, "htmx"))


class UtilsUrlsTestCase(TestCase):
    def test_urlize(self):
        url = "https://fake.com/url"
        url = f"{url}/long_string_to_truncate/"
        self.assertEqual(urlize(url, trim_url_limit=10), f'<a href="{url}">{url[:9]}…</a>')

        link = f'<a href="{url}">Something</a>'
        self.assertEqual(urlize(link), link)

        img = f'<img src="{url}">'
        self.assertEqual(urlize(img), img)


class TestUtilsTemplateTags:
    @pytest.mark.parametrize(
        "text,expected",
        [
            (
                "[youtube:123456abc]",
                (
                    "&lt;div&gt;&lt;iframe width=&quot;560&quot; height=&quot;315&quot; src=&quot;"
                    "https://www.youtube.com/embed/123456abc&quot; frameborder=&quot;0&quot; allow=&quot;"
                    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; "
                    "web-share&quot; referrerpolicy=&quot;strict-origin-when-cross-origin&quot; allowfullscreen&gt; "
                    "&lt;/iframe&gt;&lt;/div&gt;"
                ),
            ),
            ("[ youtube:123456abc]", "[ youtube:123456abc]"),
            ("[youtube:123456abc ]", "[youtube:123456abc ]"),
            ("[youtube:123456abc youtube:123456abc]", "[youtube:123456abc youtube:123456abc]"),
        ],
    )
    def test_youtube_embed(self, text, expected):
        template = Template("{% load str_filters %}{{ text|youtube_embed }}")
        out = template.render(Context({"text": text}))
        assert out == expected


class UtilsTemplateTagsTestCase(TestCase):
    def test_pluralizefr(self):
        """Test `pluralizefr` template tag."""
        template = Template("{% load str_filters %}Résultat{{ counter|pluralizefr }}")
        out = template.render(Context({"counter": 0}))
        self.assertEqual(out, "Résultat")
        out = template.render(Context({"counter": 1}))
        self.assertEqual(out, "Résultat")
        out = template.render(Context({"counter": 10}))
        self.assertEqual(out, "Résultats")

    def test_relativetimesince_fr(self):
        template = Template("{% load date_filters %}{{ date|relativetimesince_fr }}")

        d = timezone.now() - timedelta(hours=1)
        out = template.render(Context({"date": d}))
        self.assertEqual(out, f"il y a {timesince(d)}")

        d = timezone.now() - timedelta(days=2)
        out = template.render(Context({"date": d}))
        self.assertEqual(out, f"{date(d, 'l')}, {time(d)}")

        d = timezone.now() - timedelta(days=10)
        out = template.render(Context({"date": d}))
        self.assertEqual(out, f"le {date(d)}, {time(d)}")

    def test_urlizetrunc_target_blank(self):
        template = Template("{% load str_filters %}{{ str|urlizetrunc_target_blank:16 }}")
        out = template.render(Context({"str": "www.neuralia.co/mission"}))
        self.assertEqual(
            out, '<a target="_blank" href="http://www.neuralia.co/mission" rel="nofollow">www.neuralia.co…</a>'
        )

        out = template.render(Context({"str": 'src="www.neuralia.co/image.png"'}))
        self.assertEqual(out, "src=&quot;www.neuralia.co/image.png&quot;")

    def test_img_fluid(self):
        template = Template("{% load str_filters %}{{ html|img_fluid }}")
        out = template.render(Context({"html": '<img src="image.png">'}))
        self.assertEqual(out, '<img class="img-fluid" src="image.png">')

    def test_url_add_query(self):
        base_url = "https://fake.com/url"
        # Full URL.
        context = {"url": f"{base_url}/?status=new&page=4&page=1"}
        template = Template("{% load url_query_tags %}{% url_add_query url page=2 %}")
        out = template.render(Context(context))
        expected = f"{base_url}/?status=new&amp;page=2"
        assert out == expected

        # Relative URL.
        context = {"url": "/?status=new&page=1"}
        template = Template("{% load url_query_tags %}{% url_add_query url page=22 %}")
        out = template.render(Context(context))
        expected = "/?status=new&amp;page=22"
        assert out == expected

        # Empty URL.
        context = {"url": ""}
        template = Template("{% load url_query_tags %}{% url_add_query url page=1 %}")
        out = template.render(Context(context))
        expected = "?page=1"
        assert out == expected


class UtilsParseResponseToSoupTest(TestCase):
    def test_parse_wo_selector(self):
        html = '<html><head></head><body><div id="foo">bar</div></body></html>'
        response = HttpResponse(html)
        assert parse_response_to_soup(response) == BeautifulSoup(html, "html.parser")

    def test_parse_with_selector(self):
        response = HttpResponse('<html><head></head><body><div id="foo">bar</div></body></html>')
        assert str(parse_response_to_soup(response, selector="#foo")) == '<div id="foo">bar</div>'
