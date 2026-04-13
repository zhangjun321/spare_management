from flask import Blueprint, request, jsonify
from app import db
from app.services.warehouse_v3.cycle_count_service import ABCClassificationService, CycleCountPlanService
from app.models.warehouse_v3.cycle_count import CycleCountPlan, CycleCountItem, ABCClassification
from datetime import datetime

cycle_count_bp = Blueprint('cycle_count', __name__, url_prefix='/api/cycle-count')


# ==================== ABC 分类 API ====================

@cycle_count_bp.route('/abc/calculate', methods=['POST'])
def calculate_abc():
    """计算 ABC 分类"""
    data = request.get_json()
    warehouse_id = data.get('warehouse_id', type=int)
    
    result = ABCClassificationService.calculate_abc_classification(warehouse_id)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@cycle_count_bp.route('/abc/list', methods=['GET'])
def get_abc_list():
    """获取 ABC 分类列表"""
    abc_class = request.args.get('class', '')  # A/B/C
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    if abc_class:
        items = ABCClassificationService.get_parts_by_class(abc_class.upper(), warehouse_id)
    else:
        # 获取所有分类
        query = ABCClassification.query
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        items = [item.to_dict() for item in query.all()]
    
    return jsonify({
        'success': True,
        'data': items
    })


@cycle_count_bp.route('/abc/due', methods=['GET'])
def get_due_for_count():
    """获取到期需要盘点的物品"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    items = ABCClassificationService.get_due_for_count(warehouse_id)
    
    return jsonify({
        'success': True,
        'data': items
    })


# ==================== 盘点计划 API ====================

@cycle_count_bp.route('/plan/create-abc', methods=['POST'])
def create_abc_plan():
    """根据 ABC 分类创建盘点计划"""
    data = request.get_json()
    
    abc_class = data.get('abc_class')  # A/B/C
    warehouse_id = data.get('warehouse_id', type=int)
    plan_name = data.get('plan_name')
    remark = data.get('remark')
    
    if not abc_class or abc_class not in ['A', 'B', 'C']:
        return jsonify({'success': False, 'message': 'ABC 分类参数错误'}), 400
    
    plan = CycleCountPlanService.create_plan_by_abc(
        abc_class=abc_class,
        warehouse_id=warehouse_id,
        plan_name=plan_name,
        remark=remark
    )
    
    return jsonify({
        'success': True,
        'message': '盘点计划创建成功',
        'data': plan.to_dict()
    })


@cycle_count_bp.route('/plan/create-periodic', methods=['POST'])
def create_periodic_plan():
    """创建定期盘点计划"""
    data = request.get_json()
    
    warehouse_id = data.get('warehouse_id', type=int)
    plan_name = data.get('plan_name')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    remark = data.get('remark')
    
    if not warehouse_id or not plan_name or not start_date or not end_date:
        return jsonify({'success': False, 'message': '参数不完整'}), 400
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': '日期格式错误'}), 400
    
    plan = CycleCountPlanService.create_periodic_plan(
        warehouse_id=warehouse_id,
        plan_name=plan_name,
        start_date=start,
        end_date=end,
        remark=remark
    )
    
    return jsonify({
        'success': True,
        'message': '盘点计划创建成功',
        'data': plan.to_dict()
    })


@cycle_count_bp.route('/plan/list', methods=['GET'])
def get_plan_list():
    """获取盘点计划列表"""
    status = request.args.get('status')
    plan_type = request.args.get('plan_type')
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    query = CycleCountPlan.query
    
    if status:
        query = query.filter_by(status=status)
    if plan_type:
        query = query.filter_by(plan_type=plan_type)
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    
    plans = query.order_by(CycleCountPlan.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [plan.to_dict() for plan in plans]
    })


@cycle_count_bp.route('/plan/<int:plan_id>', methods=['GET'])
def get_plan_detail(plan_id):
    """获取盘点计划详情"""
    plan = CycleCountPlan.query.get(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在'}), 404
    
    return jsonify({
        'success': True,
        'data': plan.to_dict()
    })


@cycle_count_bp.route('/plan/<int:plan_id>/submit', methods=['POST'])
def submit_plan(plan_id):
    """提交盘点计划审批"""
    plan = CycleCountPlanService.submit_for_approval(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '计划已提交审批',
        'data': plan.to_dict()
    })


@cycle_count_bp.route('/plan/<int:plan_id>/approve', methods=['POST'])
def approve_plan(plan_id):
    """审批盘点计划"""
    data = request.get_json()
    approved_by = data.get('approved_by', 1)  # TODO: 从当前用户获取
    
    plan = CycleCountPlanService.approve_plan(plan_id, approved_by)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '计划已批准',
        'data': plan.to_dict()
    })


@cycle_count_bp.route('/plan/<int:plan_id>/complete', methods=['POST'])
def complete_plan(plan_id):
    """完成盘点计划"""
    plan = CycleCountPlanService.complete_plan(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在或仍有未盘点项目'}), 404
    
    return jsonify({
        'success': True,
        'message': '盘点计划已完成',
        'data': plan.to_dict()
    })


# ==================== 盘点项目 API ====================

@cycle_count_bp.route('/item/list', methods=['GET'])
def get_item_list():
    """获取盘点项目列表"""
    plan_id = request.args.get('plan_id', type=int)
    status = request.args.get('status')
    
    query = CycleCountItem.query
    
    if plan_id:
        query = query.filter_by(plan_id=plan_id)
    if status:
        query = query.filter_by(status=status)
    
    items = query.all()
    
    return jsonify({
        'success': True,
        'data': [item.to_dict() for item in items]
    })


@cycle_count_bp.route('/item/<int:item_id>/count', methods=['POST'])
def count_item(item_id):
    """登记盘点结果"""
    data = request.get_json()
    
    actual_quantity = data.get('actual_quantity')
    counted_by = data.get('counted_by', 1)  # TODO: 从当前用户获取
    remark = data.get('remark')
    
    if actual_quantity is None:
        return jsonify({'success': False, 'message': '实际数量不能为空'}), 400
    
    item = CycleCountPlanService.update_count_status(
        item_id=item_id,
        actual_quantity=actual_quantity,
        counted_by=counted_by,
        remark=remark
    )
    
    if not item:
        return jsonify({'success': False, 'message': '盘点项目不存在'}), 404
    
    return jsonify({
        'success': True,
        'message': '盘点结果已登记',
        'data': item.to_dict()
    })


@cycle_count_bp.route('/plan/<int:plan_id>/items', methods=['GET'])
def get_plan_items(plan_id):
    """获取盘点计划的所有项目"""
    items = CycleCountItem.query.filter_by(plan_id=plan_id).all()
    
    return jsonify({
        'success': True,
        'data': [item.to_dict() for item in items]
    })


# ==================== 盘点统计 API ====================

@cycle_count_bp.route('/statistics/plan/<int:plan_id>', methods=['GET'])
def get_plan_statistics(plan_id):
    """获取盘点计划统计"""
    plan = CycleCountPlan.query.get(plan_id)
    if not plan:
        return jsonify({'success': False, 'message': '计划不存在'}), 404
    
    # 统计各状态数量
    total = plan.total_items
    counted = CycleCountItem.query.filter_by(plan_id=plan_id, status='counted').count()
    pending = CycleCountItem.query.filter_by(plan_id=plan_id, status='pending').count()
    variance = CycleCountItem.query.filter_by(plan_id=plan_id).filter(
        CycleCountItem.variance_quantity != 0
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'plan_id': plan_id,
            'plan_no': plan.plan_no,
            'plan_name': plan.plan_name,
            'status': plan.status,
            'total_items': total,
            'counted_items': counted,
            'pending_items': pending,
            'variance_items': variance,
            'progress': plan.get_progress()
        }
    })


@cycle_count_bp.route('/statistics/overview', methods=['GET'])
def get_overview_statistics():
    """获取盘点概览统计"""
    # 当前活跃计划数
    active_plans = CycleCountPlan.query.filter_by(status='active').count()
    
    # 待盘点项目数
    pending_items = CycleCountItem.query.filter_by(status='pending').count()
    
    # 今日已完成盘点数
    today = datetime.now().date()
    today_counted = CycleCountItem.query.filter(
        CycleCountItem.status == 'counted',
        func.date(CycleCountItem.counted_at) == today
    ).count()
    
    # 差异项目总数
    variance_items = CycleCountItem.query.filter(
        CycleCountItem.variance_quantity != 0
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'active_plans': active_plans,
            'pending_items': pending_items,
            'today_counted': today_counted,
            'variance_items': variance_items
        }
    })
