"""
错误处理模块 - 重写版本
"""

from flask import render_template, Blueprint, request, jsonify

errors_bp = Blueprint('errors', __name__)


def is_api_request():
    """判断是否是 API 请求"""
    # 检查路径是否包含 /api/、/ai-image/ 或者 Accept 头是否包含 application/json
    return '/api/' in request.path or '/ai-image/' in request.path or '/test/' in request.path or 'application/json' in request.headers.get('Accept', '')


@errors_bp.app_errorhandler(400)
def bad_request(error):
    if is_api_request():
        return jsonify({
            'status': 'error',
            'message': '请求无效，请检查您的输入'
        }), 400
    return render_template('errors/400.html'), 400


@errors_bp.app_errorhandler(401)
def unauthorized(error):
    if is_api_request():
        return jsonify({
            'status': 'error',
            'message': '请先登录'
        }), 401
    return render_template('errors/401.html'), 401


@errors_bp.app_errorhandler(403)
def forbidden(error):
    if is_api_request():
        return jsonify({
            'status': 'error',
            'message': '您没有权限执行此操作'
        }), 403
    return render_template('errors/403.html'), 403


@errors_bp.app_errorhandler(404)
def not_found(error):
    if is_api_request():
        return jsonify({
            'status': 'error',
            'message': '请求的资源不存在'
        }), 404
    return render_template('errors/404.html'), 404


@errors_bp.app_errorhandler(500)
def internal_server_error(error):
    if is_api_request():
        return jsonify({
            'status': 'error',
            'message': '服务器内部错误，请稍后重试'
        }), 500
    return render_template('errors/500.html'), 500
