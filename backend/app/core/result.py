from typing import Any, Optional

from pydantic import BaseModel


class Result(BaseModel):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

    @staticmethod
    def ok(data: Any = None, message: str = "success") -> "Result":
        return Result(code=200, message=message, data=data)

    @staticmethod
    def error(code: int = 500, message: str = "error", data: Any = None) -> "Result":
        return Result(code=code, message=message, data=data)

    @staticmethod
    def unauthorized(message: str = "未登录或Token已过期") -> "Result":
        return Result(code=401, message=message)

    @staticmethod
    def forbidden(message: str = "无权限访问") -> "Result":
        return Result(code=403, message=message)

    @staticmethod
    def bad_request(message: str = "请求参数错误") -> "Result":
        return Result(code=400, message=message)
