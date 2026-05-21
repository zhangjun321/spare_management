# -*- coding: utf-8 -*-
"""
盘点任务 API — 可配置盘点、扫码盘点、差异处理与审批
"""
from flask import Blueprint, request
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.utils.response import ok, error
from app.utils.transaction import transactional
from app.models.stock_take import StockTakeTask, StockTakeItem, AdjustmentOrder
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from datetime import datetime
import random

stock_take_bp = Blueprint('stock_take', __name__, url_prefix='/api/stock-take')
csrf.exempt(stock_take_bp)


def _make_code(prefix='ST'):
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rnd = ''.join(str(random.randint(0, 9)) for _ in range(4))
    return f'{prefix}{ts[-8:]}{rnd}'


# ═══════════════ 盘点任务 CRUD ═══════════════

@stock_take_bp.route('/tasks', methods=['GET'])
@login_required
def list_tasks():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        warehouse_id = request.args.get('warehouse_id', type=int)

        q = StockTakeTask.query
        if status:
            q = q.filter_by(status=status)
        if warehouse_id:
            q = q.filter_by(warehouse_id=warehouse_id)

        pagination = q.order_by(StockTakeTask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        return ok(data={
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        })
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:id>', methods=['GET'])
@login_required
def get_task(id):
    try:
        task = StockTakeTask.query.get(id)
        if not task:
            return error(message='盘点任务不存在', code=404)

        data = task.to_dict()
        data['items'] = [it.to_dict() for it in (task.items or [])]
        data['adjustment_orders'] = [
            ao.to_dict() for ao in
            AdjustmentOrder.query.filter_by(task_id=id).order_by(AdjustmentOrder.created_at.desc()).all()
        ]
        return ok(data=data)
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return error(message='任务标题不能为空', code=400)

        with transactional():
            task = StockTakeTask(
                task_code=_make_code('ST'),
                title=data['title'],
                scope_type=data.get('scope_type', 'warehouse'),
                scope_value=data.get('scope_value'),
                warehouse_id=data.get('warehouse_id'),
                assignee_ids=data.get('assignee_ids'),
                assignee_names=data.get('assignee_names'),
                deadline=datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S') if data.get('deadline') else None,
                approval_required=data.get('approval_required', True),
                remark=data.get('remark'),
                planner_id=current_user.id,
                status='draft',
            )
            db.session.add(task)
            db.session.flush()

            # 自动生成盘点项：根据范围查询备件
            items_data = data.get('items', [])
            if items_data:
                for it in items_data:
                    item = StockTakeItem(
                        task_id=task.id,
                        spare_part_id=it['spare_part_id'],
                        batch_no=it.get('batch_no'),
                        location_id=it.get('location_id'),
                    )
                    db.session.add(item)
            elif task.warehouse_id:
                # 按仓库自动加载所有备件作为盘点项
                parts = SparePart.query.filter_by(is_active=True).all()
                for part in parts:
                    item = StockTakeItem(
                        task_id=task.id,
                        spare_part_id=part.id,
                    )
                    db.session.add(item)

            task.recalc_stats()

        return ok(data=task.to_dict(), message='盘点任务创建成功')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:id>', methods=['PUT'])
@login_required
def update_task(id):
    try:
        data = request.get_json()
        if not data:
            return error(message='请求数据为空', code=400)

        with transactional():
            task = StockTakeTask.query.get(id)
            if not task:
                return error(message='盘点任务不存在', code=404)
            if task.status not in ('draft',):
                return error(message='只能编辑草稿状态的任务', code=400)

            for field in ('title', 'scope_type', 'scope_value', 'warehouse_id',
                          'assignee_ids', 'assignee_names', 'approval_required', 'remark'):
                if field in data:
                    setattr(task, field, data[field])
            if data.get('deadline'):
                task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')

        return ok(data=task.to_dict(), message='任务已更新')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:id>', methods=['DELETE'])
@login_required
def delete_task(id):
    try:
        with transactional():
            task = StockTakeTask.query.get(id)
            if not task:
                return error(message='盘点任务不存在', code=404)
            if task.status != 'draft':
                return error(message='只能删除草稿状态的任务', code=400)
            StockTakeItem.query.filter_by(task_id=id).delete()
            db.session.delete(task)
        return ok(message='任务已删除')
    except Exception as e:
        return error(message=str(e))


# ═══════════════ 任务状态流转 ═══════════════

@stock_take_bp.route('/tasks/<int:id>/start', methods=['POST'])
@login_required
def start_task(id):
    """开始盘点：记录系统库存快照"""
    try:
        with transactional():
            task = StockTakeTask.query.get(id)
            if not task:
                return error(message='盘点任务不存在', code=404)

            task.transit('in_progress', current_user.id)

            # 快照系统库存到盘点明细
            for item in task.items:
                part = SparePart.query.get(item.spare_part_id)
                if part:
                    item.system_qty = part.current_stock or 0

        return ok(data=task.to_dict(), message='盘点已开始，系统库存已快照')
    except ValueError as e:
        return error(message=str(e), code=400)
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:id>/complete', methods=['POST'])
@login_required
def complete_task(id):
    """完成盘点：计算差异"""
    try:
        with transactional():
            task = StockTakeTask.query.get(id)
            if not task:
                return error(message='盘点任务不存在', code=404)

            # 计算所有差异
            for item in task.items:
                if item.counted_qty is not None:
                    item.calc_diff()
                    item.item_status = 'counted'

            task.transit('pending_review', current_user.id)
            task.recalc_stats()

            # 如果不需要审批且无差异，直接完成
            if task.diff_items == 0:
                task.transit('completed', current_user.id)

        return ok(data=task.to_dict(), message='盘点已完成')
    except ValueError as e:
        return error(message=str(e), code=400)
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_task(id):
    try:
        data = request.get_json(silent=True) or {}
        with transactional():
            task = StockTakeTask.query.get(id)
            if not task:
                return error(message='盘点任务不存在', code=404)
            task.remark = (task.remark or '') + '\n取消原因: ' + data.get('reason', '手动取消')
            task.transit('cancelled', current_user.id)
        return ok(data=task.to_dict(), message='任务已取消')
    except ValueError as e:
        return error(message=str(e), code=400)
    except Exception as e:
        return error(message=str(e))


# ═══════════════ 盘点明细操作 ═══════════════

@stock_take_bp.route('/tasks/<int:task_id>/items/<int:item_id>/count', methods=['POST'])
@login_required
def count_item(task_id, item_id):
    """盘点单条"""
    try:
        data = request.get_json()
        if not data:
            return error(message='请求数据为空', code=400)

        with transactional():
            item = StockTakeItem.query.filter_by(id=item_id, task_id=task_id).first()
            if not item:
                return error(message='盘点明细不存在', code=404)
            if item.task.status != 'in_progress':
                return error(message='任务未开始，无法盘点', code=400)

            item.counted_qty = data.get('counted_qty')
            item.scan_code = data.get('scan_code')
            item.remark = data.get('remark')

            # 动态计算差异
            s = float(item.system_qty or 0)
            c = float(item.counted_qty or 0)
            item.diff_qty = c - s
            item.counted_by = current_user.id
            item.counted_at = datetime.utcnow()
            item.item_status = 'counted'

            # 更新任务统计
            item.task.recalc_stats()

        return ok(data={
            'item': item.to_dict(),
            'task_stats': {
                'total_items': item.task.total_items,
                'counted_items': item.task.counted_items,
                'diff_items': item.task.diff_items,
            }
        }, message='盘点记录已保存')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:task_id>/items/batch-count', methods=['POST'])
@login_required
def batch_count(task_id):
    """批量盘点（扫码场景）"""
    try:
        data = request.get_json()
        if not data or not data.get('items'):
            return error(message='请提供盘点数据', code=400)

        task = StockTakeTask.query.get(task_id)
        if not task:
            return error(message='盘点任务不存在', code=404)
        if task.status != 'in_progress':
            return error(message='任务未开始', code=400)

        results = []
        with transactional():
            for it_data in data['items']:
                item = StockTakeItem.query.filter_by(
                    id=it_data.get('item_id'), task_id=task_id
                ).first()
                if not item:
                    continue
                item.counted_qty = it_data.get('counted_qty')
                item.scan_code = it_data.get('scan_code')
                s = float(item.system_qty or 0)
                c = float(item.counted_qty or 0)
                item.diff_qty = c - s
                item.counted_by = current_user.id
                item.counted_at = datetime.utcnow()
                item.item_status = 'counted'
                results.append(item.to_dict())

            task.recalc_stats()

        return ok(data={'count': len(results), 'items': results}, message=f'已盘点 {len(results)} 项')
    except Exception as e:
        return error(message=str(e))


# ═══════════════ 差异调整单 ═══════════════

@stock_take_bp.route('/adjustments', methods=['GET'])
@login_required
def list_adjustments():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        task_id = request.args.get('task_id', type=int)

        q = AdjustmentOrder.query
        if status:
            q = q.filter_by(status=status)
        if task_id:
            q = q.filter_by(task_id=task_id)

        pagination = q.order_by(AdjustmentOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        return ok(data={
            'items': [a.to_dict() for a in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        })
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/tasks/<int:task_id>/adjustments/generate', methods=['POST'])
@login_required
def generate_adjustments(task_id):
    """根据差异自动生成调整单"""
    try:
        task = StockTakeTask.query.get(task_id)
        if not task:
            return error(message='盘点任务不存在', code=404)
        if task.status != 'pending_review':
            return error(message='只有待审核的任务才能生成调整单', code=400)

        created = []
        with transactional():
            for item in task.items:
                if not item.has_diff():
                    continue
                adjust_type = 'gain' if float(item.diff_qty or 0) > 0 else 'loss'
                ao = AdjustmentOrder(
                    adjust_code=_make_code('AD'),
                    task_id=task_id,
                    stock_take_item_id=item.id,
                    spare_part_id=item.spare_part_id,
                    warehouse_id=task.warehouse_id,
                    adjust_type=adjust_type,
                    adjust_qty=abs(float(item.diff_qty or 0)),
                    reason=f'盘点差异: 系统{float(item.system_qty or 0)}, 实际{float(item.counted_qty or 0)}',
                    status='draft',
                    submitted_by=current_user.id,
                )
                db.session.add(ao)
                created.append(ao)

        return ok(data={'count': len(created), 'items': [a.to_dict() for a in created]},
                  message=f'已生成 {len(created)} 条调整单')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/adjustments/<int:id>/submit', methods=['POST'])
@login_required
def submit_adjustment(id):
    try:
        with transactional():
            ao = AdjustmentOrder.query.get(id)
            if not ao:
                return error(message='调整单不存在', code=404)
            if ao.status != 'draft':
                return error(message='只能提交草稿状态的调整单', code=400)
            ao.status = 'submitted'
            ao.submitted_at = datetime.utcnow()
            ao.submitted_by = current_user.id
        return ok(data=ao.to_dict(), message='调整单已提交')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/adjustments/<int:id>/approve', methods=['POST'])
@login_required
def approve_adjustment(id):
    try:
        with transactional():
            ao = AdjustmentOrder.query.get(id)
            if not ao:
                return error(message='调整单不存在', code=404)
            if ao.status != 'submitted':
                return error(message='只能审批已提交的调整单', code=400)

            ao.status = 'approved'
            ao.approved_at = datetime.utcnow()
            ao.approved_by = current_user.id

        return ok(data=ao.to_dict(), message='调整单已审批')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/adjustments/<int:id>/reject', methods=['POST'])
@login_required
def reject_adjustment(id):
    try:
        data = request.get_json(silent=True) or {}
        with transactional():
            ao = AdjustmentOrder.query.get(id)
            if not ao:
                return error(message='调整单不存在', code=404)
            ao.status = 'rejected'
            ao.reject_reason = data.get('reason', '未说明原因')
        return ok(data=ao.to_dict(), message='调整单已驳回')
    except Exception as e:
        return error(message=str(e))


@stock_take_bp.route('/adjustments/<int:id>/apply', methods=['POST'])
@login_required
def apply_adjustment(id):
    """执行库存调整"""
    try:
        with transactional():
            ao = AdjustmentOrder.query.get(id)
            if not ao:
                return error(message='调整单不存在', code=404)
            if ao.status != 'approved':
                return error(message='只能执行已审批的调整单', code=400)

            # 更新实际库存
            part = SparePart.query.get(ao.spare_part_id)
            if part:
                if ao.adjust_type == 'gain':
                    part.current_stock = (part.current_stock or 0) + float(ao.adjust_qty or 0)
                elif ao.adjust_type == 'loss':
                    part.current_stock = max(0, (part.current_stock or 0) - float(ao.adjust_qty or 0))

            ao.status = 'applied'
            ao.applied_at = datetime.utcnow()

        return ok(data=ao.to_dict(), message='调整已应用')
    except Exception as e:
        return error(message=str(e))


# ═══════════════ 统计 ═══════════════

@stock_take_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        return ok(data={
            'tasks': {
                'draft': StockTakeTask.query.filter_by(status='draft').count(),
                'in_progress': StockTakeTask.query.filter_by(status='in_progress').count(),
                'pending_review': StockTakeTask.query.filter_by(status='pending_review').count(),
                'completed': StockTakeTask.query.filter_by(status='completed').count(),
            },
            'adjustments': {
                'draft': AdjustmentOrder.query.filter_by(status='draft').count(),
                'submitted': AdjustmentOrder.query.filter_by(status='submitted').count(),
                'approved': AdjustmentOrder.query.filter_by(status='approved').count(),
                'applied': AdjustmentOrder.query.filter_by(status='applied').count(),
            },
        })
    except Exception as e:
        return error(message=str(e))
