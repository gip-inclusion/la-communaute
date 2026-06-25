import uuid

from django.contrib.postgres.search import SearchVectorField
from django.db import models


class CommonIndex(models.Model):
    """
    A materialized view for use as a search index for categories and cards:

    To increase search performance, the indexed documents tsvector is
    denormalized into the _ts field.
    """

    id = models.UUIDField(primary_key=True, editable=False, verbose_name="ID", default=uuid.uuid4)
    title = models.CharField(editable=False)
    content = models.TextField(editable=False)
    content_ts = SearchVectorField(editable=False)
    category_slug = models.CharField(editable=False)
    card_slug = models.CharField(editable=False)
