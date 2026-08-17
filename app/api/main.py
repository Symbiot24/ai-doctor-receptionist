import logging
import traceback

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import CORS_ORIGINS
from app.api.routes import auth
from app.api.routes import availability
from app.api.routes import appointments
from app.api.routes import clinic
from app.api.routes import clinic_day_offs
from app.api.routes import dashboard
from app.api.routes import day_offs
from app.api.routes import doctors
from app.api.routes import schedules

logger = logging.getLogger("clinic-api")

app = FastAPI(
    title="Clinic Management API",
    description=(
        "REST API for the clinic admin frontend. Wraps the existing "
        "service layer (clinic, doctors, schedules, day-offs, availability)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clinic.router)
app.include_router(clinic_day_offs.router)
app.include_router(doctors.router)
app.include_router(schedules.router)
app.include_router(day_offs.router)
app.include_router(availability.router)
app.include_router(appointments.router)
app.include_router(dashboard.router)
app.include_router(auth.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):

    # Log the full traceback server-side for debugging, but never leak
    # SQLAlchemy/PostgreSQL internals to the frontend.
    logger.error(
        "Unhandled error on %s %s\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
    )
