import logging

from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from itoutils.django.nexus.token import decode_token

from lacommunaute.users.models import User


logger = logging.getLogger(__name__)


class AutoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if "auto_login" not in request.GET:
            return

        query_params = request.GET.copy()
        auto_login = query_params.pop("auto_login")
        email = None

        new_url = f"{request.path}?{query_params.urlencode()}" if query_params else request.path

        if len(auto_login) != 1:
            logger.info("Nexus auto login: Multiple tokens found -> ignored")
            return HttpResponseRedirect(new_url)
        else:
            [token] = auto_login

        try:
            decoded_data = decode_token(token)
            email = decoded_data.get("email")
        except ValueError:
            logger.info("Invalid auto login token")

        new_url = f"{request.path}?{query_params.urlencode()}" if query_params else request.path

        if email is None:
            logger.info("Nexus auto login: Missing email in token -> ignored")
            return HttpResponseRedirect(new_url)

        if request.user.is_authenticated:
            if request.user.email == email:
                logger.info("Nexus auto login: user is already logged in")
                return HttpResponseRedirect(new_url)
            else:
                logger.info("Nexus auto login: wrong user is logged in -> logging them out")
                # We should probably also logout the user from ProConnect but it requires to redirect to ProConnect
                # and the flow becomes a lotmore complicated
                logout(request)

        try:
            user = User.objects.get(email=email)
            logger.info("Nexus auto login: %s was found and forwarded to ProConnect", user)
        except User.DoesNotExist:
            logger.info("Nexus auto login: no user found, forward to ProConnect to create account")

        return HttpResponseRedirect(reverse("openid_connect:authorize", query={"next": new_url, "login_hint": email}))
