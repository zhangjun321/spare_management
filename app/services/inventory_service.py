"""
库存服务层
"""

from app.extensions import db
from datetime import datetime


class InventoryService:
    """库存服务类"""
    
    @staticmethod
    def get_inventory(warehouse_id=None, location_id=None, spare_part_id=None):
        """获取库存详情"""
        from app.models.batch import Batch
        
        query = Batch.query
        
        if warehouse_id:
            query = query.filter(Batch.warehouse_id == warehouse_id)
        if location_id:
            query = query.filter(Batch.location_id == location_id)
        if spare_part_id:
            query = query.filter(Batch.spare_part_id == spare_part_id)
        
        return query.all()
    
    @staticmethod
    def get_inventory_by_warehouse(warehouse_id):
        """获取仓库库存"""
        from app.models.batch import Batch
        from app.models.spare_part import SparePart
        
        # 获取仓库中所有批次
        batches = Batch.query.filter_by(warehouse_id=warehouse_id).all()
        
        # 按备件汇总库存
        inventory_summary = {}
        for batch in batches:
            if batch.spare_part_id not in inventory_summary:
                inventory_summary[batch.spare_part_id] = {
                    'spare_part': batch.spare_part,
                    'total_quantity': 0,
                    'batches': []
                }
            inventory_summary[batch.spare_part_id]['total_quantity'] += batch.quantity
            inventory_summary[batch.spare_part_id]['batches'].append(batch)
        
        return list(inventory_summary.values())
    
    @staticmethod
    def get_inventory_by_location(location_id):
        """获取库位库存"""
        from app.models.batch import Batch
        
        return Batch.query.filter_by(location_id=location_id).all()
    
    @staticmethod
    def adjust_inventory(warehouse_id, location_id, spare_part_id, quantity, operator_id, remark=None):
        """调整库存"""
        from app.models.batch import Batch
        from app.models.transaction import Transaction
        from app.models.transaction_detail import TransactionDetail
        
        # 开始事务
        try:
            # 创建库存调整交易
            transaction = Transaction(
                transaction_type='adjust_in' if quantity > 0 else 'adjust_out',
                warehouse_id=warehouse_id,
                user_id=operator_id,
                total_amount=0,  # 库存调整无金额
                status='completed',
                remark=remark or f'库存调整: {quantity}'
            )
            db.session.add(transaction)
            db.session.flush()  # 获取transaction.id
            
            # 创建交易明细
            detail = TransactionDetail(
                transaction_id=transaction.id,
                spare_part_id=spare_part_id,
                quantity=abs(quantity),
                unit_price=0,  # 库存调整无单价
                total_price=0
            )
            db.session.add(detail)
            
            # 查找或创建批次
            batch = Batch.query.filter_by(
                warehouse_id=warehouse_id,
                location_id=location_id,
                spare_part_id=spare_part_id
            ).first()
            
            if batch:
                # 更新现有批次
                batch.quantity += quantity
                if batch.quantity < 0:
                    raise ValueError('库存不足')
            else:
                # 创建新批次
                if quantity < 0:
                    raise ValueError('库存不足')
                batch = Batch(
                    warehouse_id=warehouse_id,
                    location_id=location_id,
                    spare_part_id=spare_part_id,
                    quantity=quantity,
                    unit_price=0,  # 库存调整无单价
                    batch_number=f'ADJ-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    status='active'
                )
                db.session.add(batch)
            
            # 提交事务
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def transfer_inventory(from_warehouse_id, from_location_id, to_warehouse_id, to_location_id, spare_part_id, quantity, operator_id, remark=None):
        """调拨库存"""
        from app.models.batch import Batch
        from app.models.transaction import Transaction
        from app.models.transaction_detail import TransactionDetail
        
        # 开始事务
        try:
            # 检查源库位库存
            from_batch = Batch.query.filter_by(
                warehouse_id=from_warehouse_id,
                location_id=from_location_id,
                spare_part_id=spare_part_id
            ).first()
            
            if not from_batch or from_batch.quantity < quantity:
                raise ValueError('源库位库存不足')
            
            # 创建调拨出库交易
            out_transaction = Transaction(
                transaction_type='transfer_out',
                warehouse_id=from_warehouse_id,
                user_id=operator_id,
                total_amount=0,
                status='completed',
                remark=remark or f'调拨出库到仓库 {to_warehouse_id}'
            )
            db.session.add(out_transaction)
            db.session.flush()
            
            out_detail = TransactionDetail(
                transaction_id=out_transaction.id,
                spare_part_id=spare_part_id,
                quantity=quantity,
                unit_price=0,
                total_price=0
            )
            db.session.add(out_detail)
            
            # 创建调拨入库交易
            in_transaction = Transaction(
                transaction_type='transfer_in',
                warehouse_id=to_warehouse_id,
                user_id=operator_id,
                total_amount=0,
                status='completed',
                remark=remark or f'从仓库 {from_warehouse_id} 调拨入库'
            )
            db.session.add(in_transaction)
            db.session.flush()
            
            in_detail = TransactionDetail(
                transaction_id=in_transaction.id,
                spare_part_id=spare_part_id,
                quantity=quantity,
                unit_price=0,
                total_price=0
            )
            db.session.add(in_detail)
            
            # 减少源库位库存
            from_batch.quantity -= quantity
            if from_batch.quantity == 0:
                db.session.delete(from_batch)
            
            # 增加目标库位库存
            to_batch = Batch.query.filter_by(
                warehouse_id=to_warehouse_id,
                location_id=to_location_id,
                spare_part_id=spare_part_id
            ).first()
            
            if to_batch:
                to_batch.quantity += quantity
            else:
                to_batch = Batch(
                    warehouse_id=to_warehouse_id,
                    location_id=to_location_id,
                    spare_part_id=spare_part_id,
                    quantity=quantity,
                    unit_price=0,
                    batch_number=f'TRF-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    status='active'
                )
                db.session.add(to_batch)
            
            # 提交事务
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_inventory_statistics(warehouse_id=None):
        """获取库存统计"""
        from app.models.batch import Batch
        from app.models.spare_part import SparePart
        
        query = Batch.query
        if warehouse_id:
            query = query.filter(Batch.warehouse_id == warehouse_id)
        
        batches = query.all()
        
        total_quantity = 0
        total_value = 0
        spare_part_count = set()
        
        for batch in batches:
            total_quantity += batch.quantity
            if batch.purchase_price:
                total_value += batch.quantity * batch.purchase_price
            spare_part_count.add(batch.spare_part_id)
        
        return {
            'total_quantity': total_quantity,
            'total_value': float(total_value),
            'spare_part_count': len(spare_part_count)
        }
