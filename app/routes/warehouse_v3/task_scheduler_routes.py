from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.task_scheduler_service import TaskQueueService, TaskSchedulerService, WorkerService
from app.models.warehouse_v3.task_scheduler import TaskQueue, WarehouseTask, TaskScheduler, Worker
from datetime import datetime

task_scheduler_bp = Blueprint('task_scheduler', __name__, url_prefix='/api/task-scheduler')


# ==================== 任务队列 API ====================

@task_scheduler_bp.route('/queue/create', methods=['POST'])
def create_queue():
    """创建任务队列"""
    data = request.get_json()
    
    queue_name = data.get('queue_name')
    warehouse_id = data.get('warehouse_id', type=int)
    queue_type = data.get('queue_type')
    priority = data.get('priority', 5)
    max_capacity = data.get('max_capacity', 1000)
    
    if not queue_name or not queue_type:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    queue = TaskQueueService.create_queue(
        queue_name=queue_name,
        warehouse_id=warehouse_id,
        queue_type=queue_type,
        priority=priority,
        max_capacity=max_capacity
    )
    
    return jsonify({
        'success': True,
        'message': '任务队列创建成功',
        'data': queue.to_dict()
    })


@task_scheduler_bp.route('/queue/list', methods=['GET'])
def get_queue_list():
    """获取任务队列列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    queue_type = request.args.get('queue_type')
    status = request.args.get('status')
    
    query = TaskQueue.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if queue_type:
        query = query.filter_by(queue_type=queue_type)
    if status:
        query = query.filter_by(status=status)
    
    queues = query.order_by(TaskQueue.priority.asc(), TaskQueue.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [queue.to_dict() for queue in queues]
    })


@task_scheduler_bp.route('/queue/<int:queue_id>/status', methods=['GET'])
def get_queue_status(queue_id):
    """获取队列状态"""
    status = TaskQueueService.get_queue_status(queue_id)
    
    if not status:
        return jsonify({'success': False, 'message': '队列不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': status
    })


@task_scheduler_bp.route('/queue/<int:queue_id>/enqueue', methods=['POST'])
def enqueue_task(queue_id):
    """添加任务到队列"""
    data = request.get_json()
    
    data['queue_id'] = queue_id
    
    task = TaskQueueService.enqueue(data)
    
    if not task:
        return jsonify({'success': False, 'message': '队列已满或不存在'}), 400
    
    return jsonify({
        'success': True,
        'message': '任务已添加到队列',
        'data': task.to_dict()
    })


# ==================== 任务调度 API ====================

@task_scheduler_bp.route('/schedule', methods=['POST'])
def schedule_tasks():
    """调度任务"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    scheduler_type = data.get('scheduler_type', 'PRIORITY')
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    result = TaskSchedulerService.schedule_tasks(warehouse_id, scheduler_type)
    
    return jsonify(result)


@task_scheduler_bp.route('/task/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """分配任务"""
    data = request.get_json()
    user_id = data.get('user_id', type=int)
    
    if not user_id:
        return jsonify({'success': False, 'message': '用户 ID 不能为空'}), 400
    
    task = TaskSchedulerService.assign_task_to_worker(task_id, user_id)
    
    if not task:
        return jsonify({'success': False, 'message': '任务或工人不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '任务已分配',
        'data': task.to_dict()
    })


@task_scheduler_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """开始任务"""
    task = TaskSchedulerService.start_task(task_id)
    
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '任务已开始',
        'data': task.to_dict()
    })


@task_scheduler_bp.route('/task/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    data = request.get_json()
    actual_time = data.get('actual_time', type=int)
    
    task = TaskSchedulerService.complete_task(task_id, actual_time)
    
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '任务已完成',
        'data': task.to_dict()
    })


# ==================== 任务查询 API ====================

@task_scheduler_bp.route('/task/list', methods=['GET'])
def get_task_list():
    """获取任务列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    queue_id = request.args.get('queue_id', type=int)
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to', type=int)
    task_type = request.args.get('task_type')
    
    query = WarehouseTask.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if queue_id:
        query = query.filter_by(queue_id=queue_id)
    if status:
        query = query.filter_by(status=status)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    if task_type:
        query = query.filter_by(task_type=task_type)
    
    tasks = query.order_by(WarehouseTask.priority.asc(), WarehouseTask.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [task.to_dict() for task in tasks]
    })


@task_scheduler_bp.route('/task/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取任务详情"""
    task = WarehouseTask.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': task.to_dict()
    })


# ==================== 工人管理 API ====================

@task_scheduler_bp.route('/worker/list', methods=['GET'])
def get_worker_list():
    """获取工人列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status')
    
    query = Worker.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if status:
        query = query.filter_by(status=status)
    
    workers = query.order_by(Worker.efficiency_score.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [worker.to_dict() for worker in workers]
    })


@task_scheduler_bp.route('/worker/available', methods=['GET'])
def get_available_workers():
    """获取可用工人"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    workers = WorkerService.get_available_workers(warehouse_id)
    
    return jsonify({
        'success': True,
        'data': workers
    })


@task_scheduler_bp.route('/worker/statistics', methods=['GET'])
def get_worker_statistics():
    """获取工人统计"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    stats = WorkerService.get_worker_statistics(warehouse_id)
    
    return jsonify({
        'success': True,
        'data': stats
    })


# ==================== 调度器配置 API ====================

@task_scheduler_bp.route('/scheduler/list', methods=['GET'])
def get_scheduler_list():
    """获取调度器列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    is_active = request.args.get('is_active')
    
    query = TaskScheduler.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if is_active is not None:
        query = query.filter_by(is_active=(is_active.lower() == 'true'))
    
    schedulers = query.all()
    
    return jsonify({
        'success': True,
        'data': [scheduler.to_dict() for scheduler in schedulers]
    })


@task_scheduler_bp.route('/scheduler/create', methods=['POST'])
def create_scheduler():
    """创建调度器"""
    data = request.get_json()
    
    scheduler_name = data.get('scheduler_name')
    warehouse_id = data.get('warehouse_id', type=int)
    scheduler_type = data.get('scheduler_type')
    is_active = data.get('is_active', True)
    config = data.get('config', {})
    
    if not scheduler_name or not scheduler_type:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    scheduler = TaskScheduler(
        scheduler_name=scheduler_name,
        warehouse_id=warehouse_id,
        scheduler_type=scheduler_type,
        is_active=is_active,
        config=json.dumps(config)
    )
    
    db.session.add(scheduler)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '调度器创建成功',
        'data': scheduler.to_dict()
    })


# ==================== 统计 API ====================

@task_scheduler_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    # 任务统计
    total_tasks = WarehouseTask.query.count()
    pending_tasks = WarehouseTask.query.filter_by(status='pending').count()
    working_tasks = WarehouseTask.query.filter_by(status='working').count()
    completed_tasks = WarehouseTask.query.filter_by(status='completed').count()
    
    # 队列统计
    total_queues = TaskQueue.query.count()
    active_queues = TaskQueue.query.filter_by(status='active').count()
    
    # 工人统计
    worker_stats = WorkerService.get_worker_statistics(warehouse_id)
    
    return jsonify({
        'success': True,
        'data': {
            'tasks': {
                'total': total_tasks,
                'pending': pending_tasks,
                'working': working_tasks,
                'completed': completed_tasks
            },
            'queues': {
                'total': total_queues,
                'active': active_queues
            },
            'workers': worker_stats
        }
    })
