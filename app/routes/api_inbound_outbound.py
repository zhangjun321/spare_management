# -*- coding: utf-8 -*-
"""
入库单 / 出库单 REST API 路由
为 React 前端提供 /api/inbound 和 /api/outbound 接口
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.extensions import db, csrf
from app.models.inbound_outbound import InboundOrder, OutboundOrder
from app.utils.helpers import paginate_query

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

    query = InboundOrder.query.options(
        joinedload(InboundOrder.spare_part),
        joinedload(InboundOrder.warehouse)
    ).order_by(InboundOrder.created_at.desc())

    if inbound_type:
        query = query.filter(InboundOrder.inbound_type == inbound_type)
    if status:
        query = query.filter(InboundOrder.status == status)

    pagination = paginate_query(query, page=page, per_page=per_page)

    items = []
    for order in pagination.items:
        data = order.to_dict()
        if order.spare_part:
            data['spare_part_name'] = order.spare_part.name
        if order.warehouse:
            data['warehouse_name'] = order.warehouse.name
        items.append(data)

    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'total': pagination.total
        },
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@api_inbound_bp.route('/orders/pending', methods=['GET'])
@login_required
def list_pending_inbound():
    """获取待处理入库单"""
    orders = InboundOrder.query.filter(
        InboundOrder.status == 'pending'
    ).order_by(InboundOrder.created_at.desc()).limit(50).all()
    return jsonify({'success': True, 'items': [o.to_dict() for o in orders]})


@api_inbound_bp.route('/orders', methods=['POST'])
@login_required
def create_inbound_order():
    """创建入库单"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '请求数据为空'}), 400

    required = ['inbound_type', 'spare_part_id', 'warehouse_id', 'quantity']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'缺少必填字段：{field}'}), 400

    quantity = int(data['quantity'])
    if quantity <= 0:
        return jsonify({'success': False, 'error': '入库数量必须大于 0'}), 400

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
        db.session.commit()
        return jsonify({'success': True, 'data': order.to_dict(), 'message': '入库单创建成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'创建失败：{str(e)}'}), 500


@api_inbound_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_inbound_order(order_id):
    """完成入库单"""
    order = InboundOrder.query.get_or_404(order_id)
    if order.status not in ('pending', 'partial'):
        return jsonify({'success': False, 'error': f'当前状态 {order.status} 不可完成'}), 400
    try:
        order.status = 'completed'
        order.completed_at = datetime.utcnow()
        order.completed_by = current_user.id
        db.session.commit()
        return jsonify({'success': True, 'message': '入库完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_inbound_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_inbound_order(order_id):
    """取消入库单"""
    order = InboundOrder.query.get_or_404(order_id)
    if order.status in ('completed', 'cancelled'):
        return jsonify({'success': False, 'error': f'当前状态 {order.status} 不可取消'}), 400
    try:
        order.status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': '已取消'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


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

    query = OutboundOrder.query.options(
        joinedload(OutboundOrder.spare_part),
        joinedload(OutboundOrder.warehouse)
    ).order_by(OutboundOrder.created_at.desc())

    if outbound_type:
        query = query.filter(OutboundOrder.outbound_type == outbound_type)
    if status:
        query = query.filter(OutboundOrder.status == status)

    pagination = paginate_query(query, page=page, per_page=per_page)

    items = []
    for order in pagination.items:
        data = order.to_dict()
        if order.spare_part:
            data['spare_part_name'] = order.spare_part.name
        if order.warehouse:
            data['warehouse_name'] = order.warehouse.name
        items.append(data)

    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'total': pagination.total
        },
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@api_outbound_bp.route('/orders/pending', methods=['GET'])
@login_required
def list_pending_outbound():
    """获取待处理出库单"""
    orders = OutboundOrder.query.filter(
        OutboundOrder.status == 'pending'
    ).order_by(OutboundOrder.created_at.desc()).limit(50).all()
    return jsonify({'success': True, 'items': [o.to_dict() for o in orders]})


@api_outbound_bp.route('/orders', methods=['POST'])
@login_required
def create_outbound_order():
    """创建出库单，校验数量 > 0"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '请求数据为空'}), 400

    required = ['outbound_type', 'spare_part_id', 'warehouse_id', 'quantity']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'缺少必填字段：{field}'}), 400

    quantity = int(data['quantity'])
    if quantity <= 0:
        return jsonify({'success': False, 'error': '出库数量必须大于 0'}), 400

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
        db.session.commit()
        return jsonify({'success': True, 'data': order.to_dict(), 'message': '出库单创建成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'创建失败：{str(e)}'}), 500


@api_outbound_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_outbound_order(order_id):
    """完成出库单"""
    order = OutboundOrder.query.get_or_404(order_id)
    if order.status not in ('pending', 'partial'):
        return jsonify({'success': False, 'error': f'当前状态 {order.status} 不可完成'}), 400
    try:
        order.status = 'completed'
        order.completed_at = datetime.utcnow()
        order.completed_by = current_user.id
        db.session.commit()
        return jsonify({'success': True, 'message': '出库完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_outbound_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_outbound_order(order_id):
    """取消出库单"""
    order = OutboundOrder.query.get_or_404(order_id)
    if order.status in ('completed', 'cancelled'):
        return jsonify({'success': False, 'error': f'当前状态 {order.status} 不可取消'}), 400
    try:
        order.status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': '已取消'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
