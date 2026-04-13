from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.path_optimization_service import PathOptimizationService, RouteOptimizationService
from app.models.warehouse_v3.location import WarehouseLocationV3 as Location
from app.models.warehouse_v3.wave_management import WaveTaskItem, WaveTask

path_optimization_bp = Blueprint('path_optimization', __name__, url_prefix='/api/path-optimization')


# ==================== 路径优化 API ====================

@path_optimization_bp.route('/calculate-distance', methods=['POST'])
def calculate_distance():
    """计算两个库位之间的距离"""
    data = request.get_json()
    
    location1_id = data.get('location1_id', type=int)
    location2_id = data.get('location2_id', type=int)
    
    if not location1_id or not location2_id:
        return jsonify({'success': False, 'message': '库位 ID 不能为空'}), 400
    
    location1 = Location.query.get(location1_id)
    location2 = Location.query.get(location2_id)
    
    if not location1 or not location2:
        return jsonify({'success': False, 'message': '库位不存在'}), 404
    
    distance = PathOptimizationService.calculate_distance(location1, location2)
    
    return jsonify({
        'success': True,
        'data': {
            'location1_id': location1_id,
            'location2_id': location2_id,
            'distance': distance
        }
    })


@path_optimization_bp.route('/optimize/tsp', methods=['POST'])
def optimize_tsp():
    """TSP 路径优化"""
    data = request.get_json()
    
    location_ids = data.get('location_ids', [])
    start_location_id = data.get('start_location_id', type=int)
    algorithm = data.get('algorithm', 'two_opt')  # nearest_neighbor / two_opt / s_shape
    
    if not location_ids:
        return jsonify({'success': False, 'message': '库位 ID 列表不能为空'}), 400
    
    # 获取库位
    locations = Location.query.filter(Location.id.in_(location_ids)).all()
    
    if len(locations) != len(location_ids):
        return jsonify({'success': False, 'message': '部分库位不存在'}), 404
    
    start_location = Location.query.get(start_location_id) if start_location_id else None
    
    # 执行优化
    if algorithm == 'nearest_neighbor':
        optimized_path = PathOptimizationService.nearest_neighbor_tsp(locations, start_location)
    elif algorithm == 's_shape':
        optimized_path = PathOptimizationService.generate_s_shape_route(locations, start_location)
    else:  # two_opt
        optimized_path = PathOptimizationService.two_opt_tsp(locations, start_location)
    
    # 计算优化效果
    original_distance = PathOptimizationService.calculate_path_distance(locations)
    optimized_distance = PathOptimizationService.calculate_path_distance(optimized_path)
    
    improvement = 0
    if original_distance > 0:
        improvement = ((original_distance - optimized_distance) / original_distance) * 100
    
    return jsonify({
        'success': True,
        'message': '路径优化成功',
        'data': {
            'algorithm': algorithm,
            'original_distance': original_distance,
            'optimized_distance': optimized_distance,
            'improvement_percent': round(improvement, 2),
            'optimized_location_ids': [loc.id for loc in optimized_path],
            'estimated_time': PathOptimizationService.calculate_estimated_time(optimized_path)
        }
    })


