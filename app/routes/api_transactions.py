# -*- coding: utf-8 -*-
"""交易管理 REST API（供 React 前端使用）"""

from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user

from app.services.transaction_service import TransactionService
from app.models.transaction import InventoryLedger, Transaction
from app.extensions import db

api_transactions_bp = Blueprint('api_transactions', __name__)


@api_transactions_bp.route('/api/transactions', methods=['GET'])
@login_required
def list_transactions():
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
    return jsonify({'list': data, 'total': pagination.total})


@api_transactions_bp.route('/api/transactions/<int:tx_id>', methods=['GET'])
@login_required
def transaction_detail(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
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
    return jsonify(detail)


@api_transactions_bp.route('/api/transactions', methods=['POST'])
@login_required
def create_transaction():
    payload = request.get_json() or {}
    TransactionService.validate_stock(payload)
    tx = TransactionService.create_transaction(payload, current_user.id)
    return jsonify(TransactionService.to_dict(tx)), 201


@api_transactions_bp.route('/api/transactions/<int:tx_id>/submit', methods=['POST'])
@login_required
def submit_transaction(tx_id):
    tx = TransactionService.submit_transaction(tx_id)
    return jsonify(TransactionService.to_dict(tx))


@api_transactions_bp.route('/api/transactions/<int:tx_id>/approve', methods=['POST'])
@login_required
def approve_transaction(tx_id):
    tx = TransactionService.approve_transaction(tx_id, current_user.id)
    return jsonify(TransactionService.to_dict(tx))


@api_transactions_bp.route('/api/transactions/<int:tx_id>/reject', methods=['POST'])
@login_required
def reject_transaction(tx_id):
    payload = request.get_json() or {}
    reason = payload.get('reason')
    tx = TransactionService.reject_transaction(tx_id, reason)
    return jsonify(TransactionService.to_dict(tx))


@api_transactions_bp.route('/api/transactions/validate', methods=['POST'])
@login_required
def validate_transaction():
    payload = request.get_json() or {}
    TransactionService.validate_stock(payload)
    return jsonify({'ok': True})


@api_transactions_bp.route('/api/transactions/export', methods=['GET'])
@login_required
def export_transactions():
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
