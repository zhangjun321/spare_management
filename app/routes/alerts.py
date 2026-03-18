"""
告警管理模块路由
"""

from flask import Blueprint

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/')
def index():
    return "告警管理 - 开发中"
