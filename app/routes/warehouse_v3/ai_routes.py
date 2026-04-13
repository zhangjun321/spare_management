"""
AI 功能路由 V3
"""

from flask import request, jsonify, current_app
from flask_login import login_required
from app.routes.warehouse_v3 import warehouse_v3_bp
from app.services.warehouse_v3.ai_analysis_service import AIAnalysisV3Service


@warehouse_v3_bp.route('/ai/analyze-parts', methods=['POST'])
@login_required
def ai_analyze_parts():
    """AI 分析备件数据"""
    try:
        data = request.get_json()
        parts_data = data.get('parts_data', [])
        
        if not parts_data:
            return jsonify({
                'success': False,
                'error': '请提供备件数据'
            }), 400
        
        # 调用 AI 分析
        result = AIAnalysisV3Service.analyze_parts_data(parts_data)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result,
                'message': 'AI 分析完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 分析失败')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"AI 分析备件失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/ai/recommend-locations', methods=['POST'])
@login_required
def ai_recommend_locations():
    """AI 推荐货位"""
    try:
        data = request.get_json()
        
        part_data = data.get('part_data', {})
        warehouse_id = data.get('warehouse_id')
        quantity = data.get('quantity', 0)
        
        if not warehouse_id or not part_data:
            return jsonify({
                'success': False,
                'error': '请提供仓库 ID 和备件数据'
            }), 400
        
        # 调用 AI 推荐
        result = AIAnalysisV3Service.recommend_location(part_data, warehouse_id, quantity)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result,
                'message': '货位推荐完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 推荐失败')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"AI 推荐货位失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/ai/optimize-picking', methods=['POST'])
@login_required
def ai_optimize_picking():
    """AI 优化拣货路径"""
    try:
        data = request.get_json()
        picking_list = data.get('picking_list', [])
        
        if not picking_list:
            return jsonify({
                'success': False,
                'error': '请提供拣货清单'
            }), 400
        
        # 调用 AI 优化
        result = AIAnalysisV3Service.optimize_picking_path(picking_list)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result,
                'message': '拣货路径优化完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 优化失败')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"AI 优化拣货路径失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/ai/predict-demand', methods=['POST'])
@login_required
def ai_predict_demand():
    """AI 需求预测"""
    try:
        data = request.get_json()
        historical_data = data.get('historical_data', [])
        days = data.get('days', 30)
        
        if not historical_data:
            return jsonify({
                'success': False,
                'error': '请提供历史数据'
            }), 400
        
        # 调用 AI 预测
        result = AIAnalysisV3Service.predict_demand(historical_data, days)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'data': result,
                'message': f'未来{days}天需求预测完成'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'AI 预测失败')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"AI 需求预测失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@warehouse_v3_bp.route('/ai/insights', methods=['GET'])
@login_required
def get_ai_insights():
    """获取 AI 洞察"""
    try:
        # 这里可以返回各种 AI 分析结果
        insights = {
            'optimization_suggestions': [
                {
                    'type': 'location',
                    'priority': 'high',
                    'content': '发现 23 个备件货位分配不合理，建议调整'
                },
                {
                    'type': 'inventory',
                    'priority': 'medium',
                    'content': '识别 15 个呆滞物料，建议促销或调拨'
                }
            ],
            'predictions': {
                'next_week_demand': '预计增长 15%',
                'inventory_risk': '低风险'
            }
        }
        
        return jsonify({
            'success': True,
            'data': insights
        })
        
    except Exception as e:
        current_app.logger.error(f"获取 AI 洞察失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
