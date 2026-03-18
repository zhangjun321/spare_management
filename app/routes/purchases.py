"""
采购管理模块路由
"""

from flask import Blueprint

purchases_bp = Blueprint('purchases', __name__)

@purchases_bp.route('/')
def index():
    return "采购管理 - 开发中"
