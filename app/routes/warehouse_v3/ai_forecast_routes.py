from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.ai_forecast_service import DemandForecastService, ReorderRecommendationService, InventoryOptimizationService
from app.models.warehouse_v3.ai_forecast import DemandForecast, ReorderRecommendation, InventoryOptimization
from app.models.warehouse_v3.inventory import InventoryV3
from datetime import datetime

ai_forecast_bp = Blueprint('ai_forecast', __name__, url_prefix='/api/ai-forecast')


# ==================== 需求预测 API ====================

@ai_forecast_bp.route('/demand/generate', methods=['POST'])
def generate_forecast():
    """生成需求预测"""
    data = request.get_json()
    
    part_id = data.get('part_id', type=int)
    warehouse_id = data.get('warehouse_id', type=int)
    forecast_days = data.get('forecast_days', 30)
    
    if not part_id or not warehouse_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    forecast = DemandForecastService.generate_forecast(part_id, warehouse_id, forecast_days)
    
    return jsonify({
        'success': True,
        'message': '需求预测生成成功',
        'data': forecast.to_dict()
    })


@ai_forecast_bp.route('/demand/batch-generate', methods=['POST'])
def batch_generate_forecast():
    """批量生成需求预测"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    part_ids = data.get('part_ids', [])
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    # 如果没有指定备件 ID，使用仓库所有备件
    if not part_ids:
        inventories = InventoryV3.query.filter_by(warehouse_id=warehouse_id).all()
        part_ids = [inv.part_id for inv in inventories]
    
    forecasts = []
    for part_id in part_ids:
        forecast = DemandForecastService.generate_forecast(part_id, warehouse_id)
        forecasts.append(forecast.to_dict())
    
    return jsonify({
        'success': True,
        'message': f'生成{len(forecasts)}个预测',
        'data': forecasts
    })


@ai_forecast_bp.route('/demand/list', methods=['GET'])
def get_forecast_list():
    """获取预测列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    part_id = request.args.get('part_id', type=int)
    status = request.args.get('status')
    
    query = DemandForecast.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if part_id:
        query = query.filter_by(part_id=part_id)
    if status:
        query = query.filter_by(status=status)
    
    forecasts = query.order_by(DemandForecast.forecast_date.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [forecast.to_dict() for forecast in forecasts]
    })


@ai_forecast_bp.route('/demand/accuracy', methods=['GET'])
def get_forecast_accuracy():
    """获取预测准确率"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    cutoff_date = datetime.now().date() - timedelta(days=days)
    
    query = DemandForecast.query.filter(
        DemandForecast.forecast_date >= cutoff_date,
        DemandForecast.actual_demand.isnot(None)
    )
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    
    forecasts = query.all()
    
    if not forecasts:
        return jsonify({
            'success': True,
            'data': {
                'message': '暂无准确率数据'
            }
        })
    
    # 计算平均准确率
    total_accuracy = sum([float(f.accuracy) for f in forecasts if f.accuracy])
    avg_accuracy = total_accuracy / len(forecasts) if forecasts else 0
    
    return jsonify({
        'success': True,
        'data': {
            'period_days': days,
            'total_forecasts': len(forecasts),
            'average_accuracy': round(avg_accuracy, 2),
            'forecasts': [f.to_dict() for f in forecasts]
        }
    })


# ==================== 补货建议 API ====================

@ai_forecast_bp.route('/reorder/generate', methods=['POST'])
def generate_reorder():
    """生成补货建议"""
    data = request.get_json()
    
    part_id = data.get('part_id', type=int)
    warehouse_id = data.get('warehouse_id', type=int)
    
    if not part_id or not warehouse_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    recommendation = ReorderRecommendationService.generate_reorder_recommendation(part_id, warehouse_id)
    
    if not recommendation:
        return jsonify({
            'success': False,
            'message': '当前库存充足，无需补货'
        }), 400
    
    return jsonify({
        'success': True,
        'message': '补货建议生成成功',
        'data': recommendation.to_dict()
    })


@ai_forecast_bp.route('/reorder/batch-generate', methods=['POST'])
def batch_generate_reorder():
    """批量生成补货建议"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    count = ReorderRecommendationService.batch_generate_recommendations(warehouse_id)
    
    return jsonify({
        'success': True,
        'message': f'生成{count}个补货建议',
        'data': {
            'count': count
        }
    })


