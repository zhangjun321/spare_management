"""
出库路由 V3 - 占位符
"""

from flask import request, jsonify, current_app
from flask_login import login_required
from app.routes.warehouse_v3 import warehouse_v3_bp


@warehouse_v3_bp.route('/outbound-orders', methods=['GET'])
@login_required
def get_outbound_orders():
    """获取出库单列表"""
    return jsonify({
        'success': True,
        'data': [],
        'message': '出库功能开发中'
    })
