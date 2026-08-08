from typing import cast
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions.exceptions import ServiceError


async def service_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    service_exc = cast(ServiceError, exc)
    
    return JSONResponse(
        status_code=service_exc.status_code,
        content={"detail": service_exc.detail},
    )

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )