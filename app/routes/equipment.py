"""
设备管理模块路由
"""

from flask import Blueprint

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/')
def index():
    return "设备管理 - 开发中"
