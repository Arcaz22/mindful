from app.core.errors import AppError


class ChatException(AppError):
    def __init__(self, message: str, code: str = "CHAT_ERROR", status_code: int = 400, detail: str | None = None):
        super().__init__(code=code, message=message, status_code=status_code, detail=detail)


class UserNotFoundException(ChatException):
    def __init__(self, message: str = "User tidak ditemukan."):
        super().__init__(message=message, code="USER_NOT_FOUND", status_code=404)
