"""
自定义异常处理
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger


class APIException(Exception):
    """API 异常基类"""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(APIException):
    """资源未找到异常"""
    def __init__(self, message: str = "资源未找到"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class UnauthorizedException(APIException):
    """未授权异常"""
    def __init__(self, message: str = "未授权访问"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(APIException):
    """禁止访问异常"""
    def __init__(self, message: str = "禁止访问"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class BadRequestException(APIException):
    """错误请求异常"""
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class InternalServerException(APIException):
    """服务器内部错误"""
    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def api_exception_handler(request: Request, exc: APIException):
    """API 异常处理器"""
    logger.error(f"API异常: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = exc.errors()
    logger.warning(f"请求验证失败: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "请求参数验证失败",
            "errors": errors
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.exception(f"未捕获的异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "data": None
        }
    )
