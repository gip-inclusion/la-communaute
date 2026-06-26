from django.urls import reverse


def test_sitemap(client, db, snapshot):
    url = reverse("pages:django.contrib.sitemaps.views.sitemap")
    response = client.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/xml"
    assert "sitemap.xml" in response.templates[0].name
    assert response.content.decode() == snapshot
