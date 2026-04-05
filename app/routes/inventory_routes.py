"""
库存管理路由 - 入库、出库、库存查询
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.inventory import (
    InboundOrder, OutboundOrder, InventoryRecord, OperationLog
)
from app.models.warehouse import Warehouse
from app.models.spare_part import SparePart
from app.services.inbound_service import inbound_service
from app.services.outbound_service import outbound_service

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


# ==================== 入库管理路由 ====================

@inventory_bp.route('/inbound/')
@login_required
def inbound_list():
    """入库单列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 筛选条件
    order_type = request.args.get('type')
    status = request.args.get('status')
    
    query = InboundOrder.query
    
    if order_type:
        query = query.filter_by(type=order_type)
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(InboundOrder.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('inventory/inbound_list.html', pagination=pagination)


@inventory_bp.route('/inbound/create/', methods=['GET', 'POST'])
@login_required
def inbound_create():
    """创建入库单"""
    if request.method == 'POST':
        # 获取表单数据
        warehouse_id = request.form.get('warehouse_id', type=int)
        spare_part_ids = request.form.getlist('spare_part_id', type=int)
        quantities = request.form.getlist('quantity', type=int)
        
        if not warehouse_id or not spare_part_ids:
            flash('请填写完整的入库信息', 'danger')
            return redirect(url_for('inventory.inbound_create'))
        
        # 创建入库单
        order = inbound_service.create_order(
            warehouse_id=warehouse_id,
            spare_part_ids=spare_part_ids,
            quantities=quantities,
            type=request.form.get('type', 'purchase'),
            supplier_id=request.form.get('supplier_id', type=int),
            created_by=current_user.id
        )
        
        flash(f'入库单 {order.order_number} 创建成功', 'success')
        return redirect(url_for('inventory.inbound_detail', order_id=order.id))
    
    # GET 请求显示表单
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    spare_parts = SparePart.query.filter_by(is_active=True).limit(100).all()
    
    return render_template('inventory/inbound_form.html', 
                         warehouses=warehouses, 
                         spare_parts=spare_parts)


@inventory_bp.route('/inbound/<int:order_id>/')
@login_required
def inbound_detail(order_id):
    """入库单详情"""
    order = InboundOrder.query.get_or_404(order_id)
    return render_template('inventory/inbound_detail.html', order=order)


@inventory_bp.route('/inbound/<int:order_id>/ai-recommend/', methods=['POST'])
@login_required
def inbound_ai_recommend(order_id):
    """AI 推荐库位"""
    result = inbound_service.ai_recommend_locations(order_id)
    
    if result.get('success'):
        flash('AI 库位推荐完成', 'success')
    else:
        flash(f'AI 推荐失败：{result.get("error")}', 'danger')
    
    return jsonify(result)


@inventory_bp.route('/inbound/<int:order_id>/execute/', methods=['POST'])
@login_required
def inbound_execute(order_id):
    """执行入库"""
    result = inbound_service.execute_inbound(order_id, current_user.id)
    
    if result.get('success'):
        flash(f'入库完成，成功{len(result.get("success_items", []))}项，失败{len(result.get("failed_items", []))}项', 'success')
    else:
        flash(f'入库失败：{result.get("error")}', 'danger')
    
    return jsonify(result)


@inventory_bp.route('/inbound/<int:order_id>/rollback/', methods=['POST'])
@login_required
def inbound_rollback(order_id):
    """撤销入库"""
    result = inbound_service.rollback_inbound(order_id, current_user.id)
    
    if result.get('success'):
        flash('入库已撤销', 'success')
    else:
        flash(f'撤销失败：{result.get("error")}', 'danger')
    
    return jsonify(result)


# ==================== 出库管理路由 ====================

@inventory_bp.route('/outbound/')
@login_required
def outbound_list():
    """出库单列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 筛选条件
    order_type = request.args.get('type')
    status = request.args.get('status')
    
    query = OutboundOrder.query
    
    if order_type:
        query = query.filter_by(type=order_type)
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(OutboundOrder.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('inventory/outbound_list.html', pagination=pagination)


@inventory_bp.route('/outbound/create/', methods=['GET', 'POST'])
@login_required
def outbound_create():
    """创建出库单"""
    if request.method == 'POST':
        # 获取表单数据
        warehouse_id = request.form.get('warehouse_id', type=int)
        spare_part_items = []
        
        # 解析备件和数量
        spare_part_ids = request.form.getlist('spare_part_id', type=int)
        quantities = request.form.getlist('quantity', type=int)
        
        for sp_id, qty in zip(spare_part_ids, quantities):
            if sp_id and qty > 0:
                spare_part_items.append((sp_id, qty))
        
        if not warehouse_id or not spare_part_items:
            flash('请填写完整的出库信息', 'danger')
            return redirect(url_for('inventory.outbound_create'))
        
        # 检查库存
        check_result = outbound_service.check_inventory(warehouse_id, spare_part_items)
        if not check_result.get('success'):
            flash('库存不足，无法创建出库单', 'warning')
            # 可以显示详细的库存信息
        
        # 创建出库单
        order = outbound_service.create_order(
            warehouse_id=warehouse_id,
            spare_part_items=spare_part_items,
            type=request.form.get('type', 'requisition'),
            strategy=request.form.get('strategy', 'fifo'),
            requester_id=request.form.get('requester_id', type=int),
            department=request.form.get('department'),
            purpose=request.form.get('purpose'),
            created_by=current_user.id
        )
        
        flash(f'出库单 {order.order_number} 创建成功', 'success')
        return redirect(url_for('inventory.outbound_detail', order_id=order.id))
    
    # GET 请求显示表单
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    spare_parts = SparePart.query.filter_by(is_active=True).limit(100).all()
    
    return render_template('inventory/outbound_form.html',
                         warehouses=warehouses,
                         spare_parts=spare_parts)


@inventory_bp.route('/outbound/<int:order_id>/')
@login_required
def outbound_detail(order_id):
    """出库单详情"""
    order = OutboundOrder.query.get_or_404(order_id)
    return render_template('inventory/outbound_detail.html', order=order)


@inventory_bp.route('/outbound/<int:order_id>/allocate/', methods=['POST'])
@login_required
def outbound_allocate(order_id):
    """分配出库库位"""
    result = outbound_service.allocate_locations(order_id)
    
    if result.get('success'):
        flash('库位分配完成', 'success')
    else:
        flash(f'分配失败：{result.get("error")}', 'danger')
    
    return jsonify(result)


@inventory_bp.route('/outbound/<int:order_id>/execute/', methods=['POST'])
@login_required
def outbound_execute(order_id):
    """执行出库"""
    result = outbound_service.execute_outbound(order_id, current_user.id)
    
    if result.get('success'):
        flash(f'出库完成，成功{len(result.get("success_items", []))}项，失败{len(result.get("failed_items", []))}项', 'success')
    else:
        flash(f'出库失败：{result.get("error")}', 'danger')
    
    return jsonify(result)


@inventory_bp.route('/outbound/<int:order_id>/rollback/', methods=['POST'])
@login_required
def outbound_rollback(order_id):
    """撤销出库"""
    result = outbound_service.rollback_outbound(order_id, current_user.id)
    
    if result.get('success'):
        flash('出库已撤销', 'success')
    else:
        flash(f'撤销失败：{result.get("error")}', 'danger')
    
    return jsonify(result)


# ==================== 库存查询路由 ====================

@inventory_bp.route('/stock/')
@login_required
def stock_list():
    """库存列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 筛选条件
    warehouse_id = request.args.get('warehouse_id', type=int)
    spare_part_id = request.args.get('spare_part_id', type=int)
    status = request.args.get('status')
    
    query = InventoryRecord.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if spare_part_id:
        query = query.filter_by(spare_part_id=spare_part_id)
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(InventoryRecord.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    spare_parts = SparePart.query.filter_by(is_active=True).limit(100).all()
    
    return render_template('inventory/stock_list.html',
                         pagination=pagination,
                         warehouses=warehouses,
                         spare_parts=spare_parts,
                         filters=request.args)


@inventory_bp.route('/stock/<int:record_id>/')
@login_required
def stock_detail(record_id):
    """库存详情"""
    record = InventoryRecord.query.get_or_404(record_id)
    return render_template('inventory/stock_detail.html', record=record)


# ==================== API 接口 ====================

@inventory_bp.route('/api/inbound/check-inventory/', methods=['POST'])
@login_required
def api_check_inbound_inventory():
    """API: 检查入库库存"""
    data = request.get_json()
    warehouse_id = data.get('warehouse_id')
    spare_part_id = data.get('spare_part_id')
    
    # 查询当前库存
    inventory = InventoryRecord.query.filter_by(
        warehouse_id=warehouse_id,
        spare_part_id=spare_part_id
    ).all()
    
    total_quantity = sum(record.quantity for record in inventory)
    
    return jsonify({
        'success': True,
        'total_quantity': total_quantity,
        'records': [record.to_dict() for record in inventory]
    })


@inventory_bp.route('/api/outbound/check-stock/', methods=['POST'])
@login_required
def api_check_outbound_stock():
    """API: 检查出库库存"""
    data = request.get_json()
    warehouse_id = data.get('warehouse_id')
    items = data.get('items', [])  # [(spare_part_id, quantity), ...]
    
    spare_part_items = [(item['spare_part_id'], item['quantity']) for item in items]
    result = outbound_service.check_inventory(warehouse_id, spare_part_items)
    
    return jsonify(result)


@inventory_bp.route('/api/operation-logs/')
@login_required
def api_operation_logs():
    """API: 查询操作日志"""
    order_type = request.args.get('order_type')
    order_id = request.args.get('order_id', type=int)
    
    query = OperationLog.query
    
    if order_type:
        query = query.filter_by(order_type=order_type)
    if order_id:
        query = query.filter_by(order_id=order_id)
    
    query = query.order_by(OperationLog.created_at.desc()).limit(100)
    logs = query.all()
    
    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs]
    })
