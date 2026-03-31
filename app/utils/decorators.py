# -*- coding: utf-8 -*-
"""
装饰器模块 - 重写版本
"""

from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user


def is_api_request():
    """判断是否是 API 请求"""
    # 检查路径是否包含 /api/ 或者 Accept 头是否包含 application/json
    return '/api/' in request.path or 'application/json' in request.headers.get('Accept', '')


def permission_required(module, action):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否登录
            if not current_user.is_authenticated:
                if is_api_request():
                    return jsonify({
                        'status': 'error',
                        'message': '请先登录'
                    }), 401
                flash('请先登录以访问此页面', 'warning')
                return redirect(url_for('auth.login'))
            
            # 管理员拥有所有权限
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # 检查权限
            if current_user.has_permission(module, action):
                return f(*args, **kwargs)
            
            # 权限不足
            if is_api_request():
                return jsonify({
                    'status': 'error',
                    'message': '您没有权限执行此操作'
                }), 403
            flash('您没有权限访问此页面', 'danger')
            abort(403)
        
        return decorated_function
    return decorator


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if is_api_request():
                return jsonify({
                    'status': 'error',
                    'message': '请先登录'
                }), 401
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            if is_api_request():
                return jsonify({
                    'status': 'error',
                    'message': '您需要管理员权限才能执行此操作'
                }), 403
            flash('您需要管理员权限才能访问此页面', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function
