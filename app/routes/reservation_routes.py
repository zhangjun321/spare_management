# -*- coding: utf-8 -*-
"""
库存预留 API — 项目/订单维度预留、释放、到期自动处理
"""
from flask import Blueprint, request
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.utils.response import ok, error
from app.utils.transaction import transactional
from app.models.reservation import Reservation
from app.models.spare_part import SparePart
from datetime import datetime, timedelta
import random

reservation_bp = Blueprint('reservation', __name__, url_prefix='/api/reservations')
csrf.exempt(reservation_bp)


def _make_code(prefix='RS'):
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rnd = ''.join(str(random.randint(0, 9)) for _ in range(4))
    return f'{prefix}{ts[-8:]}{rnd}'


# ── 列表 ──

@reservation_bp.route('', methods=['GET'])
@login_required
def list_reservations():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        spare_part_id = request.args.get('spare_part_id', type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        project = request.args.get('project')

        q = Reservation.query
        if status:
            q = q.filter_by(status=status)
        if spare_part_id:
            q = q.filter_by(spare_part_id=spare_part_id)
        if warehouse_id:
            q = q.filter_by(warehouse_id=warehouse_id)
        if project:
            q = q.filter(Reservation.project.contains(project))

        pagination = q.order_by(Reservation.priority.desc(), Reservation.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)

        return ok(data={
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        })
    except Exception as e:
        return error(message=str(e))


# ── 详情 ──

@reservation_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_reservation(id):
    try:
        r = Reservation.query.get(id)
        if not r:
            return error(message='预留记录不存在', code=404)
        return ok(data=r.to_dict())
    except Exception as e:
        return error(message=str(e))


# ── 创建预留 ──

@reservation_bp.route('', methods=['POST'])
@login_required
def create_reservation():
    try:
        data = request.get_json()
        if not data:
            return error(message='请求数据为空', code=400)

        spare_part_id = data.get('spare_part_id')
        quantity = data.get('quantity')
        expire_days = data.get('expire_days', 30)
        warehouse_id = data.get('warehouse_id')

        if not spare_part_id or not quantity:
            return error(message='备件和数量不能为空', code=400)

        # 检查库存可用量
        part = SparePart.query.get(spare_part_id)
        if not part:
            return error(message='备件不存在', code=404)

        # 计算已被预留的总量
        active_reservations = Reservation.query.filter_by(
            spare_part_id=spare_part_id, status='active'
        ).all()
        reserved_total = sum(float(r.quantity or 0) - float(r.released_quantity or 0)
                             for r in active_reservations)
        available = float(part.current_stock or 0) - reserved_total

        if available < float(quantity):
            return error(
                message=f'{part.name}可用库存不足(可用{available}, 已预留{reserved_total}, 请求{quantity})',
                code=400)

        with transactional():
            expire_at = datetime.utcnow() + timedelta(days=expire_days)
            r = Reservation(
                reservation_code=_make_code('RS'),
                spare_part_id=spare_part_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                project=data.get('project'),
                order_ref=data.get('order_ref'),
                reason=data.get('reason'),
                priority=data.get('priority', 5),
                expire_at=expire_at,
                status='active',
                created_by=current_user.id,
            )
            db.session.add(r)

        return ok(data=r.to_dict(), message='预留成功')
    except Exception as e:
        return error(message=str(e))


# ── 释放预留 ──

@reservation_bp.route('/<int:id>/release', methods=['POST'])
@login_required
def release_reservation(id):
    try:
        data = request.get_json(silent=True) or {}
        partial_qty = data.get('quantity')

        with transactional():
            r = Reservation.query.get(id)
            if not r:
                return error(message='预留记录不存在', code=404)
            if r.status != 'active':
                return error(message='只能释放活跃状态的预留', code=400)

            qty = float(partial_qty) if partial_qty else float(r.quantity or 0) - float(r.released_quantity or 0)
            if qty <= 0:
                return error(message='无可释放数量', code=400)

            r.released_quantity = float(r.released_quantity or 0) + qty
            r.released_at = datetime.utcnow()
            r.released_by = current_user.id

            # 全部释放则标记状态
            remaining = float(r.quantity or 0) - float(r.released_quantity or 0)
            if remaining <= 0.001:
                r.status = 'released'

        return ok(data=r.to_dict(), message=f'已释放 {qty}')
    except Exception as e:
        return error(message=str(e))


# ── 延长预留 ──

@reservation_bp.route('/<int:id>/extend', methods=['POST'])
@login_required
def extend_reservation(id):
    try:
        data = request.get_json()
        if not data or not data.get('days'):
            return error(message='请指定延长天数', code=400)

        with transactional():
            r = Reservation.query.get(id)
            if not r:
                return error(message='预留记录不存在', code=404)
            if r.status != 'active':
                return error(message='只能延长活跃状态的预留', code=400)

            days = int(data['days'])
            if r.expire_at:
                r.expire_at = r.expire_at + timedelta(days=days)
            else:
                r.expire_at = datetime.utcnow() + timedelta(days=days)

        return ok(data=r.to_dict(), message=f'预留已延长 {days} 天')
    except Exception as e:
        return error(message=str(e))


# ── 到期自动释放 ──

@reservation_bp.route('/release-expired', methods=['POST'])
@login_required
def release_expired():
    """批量释放已过期的预留"""
    try:
        with transactional():
            now = datetime.utcnow()
            expired = Reservation.query.filter(
                Reservation.status == 'active',
                Reservation.expire_at < now
            ).all()

            count = len(expired)
            for r in expired:
                r.status = 'released'
                r.released_at = now
                r.released_quantity = r.quantity

        return ok(data={'count': count}, message=f'已释放 {count} 条过期预留')
    except Exception as e:
        return error(message=str(e))


# ── 统计 ──

@reservation_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        active_count = Reservation.query.filter_by(status='active').count()
        expired_count = Reservation.query.filter(
            Reservation.status == 'active',
            Reservation.expire_at < datetime.utcnow()
        ).count()

        return ok(data={
            'active_count': active_count,
            'expired_count': expired_count,
            'total_count': Reservation.query.count(),
        })
    except Exception as e:
        return error(message=str(e))
