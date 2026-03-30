"""
操作记录服务层
"""

from app.extensions import db
from datetime import datetime


class OperationService:
    """操作记录服务类"""
    
    @staticmethod
    def create_operation(data):
        """创建操作记录"""
        from app.models.transaction import Transaction
        from app.models.transaction_detail import TransactionDetail
        
        # 创建交易记录
        transaction = Transaction(
            transaction_type=data['operation_type'],
            warehouse_id=data['warehouse_id'],
            user_id=data['operator_id'],
            total_amount=data.get('total_amount', 0),
            status=data.get('status', 'completed'),
            remark=data.get('remark')
        )
        db.session.add(transaction)
        db.session.flush()  # 获取transaction.id
        
        # 创建交易明细
        detail = TransactionDetail(
            transaction_id=transaction.id,
            spare_part_id=data['spare_part_id'],
            quantity=data['quantity'],
            unit_price=data.get('unit_price', 0),
            total_price=data.get('total_price', 0)
        )
        db.session.add(detail)
        
        db.session.commit()
        return transaction
    
    @staticmethod
    def get_operations(filters=None, page=1, per_page=20):
        """获取操作记录"""
        from app.models.transaction import Transaction
        
        query = Transaction.query
        
        if filters:
            if filters.get('warehouse_id'):
                query = query.filter(Transaction.warehouse_id == filters['warehouse_id'])
            if filters.get('operation_type'):
                query = query.filter(Transaction.transaction_type == filters['operation_type'])
            if filters.get('start_date'):
                query = query.filter(Transaction.created_at >= filters['start_date'])
            if filters.get('end_date'):
                query = query.filter(Transaction.created_at <= filters['end_date'])
            if filters.get('user_id'):
                query = query.filter(Transaction.user_id == filters['user_id'])
        
        pagination = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination
    
    @staticmethod
    def get_operation(operation_id):
        """获取操作详情"""
        from app.models.transaction import Transaction
        return Transaction.query.get(operation_id)
    
    @staticmethod
    def get_operations_by_warehouse(warehouse_id, filters=None, page=1, per_page=20):
        """获取仓库操作记录"""
        from app.models.transaction import Transaction
        
        query = Transaction.query.filter_by(warehouse_id=warehouse_id)
        
        if filters:
            if filters.get('operation_type'):
                query = query.filter(Transaction.transaction_type == filters['operation_type'])
            if filters.get('start_date'):
                query = query.filter(Transaction.created_at >= filters['start_date'])
            if filters.get('end_date'):
                query = query.filter(Transaction.created_at <= filters['end_date'])
        
        pagination = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination
    
    @staticmethod
    def get_operations_by_location(location_id, filters=None, page=1, per_page=20):
        """获取库位操作记录"""
        from app.models.transaction import Transaction
        from app.models.transaction_detail import TransactionDetail
        from app.models.batch import Batch
        
        # 通过批次关联查询库位的操作记录
        query = Transaction.query.join(
            TransactionDetail
        ).join(
            Batch
        ).filter(
            Batch.location_id == location_id
        )
        
        if filters:
            if filters.get('operation_type'):
                query = query.filter(Transaction.transaction_type == filters['operation_type'])
            if filters.get('start_date'):
                query = query.filter(Transaction.created_at >= filters['start_date'])
            if filters.get('end_date'):
                query = query.filter(Transaction.created_at <= filters['end_date'])
        
        pagination = query.order_by(Transaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination
    
    @staticmethod
    def get_operation_statistics(warehouse_id=None, start_date=None, end_date=None):
        """获取操作统计"""
        from app.models.transaction import Transaction
        from app.models.transaction_detail import TransactionDetail
        
        query = Transaction.query
        if warehouse_id:
            query = query.filter(Transaction.warehouse_id == warehouse_id)
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
        
        transactions = query.all()
        
        # 按操作类型统计
        type_statistics = {}
        total_quantity = 0
        total_amount = 0
        
        for transaction in transactions:
            transaction_type = transaction.transaction_type
            if transaction_type not in type_statistics:
                type_statistics[transaction_type] = {
                    'count': 0,
                    'quantity': 0,
                    'amount': 0
                }
            
            type_statistics[transaction_type]['count'] += 1
            
            # 计算数量和金额
            for detail in transaction.details:
                type_statistics[transaction_type]['quantity'] += detail.quantity
                type_statistics[transaction_type]['amount'] += detail.total_price
                total_quantity += detail.quantity
                total_amount += detail.total_price
        
        return {
            'total_count': len(transactions),
            'total_quantity': total_quantity,
            'total_amount': float(total_amount),
            'type_statistics': type_statistics
        }
