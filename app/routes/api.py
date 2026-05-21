"""
API 接口模块路由
"""

from flask import Blueprint
from app.utils.response import ok

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health_check():
    """健康检查接口"""
    return ok(data={'status': 'healthy'}, message='系统运行正常')
