from dataclasses import dataclass

@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    detail: str | None = None

    def __str__(self) -> str:
        return self.detail or self.message or self.code


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", detail: str | None = None):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401, detail=detail)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", detail: str | None = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=403, detail=detail)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found", detail: str | None = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=404, detail=detail)