@ai_forecast_bp.route('/reorder/list', methods=['GET'])
def get_reorder_list():
    """获取补货建议列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    part_id = request.args.get('part_id', type=int)
    status = request.args.get('status')
    urgency_level = request.args.get('urgency_level')
    
    query = ReorderRecommendation.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if part_id:
        query = query.filter_by(part_id=part_id)
    if status:
        query = query.filter_by(status=status)
    if urgency_level:
        query = query.filter_by(urgency_level=urgency_level)
    
    recommendations = query.order_by(
        ReorderRecommendation.priority.asc(),
        ReorderRecommendation.created_at.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': [rec.to_dict() for rec in recommendations]
    })


@ai_forecast_bp.route('/reorder/<int:rec_id>/approve', methods=['POST'])
def approve_reorder(rec_id):
    """审批补货建议"""
    data = request.get_json()
    approved_by = data.get('approved_by', 1)  # TODO: 从当前用户获取
    
    recommendation = ReorderRecommendation.query.get(rec_id)
    if not recommendation:
        return jsonify({'success': False, 'message': '建议不存在'}), 404
    
    recommendation.status = 'approved'
    recommendation.approved_at = datetime.utcnow()
    recommendation.approved_by = approved_by
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '补货建议已批准',
        'data': recommendation.to_dict()
    })


@ai_forecast_bp.route('/reorder/<int:rec_id>/order', methods=['POST'])
def create_order(rec_id):
    """创建采购订单"""
    recommendation = ReorderRecommendation.query.get(rec_id)
    if not recommendation:
        return jsonify({'success': False, 'message': '建议不存在'}), 404
    
    if recommendation.status != 'approved':
        return jsonify({'success': False, 'message': '请先审批补货建议'}), 400
    
    # TODO: 创建采购订单
    # 这里应该调用采购模块 API
    
    recommendation.status = 'ordered'
    recommendation.ordered_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '采购订单已创建',
        'data': recommendation.to_dict()
    })


# ==================== 库存优化 API ====================

@ai_forecast_bp.route('/inventory/optimize', methods=['POST'])
def optimize_inventory():
    """优化库存参数"""
    data = request.get_json()
    
    part_id = data.get('part_id', type=int)
    warehouse_id = data.get('warehouse_id', type=int)
    
    if not part_id or not warehouse_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    optimization = InventoryOptimizationService.calculate_optimization_params(part_id, warehouse_id)
    
    return jsonify({
        'success': True,
        'message': '库存优化参数计算完成',
        'data': optimization.to_dict()
    })


@ai_forecast_bp.route('/inventory/batch-optimize', methods=['POST'])
def batch_optimize_inventory():
    """批量优化库存参数"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    # 获取仓库所有备件
    inventories = InventoryV3.query.filter_by(warehouse_id=warehouse_id).all()
    
    count = 0
    for inventory in inventories:
        try:
            InventoryOptimizationService.calculate_optimization_params(
                inventory.part_id, warehouse_id
            )
            count += 1
        except Exception as e:
            continue
    
    return jsonify({
        'success': True,
        'message': f'优化{count}个备件库存参数',
        'data': {
            'count': count
        }
    })


@ai_forecast_bp.route('/inventory/params', methods=['GET'])
def get_inventory_params():
    """获取库存优化参数"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    part_id = request.args.get('part_id', type=int)
    
    query = InventoryOptimization.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if part_id:
        query = query.filter_by(part_id=part_id)
    
    optimizations = query.all()
    
    return jsonify({
        'success': True,
        'data': [opt.to_dict() for opt in optimizations]
    })


# ==================== 统计 API ====================

@ai_forecast_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    # 预测统计
    total_forecasts = DemandForecast.query.count()
    active_forecasts = DemandForecast.query.filter_by(status='active').count()
    
    # 补货建议统计
    total_recommendations = ReorderRecommendation.query.count()
    pending_recommendations = ReorderRecommendation.query.filter_by(status='pending').count()
    urgent_recommendations = ReorderRecommendation.query.filter_by(urgency_level='URGENT').count()
    
    # 库存优化统计
    total_optimizations = InventoryOptimization.query.count()
    
    stats = {
        'forecasts': {
            'total': total_forecasts,
            'active': active_forecasts
        },
        'recommendations': {
            'total': total_recommendations,
            'pending': pending_recommendations,
            'urgent': urgent_recommendations
        },
        'optimizations': {
            'total': total_optimizations
        }
    }
    
    if warehouse_id:
        stats['warehouse_forecasts'] = DemandForecast.query.filter_by(warehouse_id=warehouse_id).count()
        stats['warehouse_recommendations'] = ReorderRecommendation.query.filter_by(warehouse_id=warehouse_id).count()
    
    return jsonify({
        'success': True,
        'data': stats
    })