@path_optimization_bp.route('/optimize/task/<int:task_id>', methods=['POST'])
def optimize_task_route(task_id):
    """优化任务拣货路径"""
    result = RouteOptimizationService.optimize_wave_task_route(task_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@path_optimization_bp.route('/optimize/batch', methods=['POST'])
def optimize_batch_routes():
    """批量优化路径"""
    data = request.get_json()
    
    task_ids = data.get('task_ids', [])
    
    if not task_ids:
        return jsonify({'success': False, 'message': '任务 ID 列表不能为空'}), 400
    
    result = RouteOptimizationService.batch_optimize_routes(task_ids)
    
    return jsonify(result)


# ==================== 路径查询 API ====================

@path_optimization_bp.route('/route/simulate', methods=['POST'])
def simulate_route():
    """模拟路径执行"""
    data = request.get_json()
    
    location_ids = data.get('location_ids', [])
    start_location_id = data.get('start_location_id', type=int)
    
    if not location_ids:
        return jsonify({'success': False, 'message': '库位 ID 列表不能为空'}), 400
    
    locations = Location.query.filter(Location.id.in_(location_ids)).all()
    start_location = Location.query.get(start_location_id) if start_location_id else None
    
    # 优化路径
    optimized_path = PathOptimizationService.two_opt_tsp(locations, start_location)
    
    # 模拟执行
    simulation = {
        'total_locations': len(optimized_path),
        'total_distance': PathOptimizationService.calculate_path_distance(optimized_path),
        'estimated_time': PathOptimizationService.calculate_estimated_time(optimized_path),
        'route_details': []
    }
    
    current_distance = 0
    for i, location in enumerate(optimized_path):
        if i > 0:
            segment_distance = PathOptimizationService.calculate_distance(optimized_path[i-1], location)
            current_distance += segment_distance
        
        simulation['route_details'].append({
            'sequence': i + 1,
            'location_id': location.id,
            'location_code': location.location_code,
            'distance_from_start': round(current_distance, 2),
            'estimated_arrival_time': round(current_distance / 1.5 / 60, 2)  # 假设速度 1.5m/s
        })
    
    return jsonify({
        'success': True,
        'data': simulation
    })


# ==================== 路径分析 API ====================

@path_optimization_bp.route('/analyze/heatmap', methods=['GET'])
def analyze_route_heatmap():
    """分析路径热度"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    # 获取最近 N 天的任务
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    tasks = WaveTask.query.filter(
        WaveTask.warehouse_id == warehouse_id,
        WaveTask.created_at >= cutoff_date,
        WaveTask.status == 'completed'
    ).all()
    
    # 统计库位访问频率
    location_visits = {}
    for task in tasks:
        task_items = WaveTaskItem.query.filter_by(task_id=task.id).all()
        for item in task_items:
            loc_id = item.location_id
            if loc_id not in location_visits:
                location_visits[loc_id] = 0
            location_visits[loc_id] += 1
    
    # 按访问频率排序
    sorted_locations = sorted(location_visits.items(), key=lambda x: x[1], reverse=True)
    
    # 热度分级
    hot_locations = []
    warm_locations = []
    cold_locations = []
    
    total_locations = len(sorted_locations)
    for i, (loc_id, visits) in enumerate(sorted_locations):
        location = Location.query.get(loc_id)
        location_data = {
            'location_id': loc_id,
            'location_code': location.location_code if location else '',
            'visits': visits
        }
        
        if i < total_locations * 0.2:  # 前 20% 为热点
            hot_locations.append(location_data)
        elif i < total_locations * 0.5:  # 前 50% 为温点
            warm_locations.append(location_data)
        else:
            cold_locations.append(location_data)
    
    return jsonify({
        'success': True,
        'data': {
            'period_days': days,
            'total_tasks': len(tasks),
            'total_locations': total_locations,
            'hot_locations': hot_locations,
            'warm_locations': warm_locations,
            'cold_locations': cold_locations
        }
    })


@path_optimization_bp.route('/analyze/efficiency', methods=['GET'])
def analyze_route_efficiency():
    """分析路径效率"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    tasks = WaveTask.query.filter(
        WaveTask.warehouse_id == warehouse_id,
        WaveTask.created_at >= cutoff_date,
        WaveTask.status == 'completed',
        WaveTask.actual_time.isnot(None)
    ).all()
    
    if not tasks:
        return jsonify({
            'success': True,
            'data': {
                'message': '没有足够的任务数据'
            }
        })
    
    # 计算效率指标
    total_estimated_time = sum([t.estimated_time or 0 for t in tasks])
    total_actual_time = sum([t.actual_time or 0 for t in tasks])
    
    avg_estimated_time = total_estimated_time / len(tasks) if tasks else 0
    avg_actual_time = total_actual_time / len(tasks) if tasks else 0
    
    efficiency_rate = (total_estimated_time / total_actual_time * 100) if total_actual_time > 0 else 100
    
    # 按任务类型分组
    by_type = {}
    for task in tasks:
        task_type = task.task_type
        if task_type not in by_type:
            by_type[task_type] = {'count': 0, 'total_estimated': 0, 'total_actual': 0}
        
        by_type[task_type]['count'] += 1
        by_type[task_type]['total_estimated'] += task.estimated_time or 0
        by_type[task_type]['total_actual'] += task.actual_time or 0
    
    # 计算各类型效率
    for task_type in by_type:
        if by_type[task_type]['total_actual'] > 0:
            by_type[task_type]['efficiency'] = round(
                by_type[task_type]['total_estimated'] / by_type[task_type]['total_actual'] * 100, 2
            )
        else:
            by_type[task_type]['efficiency'] = 100
    
    return jsonify({
        'success': True,
        'data': {
            'period_days': days,
            'total_tasks': len(tasks),
            'total_estimated_time': total_estimated_time,
            'total_actual_time': total_actual_time,
            'avg_estimated_time': round(avg_estimated_time, 2),
            'avg_actual_time': round(avg_actual_time, 2),
            'efficiency_rate': round(efficiency_rate, 2),
            'by_type': by_type
        }
    })
