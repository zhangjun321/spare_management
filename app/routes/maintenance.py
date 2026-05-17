"""
维修管理模块路由
"""

from flask import Blueprint, render_template
from app.models import MaintenanceOrder
from flask_login import login_required

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/')
@login_required
def index():
    """维修工单列表"""
    orders = MaintenanceOrder.query.order_by(MaintenanceOrder.created_at.desc()).all()
    return render_template('maintenance/index.html', orders=orders)

@maintenance_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    """维修工单详情"""
    order = MaintenanceOrder.query.get_or_404(order_id)
    return render_template('maintenance/detail.html', order=order)
