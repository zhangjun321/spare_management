# -*- coding: utf-8 -*-
"""
调拨单 API — 跨仓库调拨与在途库存管理

状态机: draft → submitted → approved → in_transit → received → completed
"""
from flask import Blueprint, request
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.utils.response import ok, error
from app.utils.transaction import transactional
from app.models.transfer_order import TransferOrder, TransferOrderItem
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from datetime import datetime
import random

transfer_order_bp = Blueprint('transfer_order', __name__, url_prefix='/api/transfer-orders')
csrf.exempt(transfer_order_bp)


def _make_code(prefix='TO'):
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rnd = ''.join(str(random.randint(0, 9)) for _ in range(4))
    return f'{prefix}{ts[-8:]}{rnd}'


# ── 列表 ──

@transfer_order_bp.route('', methods=['GET'])
@login_required
def list_orders():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        from_wh = request.args.get('from_warehouse_id', type=int)
        to_wh = request.args.get('to_warehouse_id', type=int)
        keyword = request.args.get('keyword')

        q = TransferOrder.query
        if status:
            q = q.filter_by(status=status)
        if from_wh:
            q = q.filter_by(from_warehouse_id=from_wh)
        if to_wh:
            q = q.filter_by(to_warehouse_id=to_wh)
        if keyword:
            q = q.filter(TransferOrder.order_code.contains(keyword))

        pagination = q.order_by(TransferOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        return ok(data={
            'items': [o.to_dict() for o in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        })
    except Exception as e:
        return error(message=str(e))


# ── 详情 ──

@transfer_order_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_order(id):
    try:
        order = TransferOrder.query.get(id)
        if not order:
            return error(message='调拨单不存在', code=404)
        return ok(data=order.to_dict())
    except Exception as e:
        return error(message=str(e))


# ── 创建 ──

@transfer_order_bp.route('', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        if not data:
            return error(message='请求数据为空', code=400)

        from_wh = data.get('from_warehouse_id')
        to_wh = data.get('to_warehouse_id')
        items_data = data.get('items', [])

        if not from_wh or not to_wh:
            return error(message='调出和调入仓库不能为空', code=400)
        if from_wh == to_wh:
            return error(message='调出和调入仓库不能相同', code=400)
        if not items_data:
            return error(message='至少需要一个调拨备件', code=400)

        with transactional():
            order = TransferOrder(
                order_code=_make_code('TO'),
                from_warehouse_id=from_wh,
                to_warehouse_id=to_wh,
                status='draft',
                requester_id=current_user.id,
                remark=data.get('remark'),
                eta=datetime.strptime(data['eta'], '%Y-%m-%d %H:%M:%S') if data.get('eta') else None,
            )
            db.session.add(order)
            db.session.flush()

            for it in items_data:
                item = TransferOrderItem(
                    transfer_id=order.id,
                    spare_part_id=it['spare_part_id'],
                    quantity=it['quantity'],
                    batch_no=it.get('batch_no'),
                    item_status='pending',
                )
                db.session.add(item)

        return ok(data=order.to_dict(), message='调拨单创建成功')
    except ValueError as e:
        return error(message=str(e), code=400)
    except Exception as e:
        return error(message=str(e))


# ── 更新草稿 ──

@transfer_order_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_order(id):
    try:
        data = request.get_json()
        if not data:
            return error(message='请求数据为空', code=400)

        with transactional():
            order = TransferOrder.query.get(id)
            if not order:
                return error(message='调拨单不存在', code=404)
            if order.status != 'draft':
                return error(message='只能编辑草稿状态的调拨单', code=400)

            if 'remark' in data:
                order.remark = data['remark']
            if 'eta' in data and data['eta']:
                order.eta = datetime.strptime(data['eta'], '%Y-%m-%d %H:%M:%S')
            if 'from_warehouse_id' in data:
                order.from_warehouse_id = data['from_warehouse_id']
            if 'to_warehouse_id' in data:
                order.to_warehouse_id = data['to_warehouse_id']

            # 更新明细
            if 'items' in data:
                TransferOrderItem.query.filter_by(transfer_id=id).delete()
                for it in data['items']:
                    item = TransferOrderItem(
                        transfer_id=order.id,
                        spare_part_id=it['spare_part_id'],
                        quantity=it['quantity'],
                        batch_no=it.get('batch_no'),
                        item_status='pending',
                    )
                    db.session.add(item)

        return ok(data=order.to_dict(), message='调拨单更新成功')
    except Exception as e:
        return error(message=str(e))


# ── 状态流转 ──

@transfer_order_bp.route('/<int:id>/transit', methods=['POST'])
@login_required
def transit_order(id):
    """状态流转: submitted/approved/ship/receive/cancel"""
    try:
        data = request.get_json()
        if not data:
            return error(message='请求数据为空', code=400)

        target = data.get('target')
        if target not in ('submitted', 'approved', 'ship', 'receive', 'cancel', 'complete'):
            return error(message=f'无效的目标状态: {target}', code=400)

        # Map frontend terms to model states
        STATE_MAP = {
            'submitted': 'submitted',
            'approved': 'approved',
            'ship': 'in_transit',
            'receive': 'received',
            'complete': 'completed',
            'cancel': 'cancelled',
        }
        model_target = STATE_MAP[target]

        with transactional():
            order = TransferOrder.query.get(id)
            if not order:
                return error(message='调拨单不存在', code=404)

            if target == 'cancel':
                order.cancel_reason = data.get('reason', '')
                order.transit(model_target, current_user.id)
            elif target == 'submitted':
                # 提交时检查库存是否足够
                for item in order.items:
                    part = SparePart.query.get(item.spare_part_id)
                    if not part:
                        return error(message=f'备件({item.spare_part_id})不存在', code=400)
                    available = float(part.current_stock or 0)
                    needed = float(item.quantity or 0)
                    if available < needed:
                        return error(message=f'{part.name}库存不足(可用{available}, 需要{needed})', code=400)
                order.transit(model_target, current_user.id)
            elif target == 'receive':
                # 收货时更新收货数量
                for item in order.items:
                    received = float(item.quantity or 0)
                    item.received_quantity = received
                    item.item_status = 'received'
                order.transit(model_target, current_user.id)
            else:
                order.transit(model_target, current_user.id)

        return ok(data=order.to_dict(), message=f'调拨单已{target}')
    except ValueError as e:
        return error(message=str(e), code=400)
    except Exception as e:
        return error(message=str(e))


# ── 删除草稿 ──

@transfer_order_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_order(id):
    try:
        with transactional():
            order = TransferOrder.query.get(id)
            if not order:
                return error(message='调拨单不存在', code=404)
            if order.status != 'draft':
                return error(message='只能删除草稿状态的调拨单', code=400)
            TransferOrderItem.query.filter_by(transfer_id=id).delete()
            db.session.delete(order)
        return ok(message='调拨单已删除')
    except Exception as e:
        return error(message=str(e))


# ── 统计 ──

@transfer_order_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        from sqlalchemy import func
        stats = {}
        for st in ['draft', 'submitted', 'approved', 'in_transit', 'received', 'completed']:
            stats[st] = TransferOrder.query.filter_by(status=st).count()
        total = sum(stats.values())
        return ok(data={'by_status': stats, 'total': total})
    except Exception as e:
        return error(message=str(e))
