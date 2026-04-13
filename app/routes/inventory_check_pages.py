"""
库存盘点页面路由
"""

from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.decorators import permission_required

inventory_check_pages_bp = Blueprint('inventory_check_pages', __name__)


@inventory_check_pages_bp.route('/inventory-check')
@login_required
def inventory_check_list():
    """库存盘点列表页面"""
    return render_template('warehouse_new/inventory_check.html')
