# -*- coding: utf-8 -*-
"""
入库单 / 出库单 REST API 路由
为 React 前端提供 /api/inbound 和 /api/outbound 接口
F0-2 已迁移：全部 jsonify → ok() / error() / paginated_data()
F0-3 已迁移：业务校验 → raise BusinessError / InvalidStatusError
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.extensions import db, csrf
from app.models.inbound_outbound import InboundOrder, OutboundOrder
from app.models.spare_part import SparePart
from app.utils.helpers import paginate_query
from app.utils.response import ok, error, paginated_data, ResponseCode
from app.utils.transaction import transactional
from app.utils.exceptions import (
    ParamError, NotFoundError, InvalidStatusError, BusinessError,
    ConcurrentModificationError,
)

# ==================== 入库单蓝图 ====================

api_inbound_bp = Blueprint('api_inbound', __name__, url_prefix='/api/inbound')
csrf.exempt(api_inbound_bp)

_INBOUND_ORDER_SEQ = [0]


def _gen_inbound_no():
    now = datetime.utcnow()
    _INBOUND_ORDER_SEQ[0] += 1
    return f"IN{now.strftime('%Y%m%d%H%M%S')}{_INBOUND_ORDER_SEQ[0]:04d}"


@api_inbound_bp.route('/orders', methods=['GET'])
@login_required
def list_inbound_orders():
    """获取入库单列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 200)
    inbound_type = request.args.get('inbound_type', '')
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    try:
        query = InboundOrder.query.options(
            joinedload(InboundOrder.spare_part),
            joinedload(InboundOrder.warehouse)
        ).order_by(InboundOrder.created_at.desc())

        if inbound_type:
            query = query.filter(InboundOrder.inbound_type == inbound_type)
        if status:
            query = query.filter(InboundOrder.status == status)
        if start_date:
            try:
                query = query.filter(InboundOrder.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
            except ValueError:
                pass
        if end_date:
            try:
                query = query.filter(InboundOrder.created_at < datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
            except ValueError:
                pass

        pagination = paginate_query(query, page=page, per_page=per_page)

        items = []
        for order in pagination.items:
            data = order.to_dict()
            if order.spare_part:
                data['spare_part_name'] = order.spare_part.name
            if order.warehouse:
                data['warehouse_name'] = order.warehouse.name
            items.append(data)

        return paginated_data(items=items, pagination=pagination)
    except BusinessError:
        raise
    except Exception:
        current_app.logger.exception('list_inbound_orders failed, fallback to empty result')
        # 降级返回空结果，不抛异常（前端列表页不应因查询报错而白屏）
        return ok(data={'items': [], 'total': 0})


@api_inbound_bp.route('/orders/pending', methods=['GET'])
@login_required
def list_pending_inbound():
    """获取待处理入库单"""
    try:
        orders = InboundOrder.query.filter(
            InboundOrder.status == 'pending'
        ).order_by(InboundOrder.created_at.desc()).limit(50).all()
        return ok(data=[o.to_dict() for o in orders])
    except Exception:
        current_app.logger.exception('list_pending_inbound failed, fallback to empty list')
        return ok(data=[])


@api_inbound_bp.route('/orders', methods=['POST'])
@login_required
def create_inbound_order():
    """创建入库单"""
    data = request.get_json()
    if not data:
        raise ParamError('请求数据为空')

    required = ['inbound_type', 'spare_part_id', 'warehouse_id', 'quantity']
    for field in required:
        if not data.get(field):
            raise ParamError(f'缺少必填字段：{field}')

    quantity = int(data['quantity'])
    if quantity <= 0:
        raise ParamError('入库数量必须大于 0')

    try:
        order = InboundOrder(
            order_no=_gen_inbound_no(),
            inbound_type=data['inbound_type'],
            spare_part_id=int(data['spare_part_id']),
            warehouse_id=int(data['warehouse_id']),
            location_id=data.get('location_id'),
            quantity=quantity,
            batch_number=data.get('batch_number'),
            unit_price=data.get('unit_price'),
            remark=data.get('remark'),
            status='pending',
            created_by=current_user.id
        )
        db.session.add(order)
        with transactional():
            pass  # commit only
        return ok(data=order.to_dict(), message='入库单创建成功', status_code=201)
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'创建入库单失败: {e}')


@api_inbound_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_inbound_order(order_id):
    """完成入库单 — 使用悲观锁安全更新库存"""
    order = InboundOrder.query.get(order_id)
    if not order:
        raise NotFoundError(f'入库单不存在 (ID: {order_id})')
    if order.status not in ('pending', 'partial'):
        raise InvalidStatusError(f'当前状态 {order.status} 不可完成')
    try:
        # 使用 SELECT FOR UPDATE 安全修改库存（防并发）
        SparePart.safe_stock_update(
            part_id=order.spare_part_id,
            delta=order.quantity,  # 入库为正
            reason=f'入库单 {order.order_no}',
            operator_id=current_user.id,
            warehouse_id=order.warehouse_id,
            order_no=order.order_no,
        )
        order.status = 'completed'
        order.completed_at = datetime.utcnow()
        order.completed_by = current_user.id
        with transactional():
            pass  # commit only
        return ok(message='入库完成')
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'完成入库单失败: {e}')


