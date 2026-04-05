
"""
智能仓库管理路由 - 基于百度千帆 AI
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.services.intelligent_warehouse_service import intelligent_warehouse_service
from app.models import Warehouse
from app.extensions import db

intelligent_warehouse_bp = Blueprint('intelligent_warehouse', __name__, url_prefix='/warehouses/intelligent')


@intelligent_warehouse_bp.route('/')
@login_required
def index():
    """智能仓库管理首页"""
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('warehouses/intelligent/index.html', warehouses=warehouses or [])


@intelligent_warehouse_bp.route('/analyze/<int:warehouse_id>/')
@login_required
def analyze_warehouse(warehouse_id):
    """AI 分析仓库备件数据"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    # 调用 AI 分析
    result = intelligent_warehouse_service.analyze_spare_parts_data(warehouse_id)
    
    if result.get('success'):
        return render_template('warehouses/intelligent/analysis_result.html',
                             warehouse=warehouse,
                             analysis_result=result)
    else:
        flash('AI 分析失败：' + result.get('error', '未知错误'), 'danger')
        return redirect(url_for('intelligent_warehouse.index'))


@intelligent_warehouse_bp.route('/api/analyze/<int:warehouse_id>/', methods=['GET'])
@login_required
def api_analyze_warehouse(warehouse_id):
    """API: AI 分析仓库数据"""
    result = intelligent_warehouse_service.analyze_spare_parts_data(warehouse_id)
    return jsonify(result)


@intelligent_warehouse_bp.route('/layout/<int:warehouse_id>/')
@login_required
def generate_layout(warehouse_id):
    """AI 生成仓库布局方案"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    # 先分析备件数据
    analysis_result = intelligent_warehouse_service.analyze_spare_parts_data(warehouse_id)
    
    if not analysis_result.get('success'):
        flash('备件分析失败', 'danger')
        return redirect(url_for('intelligent_warehouse.index'))
    
    # 生成布局方案
    layout_result = intelligent_warehouse_service.generate_warehouse_layout(
        warehouse_id, 
        analysis_result
    )
    
    if layout_result.get('success'):
        return render_template('warehouses/intelligent/layout_result.html',
                             warehouse=warehouse,
                             analysis_result=analysis_result,
                             layout_result=layout_result)
    else:
        flash('布局生成失败', 'danger')
        return redirect(url_for('intelligent_warehouse.index'))


@intelligent_warehouse_bp.route('/optimize/<int:warehouse_id>/')
@login_required
def optimize_inventory(warehouse_id):
    """AI 优化库存"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    result = intelligent_warehouse_service.optimize_inventory(warehouse_id)
    
    if result.get('success'):
        return render_template('warehouses/intelligent/optimization_result.html',
                             warehouse=warehouse,
                             optimization_result=result)
    else:
        flash('库存优化失败', 'danger')
        return redirect(url_for('intelligent_warehouse.index'))


@intelligent_warehouse_bp.route('/api/optimize/<int:warehouse_id>/', methods=['GET'])
@login_required
def api_optimize_inventory(warehouse_id):
    """API: AI 优化库存"""
    result = intelligent_warehouse_service.optimize_inventory(warehouse_id)
    return jsonify(result)


@intelligent_warehouse_bp.route('/visualization/<int:warehouse_id>/')
@login_required
def visualization(warehouse_id):
    """仓库可视化看板"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    # 获取可视化数据
    viz_result = intelligent_warehouse_service.generate_visualization_report(warehouse_id)
    
    if viz_result.get('success'):
        return render_template('warehouses/intelligent/visualization.html',
                             warehouse=warehouse,
                             viz_data=viz_result['visualization'])
    else:
        flash('获取可视化数据失败', 'danger')
        return redirect(url_for('intelligent_warehouse.index'))


@intelligent_warehouse_bp.route('/api/visualization/<int:warehouse_id>/', methods=['GET'])
@login_required
def api_visualization(warehouse_id):
    """API: 获取可视化数据"""
    result = intelligent_warehouse_service.generate_visualization_report(warehouse_id)
    return jsonify(result)


@intelligent_warehouse_bp.route('/smart-assignment/<int:warehouse_id>/', methods=['GET', 'POST'])
@login_required
def smart_assignment(warehouse_id):
    """智能库位分配"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    if request.method == 'POST':
        # TODO: 实现智能库位分配逻辑
        flash('智能库位分配功能开发中', 'info')
        return redirect(url_for('intelligent_warehouse.visualization', warehouse_id=warehouse_id))
    
    return render_template('warehouses/intelligent/smart_assignment.html',
                         warehouse=warehouse)

