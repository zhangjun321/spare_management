"""
API 接口模块路由
"""

from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'message': '系统运行正常'})