@api_inbound_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_inbound_order(order_id):
    """取消入库单"""
    order = InboundOrder.query.get(order_id)
    if not order:
        raise NotFoundError(f'入库单不存在 (ID: {order_id})')
    if order.status in ('completed', 'cancelled'):
        raise InvalidStatusError(f'当前状态 {order.status} 不可取消')
    try:
        order.status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        with transactional():
            pass  # commit only
        return ok(message='已取消')
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'取消入库单失败: {e}')


# ==================== 出库单蓝图 ====================

api_outbound_bp = Blueprint('api_outbound', __name__, url_prefix='/api/outbound')
csrf.exempt(api_outbound_bp)

_OUTBOUND_ORDER_SEQ = [0]


def _gen_outbound_no():
    now = datetime.utcnow()
    _OUTBOUND_ORDER_SEQ[0] += 1
    return f"OUT{now.strftime('%Y%m%d%H%M%S')}{_OUTBOUND_ORDER_SEQ[0]:04d}"


@api_outbound_bp.route('/orders', methods=['GET'])
@login_required
def list_outbound_orders():
    """获取出库单列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 200)
    outbound_type = request.args.get('outbound_type', '')
    status = request.args.get('status', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    try:
        query = OutboundOrder.query.options(
            joinedload(OutboundOrder.spare_part),
            joinedload(OutboundOrder.warehouse)
        ).order_by(OutboundOrder.created_at.desc())

        if outbound_type:
            query = query.filter(OutboundOrder.outbound_type == outbound_type)
        if status:
            query = query.filter(OutboundOrder.status == status)
        if start_date:
            try:
                query = query.filter(OutboundOrder.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
            except ValueError:
                pass
        if end_date:
            try:
                query = query.filter(OutboundOrder.created_at < datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
            except ValueError:
                pass

        pagination = paginate_query(query, page=page, per_page=per_page)

        items = []
        for order in pagination.items:
            data = order.to_dict()
            if order.spare_part:
                data['spare_part_name'] = order.spare_part.name
            if order.warehouse:
                data['warehouse_name'] = order.warehouse.name
            items.append(data)

        return paginated_data(items=items, pagination=pagination)
    except BusinessError:
        raise
    except Exception:
        current_app.logger.exception('list_outbound_orders failed, fallback to empty result')
        return ok(data={'items': [], 'total': 0})


@api_outbound_bp.route('/orders/pending', methods=['GET'])
@login_required
def list_pending_outbound():
    """获取待处理出库单"""
    try:
        orders = OutboundOrder.query.filter(
            OutboundOrder.status == 'pending'
        ).order_by(OutboundOrder.created_at.desc()).limit(50).all()
        return ok(data=[o.to_dict() for o in orders])
    except Exception:
        current_app.logger.exception('list_pending_outbound failed, fallback to empty list')
        return ok(data=[])


@api_outbound_bp.route('/orders', methods=['POST'])
@login_required
def create_outbound_order():
    """创建出库单，校验数量 > 0"""
    data = request.get_json()
    if not data:
        raise ParamError('请求数据为空')

    required = ['outbound_type', 'spare_part_id', 'warehouse_id', 'quantity']
    for field in required:
        if not data.get(field):
            raise ParamError(f'缺少必填字段：{field}')

    quantity = int(data['quantity'])
    if quantity <= 0:
        raise ParamError('出库数量必须大于 0')

    try:
        order = OutboundOrder(
            order_no=_gen_outbound_no(),
            outbound_type=data['outbound_type'],
            spare_part_id=int(data['spare_part_id']),
            warehouse_id=int(data['warehouse_id']),
            location_id=data.get('location_id'),
            quantity=quantity,
            remark=data.get('remark'),
            status='pending',
            created_by=current_user.id
        )
        db.session.add(order)
        with transactional():
            pass  # commit only
        return ok(data=order.to_dict(), message='出库单创建成功', status_code=201)
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'创建出库单失败: {e}')


@api_outbound_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_outbound_order(order_id):
    """完成出库单 — 使用悲观锁安全扣减库存（含库存不足校验）"""
    order = OutboundOrder.query.get(order_id)
    if not order:
        raise NotFoundError(f'出库单不存在 (ID: {order_id})')
    if order.status not in ('pending', 'partial'):
        raise InvalidStatusError(f'当前状态 {order.status} 不可完成')
    try:
        # 使用 SELECT FOR UPDATE 安全扣减库存（防并发 + 库存不足检测）
        SparePart.safe_stock_update(
            part_id=order.spare_part_id,
            delta=-order.quantity,  # 出库为负
            reason=f'出库单 {order.order_no}',
            operator_id=current_user.id,
            warehouse_id=order.warehouse_id,
            order_no=order.order_no,
        )
        order.status = 'completed'
        order.completed_at = datetime.utcnow()
        order.completed_by = current_user.id
        with transactional():
            pass  # commit only
        return ok(message='出库完成')
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'完成出库单失败: {e}')


@api_outbound_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_outbound_order(order_id):
    """取消出库单"""
    order = OutboundOrder.query.get(order_id)
    if not order:
        raise NotFoundError(f'出库单不存在 (ID: {order_id})')
    if order.status in ('completed', 'cancelled'):
        raise InvalidStatusError(f'当前状态 {order.status} 不可取消')
    try:
        order.status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        with transactional():
            pass  # commit only
        return ok(message='已取消')
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'取消出库单失败: {e}')
