import logging

from django.urls import reverse
from itoutils.django.nexus.middleware import BaseAutoLoginMiddleware


logger = logging.getLogger(__name__)


class AutoLoginMiddleware(BaseAutoLoginMiddleware):
    def get_proconnect_authorize_url(self, user, next_url):
        return reverse("openid_connect:authorize", query={"next": next_url, "login_hint": user.email})

    def get_no_user_url(self, email, next_url):
        logger.info("Nexus auto login: forward to ProConnect to create account")
        return reverse("openid_connect:authorize", query={"next": next_url, "login_hint": email})
