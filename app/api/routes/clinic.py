from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.deps import get_db
from app.api.schemas.clinic import ClinicResponse
from app.api.schemas.clinic import ClinicUpdate
from app.services.clinic_service import ClinicService

router = APIRouter(
    prefix="/api/clinic",
    tags=["clinic"],
    dependencies=[Depends(get_current_admin)],
)


def _resolve_current_clinic(db):

    try:

        return ClinicService(db).get()

    except ValueError as error:

        message = str(error)

        if "Expected exactly one clinic" in message:

            # Server configuration problem: the database must contain
            # exactly one clinic record.
            raise HTTPException(
                status_code=500,
                detail=message,
            )

        raise HTTPException(
            status_code=404,
            detail=message,
        )


@router.get("", response_model=ClinicResponse)
def get_clinic(db: Session = Depends(get_db)):

    return _resolve_current_clinic(db)


@router.put("", response_model=ClinicResponse)
def update_clinic(
    payload: ClinicUpdate,
    db: Session = Depends(get_db),
):

    clinic = _resolve_current_clinic(db)

    return ClinicService(db).update(
        clinic,
        payload.model_dump(exclude_unset=True),
    )
