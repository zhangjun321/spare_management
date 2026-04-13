"""
仓库管理 V3 前端页面路由
"""

from flask import render_template, Blueprint

warehouse_v3_pages_bp = Blueprint('warehouse_v3_pages', __name__, url_prefix='/warehouse-v3')


@warehouse_v3_pages_bp.route('/')
def index():
    """V3 管理页面"""
    return render_template('warehouse_v3/index.html')
