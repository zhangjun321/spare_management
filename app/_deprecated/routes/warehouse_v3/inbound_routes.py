"""
入库路由 V3 - 占位符
"""

from flask import request, jsonify, current_app
from flask_login import login_required
from app.routes.warehouse_v3 import warehouse_v3_bp


@warehouse_v3_bp.route('/inbound-orders', methods=['GET'])
@login_required
def get_inbound_orders():
    """获取入库单列表"""
    return jsonify({
        'success': True,
        'data': [],
        'message': '入库功能开发中'
    })
