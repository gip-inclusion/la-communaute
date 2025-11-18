import datetime
from unittest import mock

import pytest
from django.core.management import call_command
from freezegun import freeze_time

from lacommunaute.stats.factories import StatFactory
from lacommunaute.stats.management.commands.collect_matomo_stats import get_initial_from_date, matomo_stats_names
from lacommunaute.stats.models import Stat
from lacommunaute.surveys.factories import DSPFactory


def test_collect_django_stats(db, capsys):
    DSPFactory()
    StatFactory(for_dsp_snapshot=True)
    call_command("collect_django_stats")
    captured = capsys.readouterr()
    assert captured.out.strip() == "Collecting DSP stats from 2024-05-18 to yesterday: 1 new stats\nThat's all, folks!"


@pytest.mark.parametrize(
    "name", ["nb_uniq_visitors", "nb_uniq_visitors_returning", "nb_uniq_active_visitors", "nb_uniq_engaged_visitors"]
)
def test_get_initial_from_date_in_collect_matomo_stats(db, name):
    # desired datas for sorting test
    StatFactory(period="day", name=name, date="2024-05-17")
    StatFactory(period="day", name=name, date="2024-05-18")

    # undesired datas
    StatFactory(period="xxx", name=name, date="2024-05-19")
    StatFactory(period="day", name="unexpected_name", date="2024-05-20")

    assert get_initial_from_date("day") == datetime.date(2024, 5, 19)


def test_collect_matomo_stats(db, mocker):
    # Fake command launched on 2025-10-31 :
    # day period filled up to 2025-10-30
    # month period filled up to 2025-09-01
    stats = []
    for name in matomo_stats_names:
        stats.append(StatFactory.build(period="day", name=name, date="2025-10-30"))  # previous day
        stats.append(StatFactory.build(period="month", name=name, date="2025-09-01"))  # Start of previous month
    Stat.objects.bulk_create(stats)

    # Mock get_matomo_visits_data and get_matomo_events_data to return one stat per call
    visits_mock = mocker.patch(
        "lacommunaute.utils.matomo.get_matomo_visits_data",
        side_effect=lambda period, search_date: [
            {"period": period, "date": search_date.strftime("%Y-%m-%d"), "name": "nb_uniq_visitors", "value": 10}
        ],
    )
    events_mock = mocker.patch(
        "lacommunaute.utils.matomo.get_matomo_events_data",
        side_effect=lambda period, search_date, nb_uniq_visitors_key: [
            {
                "period": period,
                "date": search_date.strftime("%Y-%m-%d"),
                "name": "nb_uniq_active_visitors",
                "value": 10,
            }
        ],
    )
    # Nominal case :
    with freeze_time("2025-11-01"):
        call_command("collect_matomo_stats")
        assert visits_mock.call_args_list == [
            mock.call("day", datetime.date(2025, 10, 31)),
            mock.call("month", datetime.date(2025, 10, 1)),
        ]
        assert events_mock.call_args_list == [
            mock.call("day", datetime.date(2025, 10, 31), nb_uniq_visitors_key="nb_uniq_visitors"),
            mock.call("month", datetime.date(2025, 10, 1), nb_uniq_visitors_key="sum_daily_nb_uniq_visitors"),
        ]
    # one stat created per call to get_matomo_visits_data or get_matomo_events_data
    assert Stat.objects.filter(period="day", date__gte="2025-10-31").count() == 2
    assert Stat.objects.filter(period="month", date__gte="2025-10-01").count() == 2

    # Another call on the same day : nothing happens
    visits_mock.reset_mock()
    events_mock.reset_mock()
    with freeze_time("2025-10-01"):
        call_command("collect_matomo_stats")
        assert visits_mock.call_args_list == []
        assert events_mock.call_args_list == []

    # Next day: Only add day stat
    visits_mock.reset_mock()
    events_mock.reset_mock()
    with freeze_time("2025-11-02"):
        call_command("collect_matomo_stats")
        assert visits_mock.call_args_list == [
            mock.call("day", datetime.date(2025, 11, 1)),
        ]
        assert events_mock.call_args_list == [
            mock.call("day", datetime.date(2025, 11, 1), nb_uniq_visitors_key="nb_uniq_visitors"),
        ]
        assert Stat.objects.filter(period="day", date__gte="2025-10-31").count() == 4
        assert Stat.objects.filter(period="month", date__gte="2025-10-01").count() == 2

    # Edge case: the command skipped a day 2025-11-01
    Stat.objects.filter(period="day", date__gte="2025-10-31").delete()
    Stat.objects.filter(period="month", date__gte="2025-10-01").delete()
    visits_mock.reset_mock()
    events_mock.reset_mock()
    with freeze_time("2025-11-02"):
        call_command("collect_matomo_stats")
        assert visits_mock.call_args_list == [
            mock.call("day", datetime.date(2025, 10, 31)),
            mock.call("day", datetime.date(2025, 11, 1)),
            mock.call("month", datetime.date(2025, 10, 1)),
        ]
        assert events_mock.call_args_list == [
            mock.call("day", datetime.date(2025, 10, 31), nb_uniq_visitors_key="nb_uniq_visitors"),
            mock.call("day", datetime.date(2025, 11, 1), nb_uniq_visitors_key="nb_uniq_visitors"),
            mock.call("month", datetime.date(2025, 10, 1), nb_uniq_visitors_key="sum_daily_nb_uniq_visitors"),
        ]
    assert Stat.objects.filter(period="day", date__gte="2025-10-31").count() == 4
    assert Stat.objects.filter(period="month", date__gte="2025-10-01").count() == 2
