"""
库存盘点路由
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.warehouse_v3.inventory_check import InventoryCheck, InventoryCheckItem
from app.models.warehouse_v3.inventory import InventoryV3
from app.models.warehouse_v3.warehouse import WarehouseV3
from app.models.spare_part import SparePart
from app.utils.decorators import permission_required
from datetime import datetime

inventory_check_bp = Blueprint('inventory_check', __name__, url_prefix='/api/inventory-check')


@inventory_check_bp.route('/checks', methods=['GET'])
@login_required
@permission_required('inventory_check', 'read')
def get_checks():
    """获取盘点单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        status = request.args.get('status', type=str)
        
        query = InventoryCheck.query
        
        if warehouse_id:
            query = query.filter(InventoryCheck.warehouse_id == warehouse_id)
        if status:
            query = query.filter(InventoryCheck.status == status)
        
        query = query.order_by(InventoryCheck.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        checks = [{
            **check.to_dict(),
            'progress': f"{check.checked_items}/{check.total_items}" if check.total_items > 0 else "0/0"
        } for check in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': checks,
                'total': pagination.total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        current_app.logger.error(f'获取盘点单列表失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_check_bp.route('/checks', methods=['POST'])
@login_required
@permission_required('inventory_check', 'create')
def create_check():
    """创建盘点单"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['warehouse_id', 'check_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'缺少必填字段：{field}'}), 400
        
        # 创建盘点单
        check = InventoryCheck(
            check_no=InventoryCheck.generate_check_no(),
            warehouse_id=data['warehouse_id'],
            check_type=data['check_type'],
            status='planned',
            planned_date=datetime.strptime(data['planned_date'], '%Y-%m-%d').date() if data.get('planned_date') else None,
            notes=data.get('notes'),
            created_by=current_user.id
        )
        
        db.session.add(check)
        db.session.flush()
        
        # 如果是立即盘点，自动生成盘点明细
        if data.get('auto_generate_items'):
            # 获取该仓库的所有库存
            inventories = InventoryV3.query.filter_by(warehouse_id=data['warehouse_id']).all()
            
            for inv in inventories:
                item = InventoryCheckItem(
                    check_id=check.id,
                    inventory_id=inv.id,
                    part_id=inv.part_id,
                    location_id=inv.location_id,
                    system_quantity=inv.quantity,
                    status='pending'
                )
                db.session.add(item)
            
            # 更新汇总信息
            check.total_items = len(inventories)
            check.status = 'in_progress'
            check.start_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '盘点单创建成功',
            'data': check.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建盘点单失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_check_bp.route('/checks/<int:check_id>', methods=['GET'])
@login_required
@permission_required('inventory_check', 'read')
def get_check_detail(check_id):
    """获取盘点单详情"""
    try:
        check = InventoryCheck.query.get_or_404(check_id)
        
        return jsonify({
            'success': True,
            'data': check.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f'获取盘点单详情失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_check_bp.route('/checks/<int:check_id>/items', methods=['GET'])
@login_required
@permission_required('inventory_check', 'read')
def get_check_items(check_id):
    """获取盘点明细列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        query = InventoryCheckItem.query.filter_by(check_id=check_id)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [item.to_dict() for item in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': pagination.total,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        current_app.logger.error(f'获取盘点明细失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_check_bp.route('/checks/<int:check_id>/items/<int:item_id>', methods=['POST'])
@login_required
@permission_required('inventory_check', 'execute')
def submit_check_item(check_id, item_id):
    """提交盘点明细"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if 'actual_quantity' not in data:
            return jsonify({'success': False, 'message': '缺少实际数量'}), 400
        
        # 获取盘点明细
        item = InventoryCheckItem.query.get_or_404(item_id)
        
        if item.check_id != check_id:
            return jsonify({'success': False, 'message': '盘点明细不匹配'}), 400
        
        # 更新盘点数据
        item.actual_quantity = data['actual_quantity']
        item.difference_reason = data.get('difference_reason')
        item.calculate_difference()
        item.checked_at = datetime.utcnow()
        item.checked_by = current_user.id
        
        # 更新盘点单进度
        check = InventoryCheck.query.get(check_id)
        if check:
            checked_count = InventoryCheckItem.query.filter_by(
                check_id=check_id,
                status='confirmed'
            ).count()
            difference_count = InventoryCheckItem.query.filter_by(
                check_id=check_id,
                status='difference'
            ).count()
            
            check.checked_items = checked_count + difference_count
            check.difference_items = difference_count
            
            # 如果所有明细都已盘点，自动完成盘点单
            if check.checked_items >= check.total_items:
                check.status = 'completed'
                check.end_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '盘点数据提交成功',
            'data': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'提交盘点明细失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_check_bp.route('/checks/<int:check_id>/process-differences', methods=['POST'])
@login_required
@permission_required('inventory_check', 'execute')
def process_differences(check_id):
    """处理盘点差异"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'adjust' 调整库存，'ignore' 忽略
        
        check = InventoryCheck.query.get_or_404(check_id)
        
        # 获取所有有差异的明细
        diff_items = InventoryCheckItem.query.filter_by(
            check_id=check_id,
            status='difference'
        ).all()
        
        if action == 'adjust':
            # 调整库存
            for item in diff_items:
                if item.inventory_id:
                    inventory = InventoryV3.query.get(item.inventory_id)
                    if inventory:
                        # 更新库存数量
                        inventory.quantity = item.actual_quantity
                        inventory.available_quantity = inventory.quantity - inventory.locked_quantity
            
            check.status = 'adjusted'
            check.notes = (check.notes or '') + f'\n{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} - 已调整库存，处理人：{current_user.name}'
        
        elif action == 'ignore':
            # 忽略差异
            for item in diff_items:
                item.status = 'confirmed'
            
            check.status = 'completed'
            check.notes = (check.notes or '') + f'\n{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} - 已忽略差异，处理人：{current_user.name}'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '盘点差异处理成功'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'处理盘点差异失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@inventory_check_bp.route('/checks/<int:check_id>/cancel', methods=['POST'])
@login_required
@permission_required('inventory_check', 'delete')
def cancel_check(check_id):
    """取消盘点单"""
    try:
        check = InventoryCheck.query.get_or_404(check_id)
        
        if check.status not in ['planned', 'in_progress']:
            return jsonify({'success': False, 'message': '当前状态无法取消'}), 400
        
        check.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '盘点单已取消'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'取消盘点单失败：{str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500
