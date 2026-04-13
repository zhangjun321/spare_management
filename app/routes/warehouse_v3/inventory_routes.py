"""
库存路由 V3
"""

from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from app.routes.warehouse_v3 import warehouse_v3_bp
from app.services.warehouse_v3.inventory_service import InventoryV3Service


@warehouse_v3_bp.route('/inventory', methods=['GET'])
@login_required
def get_inventory():
    """获取库存列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        filters = {
            'part_id': request.args.get('part_id', type=int),
            'status': request.args.get('status'),
            'abc_class': request.args.get('abc_class')
        }
        
        result = InventoryV3Service.get_inventory_list(warehouse_id, page, per_page, filters)
        
        return jsonify({
            'success': True,
            'data': {
                'inventories': [inv.to_dict() for inv in result['items']],
                'total': result['total'],
                'page': result['page'],
                'pages': result['pages']
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取库存列表失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/inventory/summary/<int:warehouse_id>', methods=['GET'])
@login_required
def get_inventory_summary(warehouse_id):
    """获取库存汇总"""
    try:
        summary = InventoryV3Service.get_inventory_summary(warehouse_id)
        
        if not summary:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        current_app.logger.error(f"获取库存汇总失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/inventory/adjust/<int:inventory_id>', methods=['POST'])
@login_required
def adjust_inventory(inventory_id):
    """调整库存"""
    try:
        data = request.get_json()
        
        if not data or 'type' not in data or 'quantity' not in data:
            return jsonify({
                'success': False,
                'error': '调整类型和数量必填'
            }), 400
        
        success = InventoryV3Service.adjust_inventory(inventory_id, data, current_user.id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '库存调整成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '库存不存在'
            }), 404
    except Exception as e:
        current_app.logger.error(f"调整库存失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/inventory/warnings', methods=['GET'])
@login_required
def get_inventory_warnings():
    """获取库存预警"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        warnings = InventoryV3Service.get_inventory_warnings(warehouse_id)
        
        return jsonify({
            'success': True,
            'data': warnings
        })
    except Exception as e:
        current_app.logger.error(f"获取库存预警失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
