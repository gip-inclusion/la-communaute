import re

from django.utils.functional import keep_lazy_text
from django.utils.html import Urlizer as BaseUrlizer
from django.utils.regex_helper import _lazy_re_compile


class Urlizer(BaseUrlizer):
    """
    override django.utils.html.Urlizer to fix conflict between markdown and urlize
    """

    # do not split string from its leading/trailing double quote,
    # to keep markdown link rendered in html (src="www.example.com" and href="www.example.com")
    word_split_re = _lazy_re_compile(r"""([\s<>']+)""")

    # do not consider string containing src= or href= as url
    simple_url_2_re = _lazy_re_compile(
        r"^www\.|^(?!http|src=|href=)\w[^@]+\.(com|edu|gov|int|mil|net|org|fr)($|/.*)$", re.IGNORECASE
    )


urlizer = Urlizer()


@keep_lazy_text
def urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
    return urlizer(text, trim_url_limit=trim_url_limit, nofollow=nofollow, autoescape=autoescape)
