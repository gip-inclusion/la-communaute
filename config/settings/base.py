import os

from django.utils.csp import CSP
from dotenv import load_dotenv

from lacommunaute.utils.enums import Environment


load_dotenv()

# Django settings
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/
# ---------------
_current_dir = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(_current_dir, "../.."))

APPS_DIR = os.path.abspath(os.path.join(ROOT_DIR, "lacommunaute"))

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ENVIRONMENT = Environment(os.getenv("ENVIRONMENT"))

PARKING_PAGE = os.getenv("PARKING_PAGE", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "communaute.inclusion.gouv.fr,").split(",")

# Application definition
DJANGO_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.redirects",
    "django.contrib.flatpages",
]

THIRD_PARTIES_APPS = [
    "compressor",  # django-compressor
    "django_social_share",
    "django_htmx",
]

# MIGRATION CONFIGURATION
# ------------------------------------------------------------------------------


LOCAL_APPS = [
    # Core apps, order is important.
    "lacommunaute.utils",
    "lacommunaute.pages",
    "lacommunaute.search",
    "lacommunaute.partner",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTIES_APPS

DJANGO_MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.redirects.middleware.RedirectFallbackMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "lacommunaute.utils.middleware.ParkingPageMiddleware",
]

THIRD_PARTIES_MIDDLEWARE = [
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]


MIDDLEWARE = DJANGO_MIDDLEWARE + THIRD_PARTIES_MIDDLEWARE

ROOT_URLCONF = "config.urls"
LOGIN_URL = "/"  # No login page

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(APPS_DIR, "templates"),
        ],
        # "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.template.context_processors.media",
                "lacommunaute.utils.context_processors.expose_settings",
                "lacommunaute.utils.context_processors.matomo",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ATOMIC_REQUESTS": True,
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "HOST": os.getenv("POSTGRESQL_ADDON_HOST"),
        "PORT": os.getenv("POSTGRESQL_ADDON_PORT"),
        "NAME": os.getenv("POSTGRESQL_ADDON_DB"),
        "USER": os.getenv("POSTGRESQL_ADDON_USER"),
        "PASSWORD": os.getenv("POSTGRESQL_ADDON_PASSWORD"),
    }
}


# TODO: Remove with Django 6.0
FORMS_URLFIELD_ASSUME_HTTPS = True

LOCALE_PATHS = (os.path.join(ROOT_DIR, "locale"),)

TIME_ZONE = "Europe/Paris"
USE_TZ = True
DATE_INPUT_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

# Static Files
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    os.path.join(APPS_DIR, "static"),
]

STATIC_ROOT = os.path.join(APPS_DIR, "staticfiles")

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)
COMPRESS_OFFLINE = True
COMPRESS_OFFLINE_CONTEXT = {
    "BASE_TEMPLATE": "layouts/base.html",
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cache
# TODO : improve default cache later, with pymemcache or redis
# https://docs.djangoproject.com/en/4.1/topics/cache/
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_table",
    },
}

COMMU_PROTOCOL = "https"
COMMU_FQDN = os.getenv("COMMU_FQDN", "communaute.inclusion.gouv.fr")


# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "itoutils.django.logging.DataDogJSONFormatter"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        "commands": {
            "handlers": ["console"],
            "level": os.getenv("COMMANDS_LOG_LEVEL", "INFO"),
        },
    },
}

_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    from ._sentry import sentry_init

    sentry_init(dsn=_sentry_dsn)

# Django sites framework
SITE_ID = 1

# EMPLOI
# ------------------------------------------------------------------------------
EMPLOI_BASE_URL = os.getenv("EMPLOI_BASE_URL", "https://emplois.inclusion.beta.gouv.fr")
EMPLOIS_PRESCRIBER_SEARCH = f"{EMPLOI_BASE_URL}/search/prescribers"
EMPLOIS_COMPANY_SEARCH = f"{EMPLOI_BASE_URL}/search/employers"

# MATOMO
# ---------------------------------------
MATOMO_BASE_URL = os.getenv("MATOMO_BASE_URL", None)
MATOMO_SITE_ID = int(os.getenv("MATOMO_SITE_ID", "1"))
MATOMO_AUTH_TOKEN = os.getenv("MATOMO_AUTH_TOKEN", None)


# CSP
# ---------------------------------------
connect_src = [
    CSP.SELF,
    "*.sentry.io",
]
img_src = [
    CSP.SELF,
    "data:",
    "cellar-c2.services.clever-cloud.com",
]
script_src = [
    CSP.SELF,
    CSP.NONCE,
    "https://cdn.jsdelivr.net/npm/chart.js@4.0.1",
    "https://cdn.jsdelivr.net/npm/jquery@3.6.1/dist/jquery.min.js",
    "https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js",
    # https://docs.sentry.io/platforms/javascript/install/loader/#content-security-policy
    "https://browser.sentry-cdn.com/9.30.0/bundle.min.js",
    "https://tally.so",
    "https://www.youtube.com/iframe_api",
    "https://www.youtube.com/s/player/",
]
style_src = [
    CSP.SELF,
    "https://fonts.googleapis.com",
    CSP.UNSAFE_INLINE,  # needed for htmx.js, embed.js & tartecitron.js
]

if MATOMO_BASE_URL:
    connect_src += [
        MATOMO_BASE_URL,
    ]
    img_src += [
        MATOMO_BASE_URL,
    ]
    script_src += [
        MATOMO_BASE_URL,
    ]

SECURE_CSP = {
    "default-src": [
        CSP.SELF,
    ],
    "connect-src": connect_src,
    "img-src": img_src,
    "frame-src": [
        CSP.SELF,
        "https://tally.so",
        "https://www.youtube.com/embed/",
    ],
    "font-src": [
        CSP.SELF,
        "https://fonts.gstatic.com/",
        "data:",
    ],
    "script-src": script_src,
    "script-src-elem": script_src,
    "style-src": style_src,
    "style-src-elem": style_src,
}

# HSTS
# ---------------------------------------
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Clickjacking
# ---------------------------------------
X_FRAME_OPTIONS = "DENY"

# SECURITY
# ---------------------------------------
# See https://docs.djangoproject.com/en/4.1/topics/security/
# and https://docs.djangoproject.com/en/4.1/ref/middleware/#module-django.middleware.security
# See https://docs.djangoproject.com/en/4.1/ref/middleware/#http-strict-transport-security

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# SESSIONS
# ---------------------------------------
CSRF_COOKIE_SECURE = True

# PERMISSIONS POLICIES
# ---------------------------------------
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "autoplay": [],
    "camera": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "picture-in-picture": [],
    "sync-xhr": [],
    "usb": [],
}
