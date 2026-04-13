"""
新的仓库管理模块前端页面路由
"""

from flask import Blueprint, render_template, request, jsonify, make_response
from flask_login import login_required, current_user

# 创建蓝图
warehouse_new_pages_bp = Blueprint('warehouse_new_pages', __name__, url_prefix='/warehouse')


def add_no_cache_headers(response):
    """添加禁止缓存的响应头"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@warehouse_new_pages_bp.route('/dashboard')
@login_required
def dashboard():
    """智能仓库驾驶舱页面"""
    response = make_response(render_template('warehouse_new/dashboard.html'))
    return add_no_cache_headers(response)


@warehouse_new_pages_bp.route('/inbound')
@login_required
def inbound_list():
    """入库管理列表页面"""
    return render_template('warehouse_new/inbound_list.html')


@warehouse_new_pages_bp.route('/inbound/<int:order_id>/complete')
@login_required
def inbound_complete(order_id):
    """入库完成页面"""
    return render_template('warehouse_new/inbound_complete.html', order_id=order_id)


@warehouse_new_pages_bp.route('/outbound')
@login_required
def outbound_list():
    """出库管理列表页面"""
    return render_template('warehouse_new/outbound_list.html')


@warehouse_new_pages_bp.route('/outbound/<int:order_id>/complete')
@login_required
def outbound_complete(order_id):
    """出库完成页面"""
    return render_template('warehouse_new/outbound_complete.html', order_id=order_id)


@warehouse_new_pages_bp.route('/inventory')
@login_required
def inventory_list():
    """库存管理列表页面"""
    return render_template('warehouse_new/inventory_list.html')


@warehouse_new_pages_bp.route('/analysis')
@login_required
def analysis():
    """AI 分析页面"""
    return render_template('warehouse_new/analysis.html')


@warehouse_new_pages_bp.route('/transaction-logs')
@login_required
def transaction_logs():
    """库存变动日志页面"""
    return render_template('warehouse_new/transaction_logs.html')


@warehouse_new_pages_bp.route('/test')
@login_required
def test():
    """测试页面"""
    return render_template('warehouse_new/test.html')
