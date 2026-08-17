from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.auth import AdminMeResponse
from app.api.schemas.auth import LoginRequest
from app.api.schemas.auth import PasswordChange
from app.api.schemas.auth import ProfileUpdate
from app.api.schemas.auth import TokenResponse
from app.auth.security import create_access_token
from app.auth.security import verify_password
from app.database.models import AdminUser
from app.services.admin_service import AdminService

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):

    admin = AdminService(db).get_by_email(payload.email)

    # Generic error for both "no such admin" and "wrong password" so the
    # API never reveals whether an email exists. Inactive admins get the
    # same generic response.
    if admin is None or not admin.is_active:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(payload.password, admin.password_hash):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    return TokenResponse(
        access_token=create_access_token(admin.id),
    )


@router.get("/me", response_model=AdminMeResponse)
def me(
    admin: AdminUser = Depends(get_current_admin),
):

    # Only ever expose safe fields. password_hash is never serialized
    # because response_model only includes id/name/email/is_active.
    return admin


@router.put("/profile", response_model=AdminMeResponse)
def update_profile(
    payload: ProfileUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):

    if payload.name is None and payload.email is None:

        raise HTTPException(
            status_code=400,
            detail="Nothing to update.",
        )

    try:

        updated = AdminService(db).update_profile(
            admin.id,
            name=payload.name,
            email=payload.email,
        )

    except ValueError as exc:

        raise HTTPException(status_code=400, detail=str(exc))

    return updated


@router.put("/password")
def change_password(
    payload: PasswordChange,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):

    # Note on token invalidation: JWTs are stateless and carry only
    # sub + iat + exp. There is no token version or revocation list, so a
    # token issued before a password change stays valid until it expires.
    # Full revocation would require a token_version on AdminUser (or a
    # blacklist); that is deliberately out of scope for now.
    try:

        AdminService(db).change_password(
            admin.id,
            payload.current_password,
            payload.new_password,
            payload.confirm_password,
        )

    except ValueError as exc:

        raise HTTPException(status_code=400, detail=str(exc))

    return {"detail": "Password updated."}
