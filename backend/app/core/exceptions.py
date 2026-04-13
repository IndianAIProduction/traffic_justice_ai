from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            detail=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationException(AppException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class RateLimitException(AppException):
    def __init__(self):
        super().__init__(
            detail="Rate limit exceeded. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
