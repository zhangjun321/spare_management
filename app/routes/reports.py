"""
报表统计模块路由
"""

from flask import Blueprint

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
def index():
    return "报表统计 - 开发中"
