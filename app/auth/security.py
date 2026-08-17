"""Password and JWT utilities for admin authentication.

Passwords are never stored in plaintext. Hashing uses Argon2id (the default
algorithm of argon2-cffi's PasswordHasher); each hash embeds its own random
salt and tuning parameters, so the same password hashes differently every
time and there is no separate salt column to store.

Access tokens are signed JWTs (HS256 by default). The signing secret comes
from the JWT_SECRET_KEY environment variable and is never hardcoded.
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError
from argon2.exceptions import VerificationError
from argon2.exceptions import VerifyMismatchError

from app.core.config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.config import JWT_ALGORITHM
from app.core.config import JWT_SECRET_KEY

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2id hash string for the given plaintext password."""

    if not isinstance(password, str):
        raise TypeError("password must be a string")

    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when password matches the stored Argon2id hash.

    Any malformed hash, empty value or mismatch safely returns False.
    """

    if not isinstance(password, str) or not password_hash:
        return False

    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False


# ---------------- JWT tokens ---------------- #


def _require_secret():

    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured. Set it in the environment "
            "(see .env.example)."
        )


def create_access_token(
    admin_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token for the admin.

    The subject claim is the stringified admin id; expiry defaults to
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES (60 minutes).
    """

    _require_secret()

    now = datetime.now(timezone.utc)

    expire = now + (
        expires_delta
        or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(admin_id),
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """Decode and validate a JWT, returning the admin id.

    Raises ValueError on malformed, tampered or expired tokens so callers
    can map the failure to a 401 response.
    """

    _require_secret()

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

    except jwt.ExpiredSignatureError:

        raise ValueError("Token has expired.")

    except jwt.InvalidTokenError:

        raise ValueError("Invalid token.")

    subject = payload.get("sub")

    try:

        return int(subject)

    except (TypeError, ValueError):

        raise ValueError("Invalid token.")
