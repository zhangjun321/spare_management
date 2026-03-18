"""
维修管理模块路由
"""

from flask import Blueprint

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/')
def index():
    return "维修管理 - 开发中"
