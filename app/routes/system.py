"""
系统管理模块路由
"""

from flask import Blueprint

system_bp = Blueprint('system', __name__)

@system_bp.route('/')
def index():
    return "系统管理 - 开发中"
