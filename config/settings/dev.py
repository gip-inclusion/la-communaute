import os

# Enable django-debug-toolbar with Docker.
import socket

from lacommunaute.utils.enums import Environment


# Define ENVIRONMENT before to import base.
os.environ["ENVIRONMENT"] = Environment.DEV
from .test import *  # noqa: F403 F401


# Override ENVIRONMENT from test settings.
ENVIRONMENT = Environment.DEV


# Django settings
# ---------------
DEBUG = True

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "192.168.0.1"]

# Security.
# ------------------------------------------------------------------------------
CSRF_COOKIE_SECURE = False

# Django-debug-toolbar.
# ------------------------------------------------------------------------------

INTERNAL_IPS = ["127.0.0.1"]

# Enable django-debug-toolbar with Docker.
_, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]

SECURE_CSP["default-src"] = ["*"]  # noqa undefined-local-with-import-star-usage
SECURE_CSP["img-src"].append("localhost:9000")  # noqa undefined-local-with-import-star-usage

COMMU_PROTOCOL = "http"
COMMU_FQDN = "127.0.0.1:8000"
