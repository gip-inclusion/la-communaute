import os

from lacommunaute.utils.enums import Environment


ENVIRONMENT = Environment.TEST
os.environ["ENVIRONMENT"] = ENVIRONMENT

from .base import *  # noqa: E402 F403


# Django settings
# ---------------
SECRET_KEY = "v3ry_s3cr3t_k3y"

# Database
# ------------------------------------------------------------------------------
DATABASES["default"]["HOST"] = os.getenv("PGHOST", "localhost")  # noqa: F405
DATABASES["default"]["PORT"] = os.getenv("PGPORT", "5432")  # noqa: F405
DATABASES["default"]["NAME"] = os.getenv("PGDATABASE", "communaute")  # noqa: F405
DATABASES["default"]["USER"] = os.getenv("PGUSER", "postgres")  # noqa: F405
DATABASES["default"]["PASSWORD"] = os.getenv("PGPASSWORD", "password")  # noqa: F405

# SENDINBLUE
# ---------------------------------------
SIB_URL = "http://test.com"
SIB_API_KEY = "dummy-sib-api-key"

# EMPLOIS
# ---------------------------------------
EMPLOIS_PRESCRIBER_SEARCH = "http://test.com/prescriber/search"
EMPLOIS_COMPANY_SEARCH = "http://test.com/company/search"

ASSERT_SNAPSHOT_QUERIES_EXTRA_PACKAGES_ALLOWLIST = []
