"""
库存并发控制 API 路由
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from decimal import Decimal
from app.services.warehouse_v3.inventory_concurrency_service import (
    InventoryConcurrencyService,
    ConcurrencyError,
    InsufficientStockError
)

inventory_concurrency_bp = Blueprint('inventory_concurrency', __name__, url_prefix='/api/inventory/concurrency')


@inventory_concurrency_bp.route('/<int:inventory_id>/decrease', methods=['POST'])
@login_required
def decrease_stock(inventory_id):
    """
    扣减库存（乐观锁）
    
    Request Body:
    {
        "quantity": 10,
        "reason": "出库"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({
                'success': False,
                'message': '缺少数量参数'
            }), 400
        
        quantity = Decimal(str(data['quantity']))
        reason = data.get('reason', '')
        
        success, message, inventory = InventoryConcurrencyService.decrease_stock_with_optimistic_lock(
            inventory_id,
            quantity,
            current_user.id,
            reason
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'inventory_id': inventory.id,
                    'quantity': float(inventory.quantity),
                    'available_quantity': float(inventory.available_quantity),
                    'locked_quantity': float(inventory.locked_quantity),
                    'version': inventory.version
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_concurrency_bp.route('/<int:inventory_id>/increase', methods=['POST'])
@login_required
def increase_stock(inventory_id):
    """
    增加库存（乐观锁）
    
    Request Body:
    {
        "quantity": 10,
        "reason": "入库"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({
                'success': False,
                'message': '缺少数量参数'
            }), 400
        
        quantity = Decimal(str(data['quantity']))
        reason = data.get('reason', '')
        
        success, message, inventory = InventoryConcurrencyService.increase_stock_with_optimistic_lock(
            inventory_id,
            quantity,
            current_user.id,
            reason
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'inventory_id': inventory.id,
                    'quantity': float(inventory.quantity),
                    'available_quantity': float(inventory.available_quantity),
                    'locked_quantity': float(inventory.locked_quantity),
                    'version': inventory.version
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_concurrency_bp.route('/<int:inventory_id>/lock', methods=['POST'])
@login_required
def lock_stock(inventory_id):
    """
    锁定库存
    
    Request Body:
    {
        "quantity": 10
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({
                'success': False,
                'message': '缺少数量参数'
            }), 400
        
        quantity = Decimal(str(data['quantity']))
        
        success, message = InventoryConcurrencyService.lock_stock(
            inventory_id,
            quantity,
            current_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_concurrency_bp.route('/<int:inventory_id>/unlock', methods=['POST'])
@login_required
def unlock_stock(inventory_id):
    """
    解锁库存
    
    Request Body:
    {
        "quantity": 10
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'quantity' not in data:
            return jsonify({
                'success': False,
                'message': '缺少数量参数'
            }), 400
        
        quantity = Decimal(str(data['quantity']))
        
        success, message = InventoryConcurrencyService.unlock_stock(
            inventory_id,
            quantity,
            current_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_concurrency_bp.route('/transfer', methods=['POST'])
@login_required
def transfer_stock():
    """
    库存调拨
    
    Request Body:
    {
        "from_inventory_id": 1,
        "to_inventory_id": 2,
        "quantity": 10
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['from_inventory_id', 'to_inventory_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        from_inventory_id = data['from_inventory_id']
        to_inventory_id = data['to_inventory_id']
        quantity = Decimal(str(data['quantity']))
        
        success, message = InventoryConcurrencyService.transfer_stock(
            from_inventory_id,
            to_inventory_id,
            quantity,
            current_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_concurrency_bp.route('/batch/lock', methods=['POST'])
@login_required
def lock_batch_stock():
    """
    批量锁定库存（先进先出）
    
    Request Body:
    {
        "warehouse_id": 1,
        "part_id": 100,
        "quantity": 50,
        "fifo": true
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['warehouse_id', 'part_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段：{field}'
                }), 400
        
        warehouse_id = data['warehouse_id']
        part_id = data['part_id']
        quantity = Decimal(str(data['quantity']))
        fifo = data.get('fifo', True)
        
        success, message, locked = InventoryConcurrencyService.check_and_lock_batch(
            warehouse_id,
            part_id,
            quantity,
            fifo
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'locked_inventories': locked,
                    'total_quantity': float(quantity)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@inventory_concurrency_bp.route('/<int:inventory_id>/status', methods=['GET'])
@login_required
def get_stock_status(inventory_id):
    """获取库存状态"""
    try:
        status = InventoryConcurrencyService.get_stock_status(inventory_id)
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
