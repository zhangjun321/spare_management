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
                TransactionService._apply_stock(detail.spare_part_id, -qty, tx.source_warehouse_id, detail.source_location_id)
                # 入
                TransactionService._write_ledger(tx, detail, qty, tx.target_warehouse_id, detail.target_location_id)
                TransactionService._apply_stock(detail.spare_part_id, qty, tx.target_warehouse_id, detail.target_location_id)
            elif tx.tx_type == 'outbound':
                TransactionService._write_ledger(tx, detail, -qty, tx.source_warehouse_id, detail.source_location_id)
                TransactionService._apply_stock(detail.spare_part_id, -qty, tx.source_warehouse_id, detail.source_location_id)
            else:  # inbound / inventory_adjust
                wh_id = tx.target_warehouse_id or tx.source_warehouse_id
                TransactionService._write_ledger(tx, detail, qty, wh_id, detail.target_location_id)
                TransactionService._apply_stock(detail.spare_part_id, qty, wh_id, detail.target_location_id)

        tx.status = 'approved'
        tx.approved_at = datetime.utcnow()
        # 记录审批人
        if hasattr(tx, 'approver_id'):
            tx.approver_id = approver_id
        db.session.commit()
        return tx

    @staticmethod
    def reject_transaction(tx_id: int, reason: str = None, approver_id: int = None) -> Transaction:
        tx = Transaction.query.get(tx_id)
        if not tx:
            raise ValueError('交易不存在')
        if tx.status != 'submitted':
            raise ValueError('当前状态不可拒绝')
        tx.status = 'rejected'
        if hasattr(tx, 'reject_reason'):
            tx.reject_reason = reason
        else:
            tx.remark = f"{tx.remark or ''} [驳回原因: {reason}]" if reason else tx.remark
        if hasattr(tx, 'approver_id') and approver_id:
            tx.approver_id = approver_id
        db.session.commit()
        return tx

    @staticmethod
    def validate_stock(payload: dict):
        """库存校验（仓库维度）"""
        tx_type = payload.get('tx_type')
        source_wh_id = payload.get('source_warehouse_id')
        items = payload.get('items', [])
        if tx_type in ['outbound', 'transfer']:
            if not source_wh_id:
                raise ValueError('出库/调拨必须指定来源仓库')
            for item in items:
                spare_part = SparePart.query.get(item['spare_part_id'])
                if not spare_part:
                    raise ValueError('备件不存在')
                qty = TransactionService._dec(item['quantity'])
                # 按仓库维度校验可用库存
                from app.models.inventory_record import InventoryRecord
                wh_qty = db.session.query(
                    db.func.sum(InventoryRecord.quantity)
                ).filter_by(
                    warehouse_id=source_wh_id,
                    spare_part_id=item['spare_part_id']
                ).scalar() or 0
                if TransactionService._dec(wh_qty) < qty:
                    raise ValueError(
                        f"仓库库存不足：{spare_part.name}，"
                        f"仓库可用 {wh_qty}，需出 {item['quantity']}"
                    )
        return True

    @staticmethod
    def _apply_stock(spare_part_id: int, delta: Decimal, warehouse_id: int = None, location_id: int = None):
        """
        更新备件库存。
        优先通过 InventoryRecord 更新（触发 ORM 事件监听器自动同步 SparePart.current_stock）。
        若无对应 InventoryRecord，则直接修改 SparePart.current_stock（降级路径）。
        """
        from app.models.inventory_record import InventoryRecord

        if warehouse_id:
            # 通过 InventoryRecord 更新，事件监听器会自动同步 SparePart.current_stock
            query = InventoryRecord.query.filter_by(
                spare_part_id=spare_part_id,
                warehouse_id=warehouse_id
            )
            if location_id:
                query = query.filter_by(location_id=location_id)
            records = query.all()

            if records:
                # 按数量比例分配 delta（优先从有库存的记录扣减）
                remaining = delta
                for record in records:
                    if remaining == 0:
                        break
                    if delta < 0:
                        # 出库：从每条记录扣减，不超过其库存
                        deduct = max(remaining, -Decimal(str(record.quantity)))
                        record.quantity = int(Decimal(str(record.quantity)) + deduct)
                    else:
                        # 入库：加到第一条有效记录
                        record.quantity = int(Decimal(str(record.quantity)) + remaining)
                        remaining = Decimal('0')
                        break
                    remaining -= deduct
                    record.available_quantity = record.quantity - record.locked_quantity
                    record.update_stock_status()
                    record.last_inbound_time = datetime.utcnow() if delta > 0 else record.last_inbound_time
                    record.last_outbound_time = datetime.utcnow() if delta < 0 else record.last_outbound_time
                return  # 事件监听器会自动同步 SparePart.current_stock

        # 降级路径：直接修改 SparePart
        part = SparePart.query.get(spare_part_id)
        if not part:
            raise ValueError('备件不存在')
        new_stock = TransactionService._dec(part.current_stock) + delta
        if new_stock < 0:
            raise ValueError('库存不足')
        part.current_stock = int(new_stock)
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
