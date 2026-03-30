"""
交易服务层
"""

from app.models.transaction import Transaction, TransactionDetail
from app.models.spare_part import SparePart
from app.models.batch import Batch
from app.models.warehouse import Warehouse
from app.extensions import db
from datetime import datetime
import uuid


class TransactionService:
    """交易服务类"""
    
    @staticmethod
    def generate_transaction_number(transaction_type):
        """生成交易编号"""
        prefix = {
            'in': 'IN',
            'out': 'OUT',
            'adjust_in': 'ADJ_IN',
            'adjust_out': 'ADJ_OUT',
            'transfer_out': 'TR_OUT',
            'transfer_in': 'TR_IN'
        }.get(transaction_type, 'TRX')
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{timestamp}-{random_str}"
    
    @staticmethod
    def create_transaction(data, user_id):
        """创建交易"""
        transaction = Transaction(
            transaction_number=TransactionService.generate_transaction_number(data['transaction_type']),
            transaction_type=data['transaction_type'],
            warehouse_id=data['warehouse_id'],
            spare_part_id=data['spare_part_id'],
            batch_id=data.get('batch_id') if data.get('batch_id') != 0 else None,
            quantity=data['quantity'],
            unit_price=data.get('unit_price'),
            total_amount=data.get('unit_price') * data['quantity'] if data.get('unit_price') else None,
            remark=data.get('remark'),
            created_by=user_id,
            status='pending'  # 初始状态为待审批
        )
        
        db.session.add(transaction)
        
        # 创建交易明细
        detail = TransactionDetail(
            transaction_id=transaction.id,
            spare_part_id=data['spare_part_id'],
            batch_id=data.get('batch_id') if data.get('batch_id') != 0 else None,
            quantity=data['quantity'],
            unit_price=data.get('unit_price'),
            total_amount=data.get('unit_price') * data['quantity'] if data.get('unit_price') else None,
            remark=data.get('remark')
        )
        db.session.add(detail)
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def approve_transaction(transaction_id, user_id):
        """审批交易"""
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('交易不存在')
        
        if transaction.status != 'pending':
            raise ValueError('交易状态不是待审批')
        
        # 更新交易状态
        transaction.status = 'completed'
        transaction.confirmed_by = user_id
        transaction.confirmed_at = datetime.now()
        
        # 更新备件库存
        spare_part = SparePart.query.get(transaction.spare_part_id)
        if transaction.transaction_type in ['in', 'adjust_in']:
            spare_part.current_stock += transaction.quantity
        elif transaction.transaction_type in ['out', 'adjust_out']:
            if spare_part.current_stock < transaction.quantity:
                raise ValueError('库存不足')
            spare_part.current_stock -= transaction.quantity
        
        # 更新库存状态
        spare_part.update_stock_status()
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def reject_transaction(transaction_id, user_id, reason):
        """拒绝交易"""
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('交易不存在')
        
        if transaction.status != 'pending':
            raise ValueError('交易状态不是待审批')
        
        # 更新交易状态
        transaction.status = 'rejected'
        transaction.confirmed_by = user_id
        transaction.confirmed_at = datetime.now()
        if reason:
            transaction.remark = f"{transaction.remark or ''} [拒绝原因: {reason}]"
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def approve_transfer_transaction(transaction_id, user_id):
        """审批调拨交易"""
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            raise ValueError('交易不存在')
        
        if transaction.status != 'pending':
            raise ValueError('交易状态不是待审批')
        
        if transaction.transaction_type not in ['transfer_out', 'transfer_in']:
            raise ValueError('不是调拨交易')
        
        # 开始事务
        try:
            # 更新交易状态
            transaction.status = 'completed'
            transaction.confirmed_by = user_id
            transaction.confirmed_at = datetime.now()
            
            # 处理调拨逻辑
            if transaction.transaction_type == 'transfer_out':
                # 查找对应的调入交易
                in_transaction = Transaction.query.filter_by(
                    transaction_type='transfer_in',
                    spare_part_id=transaction.spare_part_id,
                    quantity=transaction.quantity,
                    status='pending'
                ).order_by(Transaction.created_at.desc()).first()
                
                if in_transaction:
                    in_transaction.status = 'completed'
                    in_transaction.confirmed_by = user_id
                    in_transaction.confirmed_at = datetime.now()
                
                # 更新批次库存
                out_batch = Batch.query.get(transaction.batch_id)
                if out_batch:
                    out_batch.quantity -= transaction.quantity
                    if out_batch.quantity <= 0:
                        db.session.delete(out_batch)
                
                # 创建或更新目标仓库的批次
                if in_transaction:
                    to_batch = Batch.query.filter_by(
                        warehouse_id=in_transaction.warehouse_id,
                        spare_part_id=transaction.spare_part_id
                    ).first()
                    if to_batch:
                        to_batch.quantity += transaction.quantity
                    else:
                        to_batch = Batch(
                            warehouse_id=in_transaction.warehouse_id,
                            spare_part_id=transaction.spare_part_id,
                            quantity=transaction.quantity,
                            purchase_price=out_batch.purchase_price if out_batch else None,
                            batch_number=f'TRF-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                            status='active'
                        )
                        db.session.add(to_batch)
            
            db.session.commit()
            return transaction
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def transfer_spare_part(data, user_id):
        """调拨备件"""
        from_warehouse_id = data['from_warehouse_id']
        to_warehouse_id = data['to_warehouse_id']
        spare_part_id = data['spare_part_id']
        quantity = data['quantity']
        batch_id = data.get('batch_id') if data.get('batch_id') != 0 else None
        remark = data.get('remark')
        
        # 检查仓库是否相同
        if from_warehouse_id == to_warehouse_id:
            raise ValueError('调出仓库和调入仓库不能相同')
        
        # 检查备件库存
        spare_part = SparePart.query.get(spare_part_id)
        if spare_part.current_stock < quantity:
            raise ValueError('库存不足')
        
        # 开始事务
        try:
            # 创建调出交易
            out_transaction = Transaction(
                transaction_number=TransactionService.generate_transaction_number('transfer_out'),
                transaction_type='transfer_out',
                warehouse_id=from_warehouse_id,
                spare_part_id=spare_part_id,
                batch_id=batch_id,
                quantity=quantity,
                remark=f'调拨至仓库 {Warehouse.query.get(to_warehouse_id).name} - {remark}',
                created_by=user_id,
                status='pending'  # 初始状态为待审批
            )
            db.session.add(out_transaction)
            db.session.flush()  # 生成交易ID
            
            # 创建调出明细
            out_detail = TransactionDetail(
                transaction_id=out_transaction.id,
                spare_part_id=spare_part_id,
                batch_id=batch_id,
                quantity=quantity,
                remark=f'调拨至仓库 {Warehouse.query.get(to_warehouse_id).name} - {remark}'
            )
            db.session.add(out_detail)
            
            # 创建调入交易
            in_transaction = Transaction(
                transaction_number=TransactionService.generate_transaction_number('transfer_in'),
                transaction_type='transfer_in',
                warehouse_id=to_warehouse_id,
                spare_part_id=spare_part_id,
                batch_id=batch_id,
                quantity=quantity,
                remark=f'从仓库 {Warehouse.query.get(from_warehouse_id).name} 调拨 - {remark}',
                created_by=user_id,
                status='pending'  # 初始状态为待审批
            )
            db.session.add(in_transaction)
            db.session.flush()  # 生成交易ID
            
            # 创建调入明细
            in_detail = TransactionDetail(
                transaction_id=in_transaction.id,
                spare_part_id=spare_part_id,
                batch_id=batch_id,
                quantity=quantity,
                remark=f'从仓库 {Warehouse.query.get(from_warehouse_id).name} 调拨 - {remark}'
            )
            db.session.add(in_detail)
            
            # 提交事务
            db.session.commit()
            return out_transaction, in_transaction
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_transactions(filters=None, page=1, per_page=20):
        """获取交易列表"""
        query = Transaction.query
        
        if filters:
            if filters.get('transaction_type'):
                query = query.filter(Transaction.transaction_type == filters['transaction_type'])
            if filters.get('warehouse_id'):
                query = query.filter(Transaction.warehouse_id == filters['warehouse_id'])
            if filters.get('spare_part_id'):
                query = query.filter(Transaction.spare_part_id == filters['spare_part_id'])
            if filters.get('status'):
                query = query.filter(Transaction.status == filters['status'])
        
        pagination = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination
    
    @staticmethod
    def get_transaction(transaction_id):
        """获取交易详情"""
        return Transaction.query.get(transaction_id)
