"""交易服务层"""

from datetime import datetime
from decimal import Decimal
import uuid

from app.extensions import db
from app.models.transaction import Transaction, TransactionDetail, InventoryLedger
from app.models.spare_part import SparePart
from app.models.batch import Batch
from app.models.warehouse import Warehouse


class TransactionService:
    """交易服务类：负责创建、提交、审批以及库存流水生成"""

    @staticmethod
    def _dec(value):
        return Decimal(str(value)) if value is not None else Decimal('0')

    @staticmethod
    def generate_tx_code(tx_type: str) -> str:
        prefix_map = {
            'inbound': 'IN',
            'outbound': 'OUT',
            'transfer': 'TR',
            'inventory_adjust': 'ADJ',
        }
        prefix = prefix_map.get(tx_type, 'TX')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        rand = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{rand}"

    @staticmethod
    def create_transaction(payload: dict, operator_id: int) -> Transaction:
        tx_type = payload['tx_type']
        items = payload.get('items', [])
        if not items:
            raise ValueError('至少需要一条明细')

        tx = Transaction(
            tx_code=TransactionService.generate_tx_code(tx_type),
            tx_type=tx_type,
            status='draft',
            source_warehouse_id=payload.get('source_warehouse_id'),
            target_warehouse_id=payload.get('target_warehouse_id'),
            operator_id=operator_id,
            remark=payload.get('remark'),
        )
        db.session.add(tx)
        db.session.flush()

        total_qty = Decimal('0')
        total_amount = Decimal('0')
        for item in items:
            qty = TransactionService._dec(item['quantity'])
            price = TransactionService._dec(item.get('unit_price'))
            amount = qty * price if price else None
            detail = TransactionDetail(
                transaction_id=tx.id,
                spare_part_id=item['spare_part_id'],
                batch_id=item.get('batch_id'),
                source_location_id=item.get('source_location_id'),
                target_location_id=item.get('target_location_id'),
                quantity=qty,
                unit_price=price if price else None,
                amount=amount,
                remark=item.get('remark'),
            )
            db.session.add(detail)
            total_qty += qty
            if amount:
                total_amount += amount

        tx.total_qty = total_qty
        tx.total_amount = total_amount if total_amount else None
        db.session.commit()
        return tx

    @staticmethod
    def submit_transaction(tx_id: int) -> Transaction:
        tx = Transaction.query.get(tx_id)
        if not tx:
            raise ValueError('交易不存在')
        if tx.status not in ['draft', 'rejected']:
            raise ValueError('当前状态不可提交')
        tx.status = 'submitted'
        tx.submitted_at = datetime.utcnow()
        db.session.commit()
        return tx

    @staticmethod
    def approve_transaction(tx_id: int, approver_id: int) -> Transaction:
        tx = Transaction.query.get(tx_id)
        if not tx:
            raise ValueError('交易不存在')
        if tx.status != 'submitted':
            raise ValueError('当前状态不可审批')

        # 审批通过，写入库存流水并更新库存
        for detail in tx.details:
            qty = TransactionService._dec(detail.quantity)
            if tx.tx_type == 'transfer':
                # 出
                TransactionService._write_ledger(tx, detail, -qty, tx.source_warehouse_id, detail.source_location_id)
                TransactionService._apply_stock(detail.spare_part_id, -qty)
                # 入
                TransactionService._write_ledger(tx, detail, qty, tx.target_warehouse_id, detail.target_location_id)
                TransactionService._apply_stock(detail.spare_part_id, qty)
            elif tx.tx_type == 'outbound':
                TransactionService._write_ledger(tx, detail, -qty, tx.source_warehouse_id, detail.source_location_id)
                TransactionService._apply_stock(detail.spare_part_id, -qty)
            else:  # inbound / inventory_adjust
                TransactionService._write_ledger(tx, detail, qty, tx.target_warehouse_id or tx.source_warehouse_id, detail.target_location_id)
                TransactionService._apply_stock(detail.spare_part_id, qty)

        tx.status = 'approved'
        tx.approved_at = datetime.utcnow()
        db.session.commit()
        return tx

    @staticmethod
    def reject_transaction(tx_id: int, reason: str = None) -> Transaction:
        tx = Transaction.query.get(tx_id)
        if not tx:
            raise ValueError('交易不存在')
        if tx.status != 'submitted':
            raise ValueError('当前状态不可拒绝')
        tx.status = 'rejected'
        tx.remark = f"{tx.remark or ''} [驳回原因: {reason}]" if reason else tx.remark
        db.session.commit()
        return tx

    @staticmethod
    def validate_stock(payload: dict):
        tx_type = payload.get('tx_type')
        items = payload.get('items', [])
        if tx_type in ['outbound', 'transfer']:
            for item in items:
                spare_part = SparePart.query.get(item['spare_part_id'])
                if not spare_part:
                    raise ValueError('备件不存在')
                qty = TransactionService._dec(item['quantity'])
                if TransactionService._dec(spare_part.current_stock) < qty:
                    raise ValueError(f"备件 {spare_part.name} 库存不足")
        return True

    @staticmethod
    def _apply_stock(spare_part_id: int, delta: Decimal):
        part = SparePart.query.get(spare_part_id)
        if not part:
            raise ValueError('备件不存在')
        new_stock = TransactionService._dec(part.current_stock) + delta
        if new_stock < 0:
            raise ValueError('库存不足')
        part.current_stock = new_stock
        part.update_stock_status()

    @staticmethod
    def _write_ledger(tx: Transaction, detail: TransactionDetail, delta: Decimal, warehouse_id: int, location_id: int = None):
        ledger = InventoryLedger(
            transaction_id=tx.id,
            transaction_detail_id=detail.id,
            spare_part_id=detail.spare_part_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            batch_id=detail.batch_id,
            quantity_delta=delta,
            created_at=datetime.utcnow(),
        )
        db.session.add(ledger)

    @staticmethod
    def list_transactions(filters: dict, page: int = 1, per_page: int = 20):
        query = Transaction.query
        if filters.get('tx_type'):
            query = query.filter(Transaction.tx_type == filters['tx_type'])
        if filters.get('status'):
            query = query.filter(Transaction.status == filters['status'])
        if filters.get('warehouse_id'):
            query = query.filter((Transaction.source_warehouse_id == filters['warehouse_id']) | (Transaction.target_warehouse_id == filters['warehouse_id']))
        if filters.get('keyword'):
            kw = f"%{filters['keyword']}%"
            query = query.filter(Transaction.tx_code.like(kw))

        pagination = query.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return pagination

    @staticmethod
    def to_dict(tx: Transaction, with_details: bool = False):
        data = {
            'id': tx.id,
            'tx_code': tx.tx_code,
            'tx_type': tx.tx_type,
            'status': tx.status,
            'source_warehouse_id': tx.source_warehouse_id,
            'target_warehouse_id': tx.target_warehouse_id,
            'operator_id': tx.operator_id,
            'total_qty': float(tx.total_qty or 0),
            'total_amount': float(tx.total_amount) if tx.total_amount else None,
            'remark': tx.remark,
            'created_at': tx.created_at.isoformat() if tx.created_at else None,
            'submitted_at': tx.submitted_at.isoformat() if tx.submitted_at else None,
            'approved_at': tx.approved_at.isoformat() if tx.approved_at else None,
        }
        if with_details:
            data['details'] = [
                {
                    'id': d.id,
                    'spare_part_id': d.spare_part_id,
                    'batch_id': d.batch_id,
                    'source_location_id': d.source_location_id,
                    'target_location_id': d.target_location_id,
                    'quantity': float(d.quantity),
                    'unit_price': float(d.unit_price) if d.unit_price else None,
                    'amount': float(d.amount) if d.amount else None,
                    'remark': d.remark,
                }
                for d in tx.details
            ]
        return data
