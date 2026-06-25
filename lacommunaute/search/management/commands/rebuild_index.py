from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand

from lacommunaute.documentation.helpers import CARDS, CATEGORIES
from lacommunaute.search.models import CommonIndex


class Command(BaseCommand):
    help = "Index all categories and cards"

    def handle(self, *args, **kwargs):
        indexes = []
        for category in CATEGORIES:
            content = "\n".join(
                [
                    category["name"],
                    category["description"],
                    category["content"],
                ]
            )
            indexes.append(
                CommonIndex(
                    title=category["name"],
                    content=content,
                    category_slug=category["slug"],
                )
            )

        for card in CARDS.values():
            content = "\n".join(
                [
                    card["name"],
                    card["description"],
                    card["content"],
                ]
            )
            indexes.append(
                CommonIndex(
                    title=card["name"],
                    content=content,
                    card_slug=card["slug"],
                )
            )
        CommonIndex.objects.all().delete()
        CommonIndex.objects.bulk_create(indexes)
        CommonIndex.objects.update(content_ts=SearchVector("content"))
        self.stdout.write(self.style.SUCCESS("Indices refreshed!"))
