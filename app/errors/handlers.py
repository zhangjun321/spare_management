# -*- coding: utf-8 -*-
"""
统一错误处理模块 v2
- 使用统一 API 响应格式 (ResponseCode)
- 支持业务异常自动捕获
- API / 页面请求自动区分
"""

import logging
import traceback
from flask import render_template, Blueprint, request, jsonify

from app.utils.response import json_response, ResponseCode

errors_bp = Blueprint('errors', __name__)

logger = logging.getLogger(__name__)


def is_api_request():
    """判断是否是 API 请求（含所有 React 前端调用的接口）"""
    path = request.path
    api_indicators = [
        '/api/', '/ai-image/',
        # React 前端调用的数据接口前缀（非页面）
        '/api_transactions', '/api_warehouses', '/api_spare_parts',
        '/api_inbound', '/api_outbound', '/api_inventory',
        '/inventory_concurrency', '/warehouse_v3',
        '/industrial_equipment_api', '/spare_parts_api',
    ]
    return any(p in path for p in api_indicators) or \
           'application/json' in request.headers.get('Accept', '')


# ── HTTP 标准错误 ────────────────────────────────────────

@errors_bp.app_errorhandler(400)
def bad_request(error):
    if is_api_request():
        return json_response(code=ResponseCode.PARAM_ERROR, message="请求无效，请检查输入参数")
    return render_template('errors/400.html'), 400


@errors_bp.app_errorhandler(401)
def unauthorized(error):
    if is_api_request():
        return json_response(
            code=ResponseCode.UNAUTHORIZED,
            message="未登录或登录已过期，请重新登录",
            data={"redirect": "/login"}
        )
    return render_template('errors/401.html'), 401


@errors_bp.app_errorhandler(403)
def forbidden(error):
    if is_api_request():
        return json_response(code=ResponseCode.FORBIDDEN, message="权限不足，无法执行此操作")
    return render_template('errors/403.html'), 403


@errors_bp.app_errorhandler(404)
def not_found(error):
    if is_api_request():
        return json_response(code=ResponseCode.NOT_FOUND, message="请求的资源不存在")
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(405)
def method_not_allowed(error):
    if is_api_request():
        return json_response(code=ResponseCode.PARAM_ERROR, message=f"不支持的 HTTP 方法: {request.method}")
    return render_template('errors/405.html') if _template_exists('errors/405.html') else ("Method Not Allowed", 405)


@errors_bp.app_errorhandler(409)
def conflict(error):
    if is_api_request():
        return json_response(code=ResponseCode.CONFLICT, message="资源冲突，请检查数据是否重复")
    return ("Conflict", 409)


@errors_bp.app_errorhandler(413)
def entity_too_large(error):
    if is_api_request():
        return json_response(code=ResponseCode.PARAM_ERROR, message="上传文件过大，请压缩后重试")
    return ("File Too Large", 413)


@errors_bp.app_errorhandler(422)
def unprocessable_entity(error):
    if is_api_request():
        return json_response(code=ResponseCode.BUSINESS_ERROR, message="请求数据处理失败")
    return ("Unprocessable Entity", 422)


@errors_bp.app_errorhandler(500)
def internal_server_error(error):
    # 记录完整堆栈
    trace_id = _gen_trace_id()
    logger.error(f"[{trace_id}] 500 Internal Error on {request.path}: {str(error)}\n{traceback.format_exc()}")

    if is_api_request():
        return json_response(
            code=ResponseCode.INTERNAL_ERROR,
            message="服务器内部错误，请联系管理员",
            data={"trace_id": trace_id}
        )
    return render_template('errors/500.html', trace_id=trace_id), 500


# ── 全局异常兜底 (未处理的 Python 异常) ────────────────
@errors_bp.app_errorhandler(Exception)
def handle_unhandled_exception(error):
    """捕获所有未被上面处理器处理的异常"""
    trace_id = _gen_trace_id()
    logger.error(f"[{trace_id}] Unhandled Exception on {request.path}: {type(error).__name__}: {error}\n{traceback.format_exc()}")

    # 不暴露内部错误详情给前端
    if is_api_request():
        return json_response(
            code=ResponseCode.INTERNAL_ERROR,
            message="服务器内部错误，请稍后重试",
            data={"trace_id": trace_id}
        )

    # 开发环境显示详细错误，生产环境显示友好页面
    from flask import current_app
    if current_app.config.get('DEBUG', False):
        return f"<h1>500 Internal Server Error</h1><pre>{traceback.format_exc()}</pre>", 500
    return render_template('errors/500.html', trace_id=trace_id), 500


# ── 辅助函数 ────────────────────────────────────────────

_trace_counter = 0


def _gen_trace_id() -> str:
    """生成简短追踪 ID 用于日志关联"""
    global _trace_counter
    _trace_counter += 1
    import time
    return f"{int(time.time() * 1000) % 1000000:05d}{_trace_counter % 1000:03d}"


def _template_exists(template_name: str) -> bool:
    """检查模板是否存在"""
    try:
        from flask import current_app
            # jinja2 的 get_source 会抛 TemplateNotFound
        current_app.jinja_env.get_source(None, template_name)
        return True
    except Exception:
        return False
