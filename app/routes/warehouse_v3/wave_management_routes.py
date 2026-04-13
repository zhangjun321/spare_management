from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.wave_management_service import WaveGenerationService, WaveTaskService
from app.models.warehouse_v3.wave_management import WavePlan, WaveOrder, WaveOrderItem, WaveTask, WaveTaskItem

wave_management_bp = Blueprint('wave_management', __name__, url_prefix='/api/wave-management')


# ==================== 波次计划 API ====================

@wave_management_bp.route('/plan/create', methods=['POST'])
def create_plan():
    """创建波次计划"""
    data = request.get_json()
    
    plan_code = data.get('plan_code')
    plan_name = data.get('plan_name')
    warehouse_id = data.get('warehouse_id', type=int)
    strategy_type = data.get('strategy_type')
    priority = data.get('priority', 1)
    time_window = data.get('time_window', type=int)
    max_orders = data.get('max_orders', type=int)
    max_items = data.get('max_items', type=int)
    route_filter = data.get('route_filter')
    carrier_filter = data.get('carrier_filter')
    remark = data.get('remark')
    
    if not plan_code or not plan_name or not strategy_type:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    plan = WavePlan(
        plan_code=plan_code,
        plan_name=plan_name,
        warehouse_id=warehouse_id,
        strategy_type=strategy_type,
        priority=priority,
        time_window=time_window,
        max_orders=max_orders,
        max_items=max_items,
        route_filter=route_filter,
        carrier_filter=carrier_filter,
        status='active',
        created_by=1,  # TODO: 从当前用户获取
        remark=remark
    )
    
    db.session.add(plan)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '波次计划创建成功',
        'data': plan.to_dict()
    })


@wave_management_bp.route('/plan/list', methods=['GET'])
def get_plan_list():
    """获取波次计划列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status')
    strategy_type = request.args.get('strategy_type')
    
    query = WavePlan.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if status:
        query = query.filter_by(status=status)
    if strategy_type:
        query = query.filter_by(strategy_type=strategy_type)
    
    plans = query.order_by(WavePlan.priority.asc(), WavePlan.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [plan.to_dict() for plan in plans]
    })


@wave_management_bp.route('/plan/<int:plan_id>', methods=['GET'])
def get_plan_detail(plan_id):
    """获取波次计划详情"""
    plan = WavePlan.query.get(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': plan.to_dict()
    })


@wave_management_bp.route('/plan/<int:plan_id>/generate', methods=['POST'])
def generate_wave_by_plan(plan_id):
    """根据计划生成波次"""
    wave = WaveGenerationService.generate_by_plan(plan_id)
    
    if not wave:
        return jsonify({'success': False, 'message': '没有符合条件的订单'}), 400
    
    return jsonify({
        'success': True,
        'message': '波次生成成功',
        'data': wave.to_dict()
    })


# ==================== 波次生成 API ====================

@wave_management_bp.route('/generate/time', methods=['POST'])
def generate_by_time():
    """按时间窗口生成波次"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    time_window = data.get('time_window', 60)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    waves = WaveGenerationService.generate_by_time_window(warehouse_id, time_window)
    
    if not waves:
        return jsonify({'success': False, 'message': '没有符合条件的订单'}), 400
    
    return jsonify({
        'success': True,
        'message': f'生成{len(waves)}个波次',
        'data': [wave.to_dict() for wave in waves]
    })


@wave_management_bp.route('/generate/quantity', methods=['POST'])
def generate_by_quantity():
    """按数量阈值生成波次"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    max_orders = data.get('max_orders', 20)
    max_items = data.get('max_items', 100)
    
    if not warehouse_id:
        return jsonify({'success': False, 'message': '仓库 ID 不能为空'}), 400
    
    waves = WaveGenerationService.generate_by_quantity(warehouse_id, max_orders, max_items)
    
    if not waves:
        return jsonify({'success': False, 'message': '没有符合条件的订单'}), 400
    
    return jsonify({
        'success': True,
        'message': f'生成{len(waves)}个波次',
        'data': [wave.to_dict() for wave in waves]
    })


# ==================== 波次订单 API ====================

@wave_management_bp.route('/wave/list', methods=['GET'])
def get_wave_list():
    """获取波次列表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status')
    plan_id = request.args.get('plan_id', type=int)
    
    query = WaveOrder.query
    
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    if status:
        query = query.filter_by(status=status)
    if plan_id:
        query = query.filter_by(plan_id=plan_id)
    
    waves = query.order_by(WaveOrder.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [wave.to_dict() for wave in waves]
    })


