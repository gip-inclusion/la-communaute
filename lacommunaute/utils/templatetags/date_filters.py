import datetime

from django import template
from django.template.defaultfilters import date, time
from django.utils import timezone
from django.utils.timesince import timesince


register = template.Library()


@register.filter(is_safe=False)
def relativetimesince_fr(d):
    now = timezone.now()

    if d < now - datetime.timedelta(days=6):
        return f"le {date(d)}, {time(d)}"

    if d < now - datetime.timedelta(days=1):
        return f"{date(d, 'l')}, {time(d)}"

    return f"il y a {timesince(d)}"
