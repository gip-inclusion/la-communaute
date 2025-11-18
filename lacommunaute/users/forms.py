from django import forms
from django.core.exceptions import ValidationError

from lacommunaute.forum_moderation.models import BlockedDomainName, BlockedEmail


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(attrs={"placeholder": "Votre adresse email"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        domain = email.split("@")[-1]
        if BlockedDomainName.objects.filter(domain=domain).exists():
            raise ValidationError(f"Les emails utilisant le domaine {domain} ont été bannis.")
        elif BlockedEmail.objects.filter(email=email).exists():
            raise ValidationError(f"L’utilisateur associé à {email} a été banni.")
        return email


class CreateUserForm(forms.Form):
    first_name = forms.CharField(label="Votre prénom", max_length=150)
    last_name = forms.CharField(label="Votre nom", max_length=150)
    email = forms.EmailField(label="Votre adresse email")
