from django import forms
from django.utils.translation import gettext_lazy as _


class SearchForm(forms.Form):
    q = forms.CharField(
        max_length=255,
        required=False,
        label=_("Search for keywords"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Keywords or phrase"),
                "type": "search",
            }
        ),
    )
