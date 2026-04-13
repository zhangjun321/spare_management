from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.location_optimization_service import LocationHeatmapService, LocationOptimizationService
from app.models.warehouse_v3.location_optimization import LocationOptimization, LocationHeatmap, LocationSuggestion
from datetime import datetime, timedelta

location_optimization_bp = Blueprint('location_optimization', __name__, url_prefix='/api/location-optimization')


# ==================== 库位热度分析 API ====================

@location_optimization_bp.route('/heatmap/update', methods=['POST'])
def update_heatmap():
    """更新库位热度"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    location_id = data.get('location_id', type=int)
    operation_type = data.get('operation_type', 'PICK')  # PICK/PUT/MOVE
    quantity = data.get('quantity', 1)
    
    if not warehouse_id or not location_id:
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    heatmap = LocationHeatmapService.update_location_heatmap(
        warehouse_id, location_id, operation_type, quantity
    )
    
    return jsonify({
        'success': True,
        'message': '库位热度已更新',
        'data': heatmap.to_dict()
    })


@location_optimization_bp.route('/heatmap/query', methods=['GET'])
def get_heatmap():
    """查询库位热度"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    heatmap_data = LocationHeatmapService.get_location_heatmap(
        warehouse_id, start_date, end_date
    )
    
    return jsonify({
        'success': True,
        'data': heatmap_data
    })


@location_optimization_bp.route('/heatmap/visualize', methods=['GET'])
def visualize_heatmap():
    """可视化库位热度"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    heatmap_data = LocationHeatmapService.get_location_heatmap(
        warehouse_id, start_date, end_date
    )
    
    # 按热度等级分组
    hot_locations = [loc for loc in heatmap_data if loc['heat_level'] == 'HOT']
    warm_locations = [loc for loc in heatmap_data if loc['heat_level'] == 'WARM']
    cold_locations = [loc for loc in heatmap_data if loc['heat_level'] == 'COLD']
    
    return jsonify({
        'success': True,
        'data': {
            'hot_locations': hot_locations,
            'warm_locations': warm_locations,
            'cold_locations': cold_locations,
            'total_locations': len(heatmap_data),
            'period_days': days
        }
    })


# ==================== 库位优化 API ====================

@location_optimization_bp.route('/turnover/calculate', methods=['POST'])
def calculate_turnover():
    """计算周转率"""
    data = request.get_json()
    
    part_id = data.get('part_id', type=int)
    warehouse_id = data.get('warehouse_id', type=int)
    days = data.get('days', 30)
    
    if not part_id:
        return jsonify({'success': False, 'message': '备件 ID 不能为空'}), 400
    
    turnover_rate = LocationOptimizationService.calculate_part_turnover(
        part_id, warehouse_id, days
    )
    
    return jsonify({
        'success': True,
        'data': {
            'part_id': part_id,
            'warehouse_id': warehouse_id,
            'turnover_rate': turnover_rate,
            'period_days': days
        }
    })


@location_optimization_bp.route('/pick-frequency/analyze', methods=['POST'])
def analyze_pick_frequency():
    """分析拣货频次"""
    data = request.get_json()
    
    part_id = data.get('part_id', type=int)
    warehouse_id = data.get('warehouse_id', type=int)
    days = data.get('days', 30)
    
    if not part_id:
        return jsonify({'success': False, 'message': '备件 ID 不能为空'}), 400
    
    pick_frequency = LocationOptimizationService.analyze_pick_frequency(
        part_id, warehouse_id, days
    )
    
    return jsonify({
        'success': True,
        'data': {
            'part_id': part_id,
            'warehouse_id': warehouse_id,
            'pick_frequency': pick_frequency,
            'period_days': days
        }
    })


@location_optimization_bp.route('/recommend', methods=['POST'])
def recommend_location():
    """推荐库位"""
    data = request.get_json()
    
    part_id = data.get('part_id', type=int)
    warehouse_id = data.get('warehouse_id', type=int)
    
    if not part_id or not warehouse_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    recommended_location = LocationOptimizationService.recommend_location(
        part_id, warehouse_id
    )
    
    if not recommended_location:
        return jsonify({'success': False, 'message': '未找到合适的库位'}), 404
    
    return jsonify({
        'success': True,
        'message': '推荐库位成功',
        'data': {
            'part_id': part_id,
            'warehouse_id': warehouse_id,
            'recommended_location_id': recommended_location.id,
            'recommended_location_code': recommended_location.location_code,
            'zone': recommended_location.zone,
            'level': recommended_location.level,
            'distance_to_exit': recommended_location.distance_to_exit
        }
    })


@location_optimization_bp.route('/suggestions/generate', methods=['POST'])
def generate_suggestions():
    """生成优化建议"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    suggestions = LocationOptimizationService.generate_optimization_suggestions(warehouse_id)
    
    return jsonify({
        'success': True,
        'message': f'生成{len(suggestions)}条优化建议',
        'data': [suggestion.to_dict() for suggestion in suggestions]
    })


