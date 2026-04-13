from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.ai_task_assignment_service import AITaskAssignmentService
from app.models.warehouse_v3.task_scheduler import WarehouseTask, Worker

ai_task_assignment_bp = Blueprint('ai_task_assignment', __name__, url_prefix='/api/ai-task-assignment')


# ==================== 智能任务分配 API ====================

@ai_task_assignment_bp.route('/assign/smart', methods=['POST'])
def smart_assign_task():
    """智能分配单个任务"""
    data = request.get_json()
    
    task_id = data.get('task_id', type=int)
    
    if not task_id:
        return jsonify({'success': False, 'message': '任务 ID 不能为空'}), 400
    
    result = AITaskAssignmentService.smart_assign_task(task_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@ai_task_assignment_bp.route('/assign/batch', methods=['POST'])
def batch_smart_assign():
    """批量智能分配任务"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    limit = data.get('limit', 20)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    result = AITaskAssignmentService.batch_smart_assign(warehouse_id, limit)
    
    return jsonify(result)


@ai_task_assignment_bp.route('/assign/manual', methods=['POST'])
def manual_assign_task():
    """手动分配任务（AI 辅助）"""
    data = request.get_json()
    
    task_id = data.get('task_id', type=int)
    worker_id = data.get('worker_id', type=int)
    
    if not task_id or not worker_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    task = WarehouseTask.query.get(task_id)
    worker = Worker.query.filter_by(user_id=worker_id).first()
    
    if not task or not worker:
        return jsonify({'success': False, 'message': '任务或工人不存在'}), 404
    
    # 计算适配度
    fitness = AITaskAssignmentService.calculate_worker_fitness(worker, task)
    task_priority = AITaskAssignmentService.calculate_task_priority(task)
    
    # 分配任务
    task.status = 'assigned'
    task.assigned_to = worker_id
    task.assigned_at = datetime.utcnow()
    
    worker.status = 'busy'
    worker.current_task_id = task.id
    worker.last_active_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '任务分配成功',
        'data': {
            'task': task.to_dict(),
            'worker': worker.to_dict(),
            'fitness_score': fitness,
            'task_priority_score': task_priority
        }
    })


# ==================== 任务推荐 API ====================

@ai_task_assignment_bp.route('/recommendations', methods=['GET'])
def get_task_recommendations():
    """获取任务推荐"""
    worker_id = request.args.get('worker_id', type=int)
    limit = request.args.get('limit', 5, type=int)
    
    if not worker_id:
        return jsonify({'success': False, 'message': '工人 ID 不能为空'}), 400
    
    recommendations = AITaskAssignmentService.get_task_recommendations(worker_id, limit)
    
    return jsonify({
        'success': True,
        'data': recommendations
    })


@ai_task_assignment_bp.route('/recommendations/auto-assign', methods=['POST'])
def auto_assign_from_recommendations():
    """自动分配推荐任务"""
    data = request.get_json()
    
    worker_id = data.get('worker_id', type=int)
    max_tasks = data.get('max_tasks', 3)
    
    if not worker_id:
        return jsonify({'success': False, 'message': '工人 ID 不能为空'}), 400
    
    worker = Worker.query.filter_by(user_id=worker_id).first()
    if not worker:
        return jsonify({'success': False, 'message': '工人不存在'}), 404
    
    # 获取推荐
    recommendations = AITaskAssignmentService.get_task_recommendations(worker_id, max_tasks)
    
    assigned_count = 0
    assigned_tasks = []
    
    for rec in recommendations:
        task = WarehouseTask.query.get(rec['task_id'])
        if task and task.status == 'pending':
            # 分配任务
            task.status = 'assigned'
            task.assigned_to = worker_id
            task.assigned_at = datetime.utcnow()
            db.session.add(task)
            
            assigned_count += 1
            assigned_tasks.append(rec['task_id'])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'自动分配{assigned_count}个任务',
        'data': {
            'worker_id': worker_id,
            'assigned_count': assigned_count,
            'assigned_tasks': assigned_tasks
        }
    })


# ==================== 任务序列优化 API ====================

@ai_task_assignment_bp.route('/optimize/sequence', methods=['POST'])
def optimize_task_sequence():
    """优化任务序列"""
    data = request.get_json()
    
    worker_id = data.get('worker_id', type=int)
    
    if not worker_id:
        return jsonify({'success': False, 'message': '工人 ID 不能为空'}), 400
    
    result = AITaskAssignmentService.optimize_task_sequence(worker_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


# ==================== AI 分析 API ====================

@ai_task_assignment_bp.route('/analyze/fitness', methods=['POST'])
def analyze_fitness():
    """分析工人适配度"""
    data = request.get_json()
    
    worker_id = data.get('worker_id', type=int)
    task_id = data.get('task_id', type=int)
    
    if not worker_id or not task_id:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    worker = Worker.query.filter_by(user_id=worker_id).first()
    task = WarehouseTask.query.get(task_id)
    
    if not worker or not task:
        return jsonify({'success': False, 'message': '工人或任务不存在'}), 404
    
    fitness = AITaskAssignmentService.calculate_worker_fitness(worker, task)
    task_priority = AITaskAssignmentService.calculate_task_priority(task)
    
    # 详细分析
    analysis = {
        'worker': {
            'user_id': worker.user_id,
            'skill_level': worker.skill_level,
            'efficiency_score': float(worker.efficiency_score),
            'completed_tasks': worker.completed_tasks,
            'total_tasks': worker.total_tasks
        },
        'task': {
            'task_id': task.id,
            'task_no': task.task_no,
            'task_type': task.task_type,
            'priority': task.priority,
            'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S')
        },
        'scores': {
            'fitness_score': fitness,
            'task_priority_score': task_priority,
            'combined_score': round(fitness * 0.6 + task_priority * 0.4, 2)
        }
    }
    
    return jsonify({
        'success': True,
        'data': analysis
    })


@ai_task_assignment_bp.route('/predict/duration', methods=['POST'])
def predict_duration():
    """预测任务耗时"""
    data = request.get_json()
    
    task_id = data.get('task_id', type=int)
    
    if not task_id:
        return jsonify({'success': False, 'message': '任务 ID 不能为空'}), 400
    
    task = WarehouseTask.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    estimated_time = AITaskAssignmentService.predict_task_duration(task)
    
    return jsonify({
        'success': True,
        'data': {
            'task_id': task_id,
            'task_no': task.task_no,
            'estimated_duration_minutes': estimated_time
        }
    })


# ==================== 统计 API ====================

@ai_task_assignment_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    # 任务统计
    total_tasks = WarehouseTask.query.count()
    pending_tasks = WarehouseTask.query.filter_by(status='pending').count()
    assigned_tasks = WarehouseTask.query.filter_by(status='assigned').count()
    working_tasks = WarehouseTask.query.filter_by(status='working').count()
    completed_tasks = WarehouseTask.query.filter_by(status='completed').count()
    
    # 工人统计
    total_workers = Worker.query.count()
    available_workers = Worker.query.filter_by(status='available').count()
    busy_workers = Worker.query.filter_by(status='busy').count()
    
    # 平均适配度
    avg_fitness = 0
    # TODO: 计算平均适配度
    
    stats = {
        'tasks': {
            'total': total_tasks,
            'pending': pending_tasks,
            'assigned': assigned_tasks,
            'working': working_tasks,
            'completed': completed_tasks
        },
        'workers': {
            'total': total_workers,
            'available': available_workers,
            'busy': busy_workers
        },
        'ai_metrics': {
            'avg_fitness_score': avg_fitness
        }
    }
    
    if warehouse_id:
        stats['warehouse_tasks'] = WarehouseTask.query.filter_by(warehouse_id=warehouse_id).count()
        stats['warehouse_workers'] = Worker.query.filter_by(warehouse_id=warehouse_id).count()
    
    return jsonify({
        'success': True,
        'data': stats
    })
