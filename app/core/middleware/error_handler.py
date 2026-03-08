import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.errors import AppError

logger = logging.getLogger("app.error")


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except AppError as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "code": e.code,
                    "message": e.message,
                    "detail": e.detail,
                },
            )
        except Exception as e:
            logger.exception(
                "Unhandled error",
                extra={"request_id": getattr(request.state, "request_id", None)},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                    "detail": str(e),
                },
            )
