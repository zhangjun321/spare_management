"""
拣货推荐 API 路由
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.warehouse_v3.picking_recommendation_service import PickingRecommendationService

picking_recommendation_bp = Blueprint('picking_recommendation', __name__, url_prefix='/api/picking-recommendation')


@picking_recommendation_bp.route('/single', methods=['POST'])
@login_required
def recommend_single():
    """单个备件拣货推荐"""
    try:
        data = request.get_json()
        part_id = data.get('part_id')
        quantity = data.get('quantity', 0)
        strategy = data.get('strategy', 'FEFO')
        warehouse_id = data.get('warehouse_id', type=int)
        
        if not part_id:
            return jsonify({
                'success': False,
                'message': '请提供备件 ID'
            }), 400
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': '拣货数量必须大于 0'
            }), 400
        
        result = PickingRecommendationService.recommend_with_strategy(
            part_id=part_id,
            quantity=quantity,
            strategy=strategy,
            warehouse_id=warehouse_id
        )
        
        return jsonify({
            'success': result['success'],
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@picking_recommendation_bp.route('/batch', methods=['POST'])
@login_required
def recommend_batch():
    """批量拣货推荐"""
    try:
        data = request.get_json()
        picking_list = data.get('picking_list', [])
        strategy = data.get('strategy', 'FEFO')
        warehouse_id = data.get('warehouse_id', type=int)
        
        if not picking_list:
            return jsonify({
                'success': False,
                'message': '请提供拣货清单'
            }), 400
        
        result = PickingRecommendationService.batch_recommend_multiple_parts(
            picking_list=picking_list,
            strategy=strategy,
            warehouse_id=warehouse_id
        )
        
        return jsonify({
            'success': result['success'],
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@picking_recommendation_bp.route('/compare', methods=['POST'])
@login_required
def compare_strategies():
    """比较不同策略的推荐结果"""
    try:
        data = request.get_json()
        part_id = data.get('part_id')
        quantity = data.get('quantity', 0)
        warehouse_id = data.get('warehouse_id', type=int)
        
        if not part_id:
            return jsonify({
                'success': False,
                'message': '请提供备件 ID'
            }), 400
        
        # 分别使用三种策略
        fifo_result = PickingRecommendationService.recommend_with_strategy(
            part_id=part_id,
            quantity=quantity,
            strategy='FIFO',
            warehouse_id=warehouse_id
        )
        
        fefo_result = PickingRecommendationService.recommend_with_strategy(
            part_id=part_id,
            quantity=quantity,
            strategy='FEFO',
            warehouse_id=warehouse_id
        )
        
        lifo_result = PickingRecommendationService.recommend_with_strategy(
            part_id=part_id,
            quantity=quantity,
            strategy='LIFO',
            warehouse_id=warehouse_id
        )
        
        return jsonify({
            'success': True,
            'data': {
                'part_id': part_id,
                'quantity': quantity,
                'strategies': {
                    'FIFO': fifo_result,
                    'FEFO': fefo_result,
                    'LIFO': lifo_result
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