@wave_management_bp.route('/wave/<int:wave_id>', methods=['GET'])
def get_wave_detail(wave_id):
    """获取波次详情"""
    wave = WaveOrder.query.get(wave_id)
    if not wave:
        return jsonify({'success': False, 'message': '波次不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': wave.to_dict()
    })


@wave_management_bp.route('/wave/<int:wave_id>/items', methods=['GET'])
def get_wave_items(wave_id):
    """获取波次订单项"""
    items = WaveOrderItem.query.filter_by(wave_id=wave_id).all()
    
    return jsonify({
        'success': True,
        'data': [item.to_dict() for item in items]
    })


@wave_management_bp.route('/wave/<int:wave_id>/start', methods=['POST'])
def start_wave(wave_id):
    """开始波次拣货"""
    wave = WaveOrder.query.get(wave_id)
    if not wave:
        return jsonify({'success': False, 'message': '波次不存在'}), 404
    
    # 创建拣货任务
    tasks = WaveTaskService.create_picking_tasks(wave_id)
    
    return jsonify({
        'success': True,
        'message': f'波次已启动，创建{len(tasks)}个拣货任务',
        'data': {
            'wave': wave.to_dict(),
            'tasks': [task.to_dict() for task in tasks]
        }
    })


@wave_management_bp.route('/wave/<int:wave_id>/complete', methods=['POST'])
def complete_wave(wave_id):
    """完成波次"""
    wave = WaveOrder.query.get(wave_id)
    if not wave:
        return jsonify({'success': False, 'message': '波次不存在'}), 404
    
    wave.status = 'completed'
    wave.completed_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '波次已完成',
        'data': wave.to_dict()
    })


# ==================== 拣货任务 API ====================

@wave_management_bp.route('/task/list', methods=['GET'])
def get_task_list():
    """获取拣货任务列表"""
    wave_id = request.args.get('wave_id', type=int)
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to', type=int)
    
    query = WaveTask.query
    
    if wave_id:
        query = query.filter_by(wave_id=wave_id)
    if status:
        query = query.filter_by(status=status)
    if assigned_to:
        query = query.filter_by(assigned_to=assigned_to)
    
    tasks = query.order_by(WaveTask.route_sequence.asc()).all()
    
    return jsonify({
        'success': True,
        'data': [task.to_dict() for task in tasks]
    })


@wave_management_bp.route('/task/<int:task_id>', methods=['GET'])
def get_task_detail(task_id):
    """获取任务详情"""
    task = WaveTask.query.get(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': task.to_dict()
    })


@wave_management_bp.route('/task/<int:task_id>/items', methods=['GET'])
def get_task_items(task_id):
    """获取任务明细"""
    items = WaveTaskItem.query.filter_by(task_id=task_id).all()
    
    return jsonify({
        'success': True,
        'data': [item.to_dict() for item in items]
    })


@wave_management_bp.route('/task/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """分配任务"""
    data = request.get_json()
    user_id = data.get('user_id', 1)  # TODO: 从当前用户获取
    
    task = WaveTaskService.assign_task(task_id, user_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '任务已分配',
        'data': task.to_dict()
    })


@wave_management_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """开始任务"""
    task = WaveTaskService.start_task(task_id)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '任务已开始',
        'data': task.to_dict()
    })


@wave_management_bp.route('/task/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    data = request.get_json()
    actual_time = data.get('actual_time', type=int)
    
    task = WaveTaskService.complete_task(task_id, actual_time)
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '任务已完成',
        'data': task.to_dict()
    })


# ==================== 统计 API ====================

@wave_management_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取概览统计"""
    # 今日波次数
    today = datetime.now().date()
    today_waves = WaveOrder.query.filter(
        func.date(WaveOrder.created_at) == today
    ).count()
    
    # 进行中波次
    picking_waves = WaveOrder.query.filter_by(status='picking').count()
    
    # 待处理任务
    pending_tasks = WaveTask.query.filter_by(status='pending').count()
    
    # 进行中任务
    working_tasks = WaveTask.query.filter_by(status='working').count()
    
    return jsonify({
        'success': True,
        'data': {
            'today_waves': today_waves,
            'picking_waves': picking_waves,
            'pending_tasks': pending_tasks,
            'working_tasks': working_tasks
        }
    })
