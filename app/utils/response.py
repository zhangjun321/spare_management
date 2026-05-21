# -*- coding: utf-8 -*-
"""
统一 API 响应格式
所有 REST API 应通过此模块返回响应，保证格式一致:
  { "code": 0, "message": "...", "data": ..., "timestamp": "..." }

错误码约定:
  0     - 成功
  10001 - 参数错误
  10002 - 未登录 / 登录过期
  10003 - 权限不足
  20001 - 资源不存在
  20002 - 资源冲突 (如重复创建)
  30001 - 业务逻辑错误
  30002 - 库存不足
  30003 - 状态流转非法
  50001 - 服务器内部错误
"""

import time
from flask import jsonify, Response


class ResponseCode:
    """API 错误码常量"""
    SUCCESS = 0
    PARAM_ERROR = 10001
    UNAUTHORIZED = 10002
    FORBIDDEN = 10003
    NOT_FOUND = 20001
    CONFLICT = 20002
    BUSINESS_ERROR = 30001
    STOCK_INSUFFICIENT = 30002
    INVALID_STATUS = 30003
    INTERNAL_ERROR = 50001


# 错误码 → HTTP 状态码 映射
_CODE_HTTP_MAP = {
    ResponseCode.SUCCESS: 200,
    ResponseCode.PARAM_ERROR: 400,
    ResponseCode.UNAUTHORIZED: 401,
    ResponseCode.FORBIDDEN: 403,
    ResponseCode.NOT_FOUND: 404,
    ResponseCode.CONFLICT: 409,
    ResponseCode.BUSINESS_ERROR: 422,
    ResponseCode.STOCK_INSUFFICIENT: 422,
    ResponseCode.INVALID_STATUS: 422,
    ResponseCode.INTERNAL_ERROR: 500,
}


def _http_status(code: int) -> int:
    """根据业务码返回合适的 HTTP 状态码"""
    return _CODE_HTTP_MAP.get(code, 500)


def json_response(
    code: int = ResponseCode.SUCCESS,
    message: str = "",
    data=None,
    http_status: int = None,
) -> tuple:
    """
    构造统一格式的 JSON 响应

    Args:
        code: 业务错误码 (默认 0=成功)
        message: 人类可读消息
        data: 载数据 (任意可序列化对象)
        http_status: 显式指定 HTTP 状态码 (可选，自动推断)

    Returns:
        (response, status_code) 可直接 return 给 Flask
    """
    body = {
        "code": code,
        "message": message or (_MSG_MAP.get(code) if code in _MSG_MAP else ("ok" if code == 0 else "error")),
        "timestamp": int(time.time()),
    }
    if data is not None:
        body["data"] = data

    status = http_status or _http_status(code)
    return jsonify(body), status


def ok(data=None, message: str = "success") -> tuple:
    """成功快捷方式"""
    return json_response(code=ResponseCode.SUCCESS, message=message, data=data)


def error(
    code: int = ResponseCode.INTERNAL_ERROR,
    message: str = "error",
    data=None,
    http_status: int = None,
) -> tuple:
    """错误快捷方式"""
    return json_response(code=code, message=message, data=data, http_status=http_status)


def paginated_data(items: list, total: int, page: int, per_page: int):
    """分页数据包装"""
    return {
        "list": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page > 0 else 0,
    }


# 默认提示文案（中英文双语预留）
_MSG_MAP = {
    ResponseCode.SUCCESS: "操作成功",
    ResponseCode.PARAM_ERROR: "参数错误",
    ResponseCode.UNAUTHORIZED: "未登录或登录已过期",
    ResponseCode.FORBIDDEN: "权限不足",
    ResponseCode.NOT_FOUND: "资源不存在",
    ResponseCode.CONFLICT: "资源冲突",
    ResponseCode.BUSINESS_ERROR: "业务逻辑错误",
    ResponseCode.STOCK_INSUFFICIENT: "库存不足",
    ResponseCode.INVALID_STATUS: "当前状态不允许此操作",
    ResponseCode.INTERNAL_ERROR: "服务器内部错误",
}
