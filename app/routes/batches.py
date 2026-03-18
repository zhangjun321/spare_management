"""
批次管理模块路由
"""

from flask import Blueprint

batches_bp = Blueprint('batches', __name__, template_folder='../templates/batches')


@batches_bp.route('/')
def index():
    """批次列表页面"""
    return '批次管理模块 - 开发中'