@location_optimization_bp.route('/suggestions/list', methods=['GET'])
def get_suggestions():
    """获取优化建议列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status')
    priority = request.args.get('priority', type=int)
    
    query = LocationSuggestion.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    
    suggestions = query.order_by(LocationSuggestion.priority.asc(), LocationSuggestion.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [suggestion.to_dict() for suggestion in suggestions]
    })


@location_optimization_bp.route('/suggestion/<int:suggestion_id>/apply', methods=['POST'])
def apply_suggestion(suggestion_id):
    """应用优化建议"""
    data = request.get_json()
    applied_by = data.get('applied_by', 1)  # TODO: 从当前用户获取
    
    suggestion = LocationSuggestion.query.get(suggestion_id)
    if not suggestion:
        return jsonify({'success': False, 'message': '建议不存在'}), 404
    
    suggestion.status = 'accepted'
    suggestion.applied_at = datetime.utcnow()
    suggestion.applied_by = applied_by
    
    # TODO: 实际执行库位调整操作
    # 这里应该调用库存转移服务
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '优化建议已应用',
        'data': suggestion.to_dict()
    })


@location_optimization_bp.route('/suggestion/<int:suggestion_id>/reject', methods=['POST'])
def reject_suggestion(suggestion_id):
    """拒绝优化建议"""
    suggestion = LocationSuggestion.query.get(suggestion_id)
    if not suggestion:
        return jsonify({'success': False, 'message': '建议不存在'}), 404
    
    suggestion.status = 'rejected'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '优化建议已拒绝',
        'data': suggestion.to_dict()
    })


# ==================== 优化统计 API ====================

@location_optimization_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    # 总优化建议数
    total_suggestions = LocationSuggestion.query.count()
    
    # 待处理建议数
    pending_suggestions = LocationSuggestion.query.filter_by(status='pending').count()
    
    # 已应用建议数
    applied_suggestions = LocationSuggestion.query.filter_by(status='accepted').count()
    
    # 今日热度记录数
    today = datetime.now().date()
    today_heatmaps = LocationHeatmap.query.filter_by(date=today).count()
    
    # 高热度库位数
    hot_locations = LocationHeatmap.query.filter_by(date=today, heat_level='HOT').count()
    
    stats = {
        'total_suggestions': total_suggestions,
        'pending_suggestions': pending_suggestions,
        'applied_suggestions': applied_suggestions,
        'today_heatmaps': today_heatmaps,
        'hot_locations': hot_locations
    }
    
    if warehouse_id:
        stats['warehouse_suggestions'] = LocationSuggestion.query.filter_by(warehouse_id=warehouse_id).count()
        stats['warehouse_heatmaps'] = LocationHeatmap.query.filter_by(warehouse_id=warehouse_id, date=today).count()
    
    return jsonify({
        'success': True,
        'data': stats
    })
