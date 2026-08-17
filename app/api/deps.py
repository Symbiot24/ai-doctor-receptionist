from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database.db import SessionLocal
from app.database.models import AdminUser

_bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Require a valid, unexpired Bearer token for an active admin.

    Returns the AdminUser row or raises 401 for a missing/malformed/expired
    token and for deleted or inactive admins.
    """

    if credentials is None:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:

        admin_id = decode_access_token(credentials.credentials)

    except ValueError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = db.get(AdminUser, admin_id)

    if admin is None or not admin.is_active:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin
