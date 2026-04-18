from app.core.errors import AppError


class DigitalWellbeingException(AppError):
    def __init__(self, message: str, code: str = "DIGITAL_WELLBEING_ERROR", status_code: int = 400, detail: str | None = None):
        super().__init__(code=code, message=message, status_code=status_code, detail=detail)


class ChatLimitExceededException(DigitalWellbeingException):
    def __init__(self, message: str = "Batas percobaan gratis telah tercapai."):
        super().__init__(message=message, code="CHAT_LIMIT_EXCEEDED", status_code=429)


class LLMProviderUnavailableException(DigitalWellbeingException):
    def __init__(self, message: str = "Layanan AI sedang tidak tersedia, silakan coba lagi nanti."):
        super().__init__(message=message, code="LLM_UNAVAILABLE", status_code=503)
