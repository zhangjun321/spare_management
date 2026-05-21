"""
货位路由 V3
"""

from flask import request, jsonify, current_app
from flask_login import login_required
from app.routes.warehouse_v3 import warehouse_v3_bp
from app.services.warehouse_v3.location_service import LocationV3Service


@warehouse_v3_bp.route('/locations', methods=['GET'])
@login_required
def get_locations():
    """获取货位列表"""
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        if not warehouse_id:
            return jsonify({
                'success': False,
                'error': '请提供仓库 ID'
            }), 400
        
        filters = {
            'type': request.args.get('type'),
            'size_type': request.args.get('size_type'),
            'zone_code': request.args.get('zone_code')
        }
        
        locations = LocationV3Service.get_available_locations(warehouse_id, filters)
        
        return jsonify({
            'success': True,
            'data': [loc.to_dict() for loc in locations]
        })
    except Exception as e:
        current_app.logger.error(f"获取货位列表失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/locations', methods=['POST'])
@login_required
def create_location():
    """创建货位"""
    try:
        data = request.get_json()
        
        if not data or not data.get('warehouse_id') or not data.get('code'):
            return jsonify({
                'success': False,
                'error': '仓库 ID 和货位编码必填'
            }), 400
        
        location = LocationV3Service.create_location(data)
        
        return jsonify({
            'success': True,
            'data': location.to_dict(),
            'message': '货位创建成功'
        }), 201
    except Exception as e:
        current_app.logger.error(f"创建货位失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
