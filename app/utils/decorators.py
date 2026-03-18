"""
装饰器模块
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(module, action):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否登录
            if not current_user.is_authenticated:
                flash('请先登录以访问此页面', 'warning')
                return redirect(url_for('auth.login'))
            
            # 管理员拥有所有权限
            if current_user.is_admin:
                return f(*args, **kwargs)
            
            # 检查权限
            if current_user.has_permission(module, action):
                return f(*args, **kwargs)
            
            # 权限不足
            flash('您没有权限访问此页面', 'danger')
            abort(403)
        
        return decorated_function
    return decorator


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('您需要管理员权限才能访问此页面', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function
