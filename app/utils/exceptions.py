# -*- coding: utf-8 -*-
"""
自定义业务异常
Service 层通过 raise 抛出这些异常，由全局错误处理器统一捕获并返回标准格式
"""

from app.utils.response import ResponseCode


class BusinessError(Exception):
    """
    基础业务异常
    用法: raise BusinessError("库存不足", code=ResponseCode.STOCK_INSUFFICIENT)
    """

    def __init__(self, message: str = "业务逻辑错误",
                 code: int = ResponseCode.BUSINESS_ERROR,
                 data=None,
                 http_status: int = None):
        self.message = message
        self.code = code
        self.data = data
        self.http_status = http_status
        super().__init__(message)


class ParamError(BusinessError):
    """参数验证失败"""

    def __init__(self, message: str = "参数错误", data=None):
        super().__init__(message=message, code=ResponseCode.PARAM_ERROR, data=data)


class UnauthorizedError(BusinessError):
    """未授权访问"""

    def __init__(self, message: str = "需要登录"):
        super().__init__(message=message, code=ResponseCode.UNAUTHORIZED)


class ForbiddenError(BusinessError):
    """权限不足"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, code=ResponseCode.FORBIDDEN)


class NotFoundError(BusinessError):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在", resource: str = ""):
        msg = f"{resource}不存在" if resource else message
        super().__init__(message=msg, code=ResponseCode.NOT_FOUND)


class ConflictError(BusinessError):
    """资源冲突 (如重复创建)"""

    def __init__(self, message: str = "数据已存在"):
        super().__init__(message=message, code=ResponseCode.CONFLICT)


class StockInsufficientError(BusinessError):
    """库存不足"""

    def __init__(self, message: str = "库存不足", data=None):
        super().__init__(message=message, code=ResponseCode.STOCK_INSUFFICIENT, data=data)


class InvalidStatusError(BusinessError):
    """状态流转非法"""

    def __init__(self, message: str = "当前状态不允许此操作", current_status: str = "", allowed: list = None):
        detail = {"current": current_status}
        if allowed:
            detail["allowed"] = allowed
        super().__init__(message=message, code=ResponseCode.INVALID_STATUS, data=detail)


class ConcurrentModificationError(BusinessError):
    """并发修改冲突 (乐观锁检测到数据已被其他用户修改)"""

    def __init__(self, message: str = "数据已被其他用户修改，请刷新后重试"):
        super().__init__(message=message, code=ResponseCode.CONFLICT)
