"""
仓库管理模块路由
"""

from flask import Blueprint

warehouses_bp = Blueprint('warehouses', __name__)

@warehouses_bp.route('/')
def index():
    return "仓库管理 - 开发中"
