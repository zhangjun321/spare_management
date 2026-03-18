"""
交易管理模块路由
"""

from flask import Blueprint

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/')
def index():
    return "交易管理 - 开发中"
