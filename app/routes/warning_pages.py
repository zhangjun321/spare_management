from flask import Blueprint, render_template
from flask_login import login_required

warning_pages_bp = Blueprint('warning_pages', __name__)


@warning_pages_bp.route('/warning-management')
@login_required
def warning_management():
    """预警管理页面"""
    return render_template('warehouse_new/warning_management.html')


# 兼容 React 侧边栏菜单的路由
@warning_pages_bp.route('/inventory-check')
@login_required
def inventory_check_redirect():
    """库存盘点页面"""
    return render_template('warehouse_new/inventory_check.html')


@warning_pages_bp.route('/old-quality-check')
@login_required
def quality_check_redirect():
    """质检管理页面（旧版 - 兼容用）"""
    return render_template('warehouse_new/quality_check.html')
