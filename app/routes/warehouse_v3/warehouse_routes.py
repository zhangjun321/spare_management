"""
仓库管理路由 V3
"""

from flask import request, jsonify, current_app
from flask_login import login_required
from app.routes.warehouse_v3 import warehouse_v3_bp
from app.services.warehouse_v3.warehouse_service import WarehouseV3Service
from app.services.warehouse_v3.ai_analysis_service import AIAnalysisV3Service


@warehouse_v3_bp.route('/warehouses', methods=['GET'])
@login_required
def get_warehouses():
    """获取仓库列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        filters = {
            'type': request.args.get('type'),
            'status': request.args.get('status'),
            'keyword': request.args.get('keyword')
        }
        
        result = WarehouseV3Service.get_all_warehouses(page, per_page, filters)
        
        return jsonify({
            'success': True,
            'data': {
                'warehouses': [w.to_dict() for w in result['items']],
                'total': result['total'],
                'page': result['page'],
                'pages': result['pages']
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取仓库列表失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/warehouses', methods=['POST'])
@login_required
def create_warehouse():
    """创建仓库"""
    try:
        data = request.get_json()
        
        if not data or not data.get('code') or not data.get('name'):
            return jsonify({
                'success': False,
                'error': '仓库编码和名称必填'
            }), 400
        
        warehouse = WarehouseV3Service.create_warehouse(data)
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': '仓库创建成功'
        }), 201
    except Exception as e:
        current_app.logger.error(f"创建仓库失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/warehouses/<int:warehouse_id>', methods=['GET'])
@login_required
def get_warehouse(warehouse_id):
    """获取仓库详情"""
    try:
        warehouse = WarehouseV3Service.get_warehouse_by_id(warehouse_id)
        
        if not warehouse:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"获取仓库详情失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/warehouses/<int:warehouse_id>', methods=['PUT'])
@login_required
def update_warehouse(warehouse_id):
    """更新仓库"""
    try:
        data = request.get_json()
        
        warehouse = WarehouseV3Service.update_warehouse(warehouse_id, data)
        
        if not warehouse:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': '仓库更新成功'
        })
    except Exception as e:
        current_app.logger.error(f"更新仓库失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/warehouses/<int:warehouse_id>', methods=['DELETE'])
@login_required
def delete_warehouse(warehouse_id):
    """删除仓库"""
    try:
        success = WarehouseV3Service.delete_warehouse(warehouse_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '仓库删除成功'
        })
    except Exception as e:
        current_app.logger.error(f"删除仓库失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/warehouses/<int:warehouse_id>/stats', methods=['GET'])
@login_required
def get_warehouse_stats(warehouse_id):
    """获取仓库统计信息"""
    try:
        stats = WarehouseV3Service.get_warehouse_statistics(warehouse_id)
        
        if not stats:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        current_app.logger.error(f"获取仓库统计失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/warehouses/analyze', methods=['POST'])
@login_required
def analyze_warehouse():
    """AI 分析仓库"""
    try:
        data = request.get_json()
        parts_data = data.get('parts_data', [])
        
        if not parts_data:
            return jsonify({
                'success': False,
                'error': '请提供备件数据'
            }), 400
        
        # 调用 AI 分析服务
        analysis_result = AIAnalysisV3Service.analyze_parts_data(parts_data)
        
        if analysis_result.get('success'):
            return jsonify({
                'success': True,
                'data': analysis_result,
                'message': 'AI 分析完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': analysis_result.get('error', 'AI 分析失败')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"AI 分析失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
