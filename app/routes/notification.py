"""
通知模块路由
"""

from flask import Blueprint

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/')
def index():
    return "通知管理 - 开发中"
