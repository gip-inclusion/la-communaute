from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from lacommunaute.stats.models import Stat
from lacommunaute.utils.matomo import collect_stats_from_matomo_api


matomo_stats_names = [
    "nb_uniq_visitors",
    "nb_uniq_visitors_returning",
    "nb_uniq_active_visitors",
    "nb_uniq_engaged_visitors",
]


def get_initial_from_date(period):
    last_stat = Stat.objects.filter(period=period, name__in=matomo_stats_names).order_by("-date").first()
    if last_stat is None:
        return date(2022, 12, 1)

    from_date = last_stat.date
    if period == "day":
        return from_date + relativedelta(days=1)
    return from_date + relativedelta(months=1)


class Command(BaseCommand):
    help = "Collecter les stats matomo, jusqu'à la veille de l'execution"

    def handle(self, *args, **options):
        for period in ["day", "month"]:
            from_date = get_initial_from_date(period)

            if period == "day":
                to_date = date.today() - relativedelta(days=1)
            else:
                to_date = date.today().replace(day=1) - relativedelta(days=1)

            collect_stats_from_matomo_api(period, from_date, to_date)

        self.stdout.write(self.style.SUCCESS("That's all, folks!"))
