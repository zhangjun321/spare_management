"""
仓库可视化路由
包含：平面图、热力图、动画展示
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.services.visualization_service import warehouse_visualization_service
from app.models.warehouse import Warehouse

visualization_bp = Blueprint('visualization', __name__, url_prefix='/visualization')


@visualization_bp.route('/')
@login_required
def index():
    """可视化首页"""
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('visualization/index.html', warehouses=warehouses)


@visualization_bp.route('/warehouse/<int:warehouse_id>/')
@login_required
def warehouse_layout(warehouse_id):
    """仓库平面图"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    return render_template('visualization/warehouse_layout.html', warehouse=warehouse)


@visualization_bp.route('/warehouse/<int:warehouse_id>/data/')
@login_required
def get_warehouse_layout_data(warehouse_id):
    """获取仓库布局数据（API）"""
    data = warehouse_visualization_service.get_warehouse_layout(warehouse_id)
    return jsonify(data)


@visualization_bp.route('/warehouse/<int:warehouse_id>/heatmap/')
@login_required
def warehouse_heatmap(warehouse_id):
    """仓库热力图"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    dimension = request.args.get('dimension', 'density')
    return render_template('visualization/heatmap.html', 
                         warehouse=warehouse, 
                         dimension=dimension)


@visualization_bp.route('/warehouse/<int:warehouse_id>/heatmap-data/')
@login_required
def get_heatmap_data(warehouse_id):
    """获取热力图数据（API）"""
    dimension = request.args.get('dimension', 'density')
    data = warehouse_visualization_service.get_heatmap_data(warehouse_id, dimension)
    return jsonify(data)


@visualization_bp.route('/inbound/<int:order_id>/animation/')
@login_required
def inbound_animation(order_id):
    """入库动画展示"""
    from app.models.inventory import InboundOrder
    order = InboundOrder.query.get_or_404(order_id)
    return render_template('visualization/inbound_animation.html', order=order)


@visualization_bp.route('/inbound/<int:order_id>/animation-data/')
@login_required
def get_inbound_animation_data(order_id):
    """获取入库动画数据（API）"""
    data = warehouse_visualization_service.get_inbound_animation_data(order_id)
    return jsonify(data)


@visualization_bp.route('/warehouse/<int:warehouse_id>/status/')
@login_required
def warehouse_status(warehouse_id):
    """仓库库存状态"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    data = warehouse_visualization_service.get_inventory_status(warehouse_id)
    return jsonify(data)
