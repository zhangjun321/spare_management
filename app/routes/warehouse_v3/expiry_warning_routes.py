"""
效期预警 API 路由
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.warehouse_v3.expiry_warning_service import ExpiryWarningService

expiry_warning_bp = Blueprint('expiry_warning', __name__, url_prefix='/api/expiry-warning')


@expiry_warning_bp.route('/warnings', methods=['GET'])
@login_required
def get_warnings():
    """获取近效期预警"""
    try:
        days_threshold = request.args.get('days_threshold', 30, type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        warnings = ExpiryWarningService.get_expiry_warnings(
            days_threshold=days_threshold,
            warehouse_id=warehouse_id
        )
        
        return jsonify({
            'success': True,
            'data': {
                'warnings': warnings,
                'total': len(warnings),
                'threshold_days': days_threshold
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@expiry_warning_bp.route('/expired', methods=['GET'])
@login_required
def get_expired():
    """获取已过期库存"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        expired = ExpiryWarningService.get_expired_inventory(warehouse_id=warehouse_id)
        
        return jsonify({
            'success': True,
            'data': {
                'expired': expired,
                'total': len(expired)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@expiry_warning_bp.route('/statistics', methods=['GET'])
@login_required
def get_statistics():
    """获取效期统计"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        stats = ExpiryWarningService.get_expiry_statistics(warehouse_id=warehouse_id)
        
        return jsonify({
            'success': True,
            'data': {
                'statistics': stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@expiry_warning_bp.route('/lock', methods=['POST'])
@login_required
def lock_inventory():
    """锁定近效期库存"""
    try:
        data = request.get_json()
        inventory_id = data.get('inventory_id')
        days_threshold = data.get('days_threshold', 7)
        
        if not inventory_id:
            return jsonify({
                'success': False,
                'message': '请提供库存 ID'
            }), 400
        
        success, message = ExpiryWarningService.lock_near_expiry_inventory(
            inventory_id=inventory_id,
            days_threshold=days_threshold
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@expiry_warning_bp.route('/report', methods=['GET'])
@login_required
def get_report():
    """生成效期预警报告"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        report = ExpiryWarningService.generate_expiry_report(warehouse_id=warehouse_id)
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
