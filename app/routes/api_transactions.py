# -*- coding: utf-8 -*-
"""交易管理 REST API（供 React 前端使用）—— F0-2 统一响应格式版"""

from flask import Blueprint, request, Response
from flask_login import login_required, current_user

from app.services.transaction_service import TransactionService
from app.models.transaction import InventoryLedger, Transaction
from app.extensions import db
from app.utils.response import json_response, ok, error, paginated_data, ResponseCode
from app.utils.exceptions import (
    BusinessError, ParamError, NotFoundError,
    StockInsufficientError, InvalidStatusError
)

api_transactions_bp = Blueprint('api_transactions', __name__)


@api_transactions_bp.route('/api/transactions', methods=['GET'])
@login_required
def list_transactions():
    """查询交易列表 (分页)"""
    filters = {
        'tx_type': request.args.get('tx_type'),
        'status': request.args.get('status'),
        'warehouse_id': request.args.get('warehouse_id', type=int),
        'keyword': request.args.get('keyword'),
    }
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('page_size', 20, type=int)
    pagination = TransactionService.list_transactions(filters, page, per_page)
    data = [TransactionService.to_dict(tx) for tx in pagination.items]
    return paginated_data(data, pagination.total, page, per_page)


@api_transactions_bp.route('/api/transactions/<int:tx_id>', methods=['GET'])
@login_required
def transaction_detail(tx_id):
    """查询单条交易详情"""
    tx = Transaction.query.get(tx_id)
    if not tx:
        return error(ResponseCode.NOT_FOUND, f'交易记录不存在 (ID: {tx_id})')

    detail = TransactionService.to_dict(tx, with_details=True)
    ledgers = [
        {
            'id': l.id,
            'warehouse_id': l.warehouse_id,
            'location_id': l.location_id,
            'quantity_delta': float(l.quantity_delta),
            'created_at': l.created_at.isoformat() if l.created_at else None,
        }
        for l in tx.ledgers.order_by(InventoryLedger.created_at.desc()).all()
    ]
    detail['ledgers'] = ledgers
    return ok(detail)


@api_transactions_bp.route('/api/transactions', methods=['POST'])
@login_required
def create_transaction():
    """创建新交易单"""
    payload = request.get_json() or {}
    if not payload:
        return error(ResponseCode.PARAM_ERROR, '请求体不能为空')
    try:
        TransactionService.validate_stock(payload)
        tx = TransactionService.create_transaction(payload, current_user.id)
        return ok(TransactionService.to_dict(tx), status_code=201)
    except BusinessError as e:
        raise  # 由全局 BusinessError handler 处理
    except Exception as e:
        db.session.rollback()
        raise


@api_transactions_bp.route('/api/transactions/<int:tx_id>/submit', methods=['POST'])
@login_required
def submit_transaction(tx_id):
    """提交交易单"""
    try:
        tx = TransactionService.submit_transaction(tx_id)
        return ok(TransactionService.to_dict(tx))
    except InvalidStatusError as e:
        raise
    except Exception as e:
        raise


@api_transactions_bp.route('/api/transactions/<int:tx_id>/approve', methods=['POST'])
@login_required
def approve_transaction(tx_id):
    """审批通过交易单"""
    try:
        tx = TransactionService.approve_transaction(tx_id, current_user.id)
        return ok(TransactionService.to_dict(tx))
    except InvalidStatusError as e:
        raise
    except Exception as e:
        raise


@api_transactions_bp.route('/api/transactions/<int:tx_id>/reject', methods=['POST'])
@login_required
def reject_transaction(tx_id):
    """驳回交易单"""
    payload = request.get_json() or {}
    reason = payload.get('reason')
    try:
        tx = TransactionService.reject_transaction(tx_id, reason)
        return ok(TransactionService.to_dict(tx))
    except InvalidStatusError as e:
        raise
    except Exception as e:
        raise


@api_transactions_bp.route('/api/transactions/validate', methods=['POST'])
@login_required
def validate_transaction():
    """校验库存是否充足"""
    payload = request.get_json() or {}
    if not payload:
        return error(ResponseCode.PARAM_ERROR, '请求体不能为空')
    try:
        TransactionService.validate_stock(payload)
        return ok(message='校验通过')
    except StockInsufficientError as e:
        raise
    except Exception as e:
        raise


@api_transactions_bp.route('/api/transactions/export', methods=['GET'])
@login_required
def export_transactions():
    """导出交易数据 (CSV)"""
    filters = {
        'tx_type': request.args.get('tx_type'),
        'status': request.args.get('status'),
        'warehouse_id': request.args.get('warehouse_id', type=int),
        'keyword': request.args.get('keyword'),
    }
    pagination = TransactionService.list_transactions(filters, page=1, per_page=10000)
    rows = [
        'tx_code,tx_type,status,total_qty,created_at',
    ]
    for tx in pagination.items:
        rows.append(
            f"{tx.tx_code},{tx.tx_type},{tx.status},{tx.total_qty},{tx.created_at.isoformat() if tx.created_at else ''}"
        )
    csv_data = '\n'.join(rows)
    return Response(csv_data, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=transactions.csv'
    })
