import datetime

import pytest
from freezegun import freeze_time
from jwcrypto import jwt

from lacommunaute.nexus.utils import EXPIRY_DELAY, decode_jwt, generate_jwt
from lacommunaute.users.factories import UserFactory


def test_generate_and_decode_jwt(db):
    with freeze_time() as frozen_now:
        user = UserFactory()
        token = generate_jwt(user)

        # generated token requires a key to decode
        with pytest.raises(KeyError):
            jwt.JWT(jwt=token).claims

        # It contains the user email
        assert decode_jwt(token) == {"email": user.email}

        # Wait for the JWT to expire, and then extra time for the leeway.
        leeway = 60
        frozen_now.tick(datetime.timedelta(seconds=EXPIRY_DELAY + leeway + 1))
        with pytest.raises(ValueError):
            decode_jwt(token)
