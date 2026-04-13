"""
库存事务日志服务
"""

from datetime import datetime
from app.models.warehouse_v3.inventory_transaction_log import InventoryTransactionLog
from app import db


class InventoryTransactionLogService:
    """库存事务日志服务类"""
    
    @staticmethod
    def create_transaction_log(inventory_id, change_type, change_quantity, operator_id, 
                               source_type=None, source_id=None, source_no=None, remark=None):
        """
        创建库存事务日志
        
        Args:
            inventory_id: 库存 ID
            change_type: 变动类型 (IN/OUT/ADJUST/TRANSFER/LOCK/UNLOCK)
            change_quantity: 变动数量（正数）
            operator_id: 操作人 ID
            source_type: 单据类型
            source_id: 单据 ID
            source_no: 单据编号
            remark: 备注
            
        Returns:
            InventoryTransactionLog: 创建的日志对象
        """
        from app.models.warehouse_v3.inventory import InventoryV3
        
        # 获取库存信息
        inventory = InventoryV3.query.get(inventory_id)
        if not inventory:
            raise ValueError(f'库存不存在：{inventory_id}')
        
        old_quantity = inventory.quantity
        
        # 计算新数量
        if change_type in ['IN', 'ADJUST_IN']:
            new_quantity = old_quantity + change_quantity
        elif change_type in ['OUT', 'ADJUST_OUT']:
            new_quantity = old_quantity - change_quantity
        else:
            new_quantity = old_quantity
        
        # 创建日志
        log = InventoryTransactionLog(
            transaction_no=InventoryTransactionLog.generate_transaction_no(),
            inventory_id=inventory_id,
            warehouse_id=inventory.warehouse_id,
            location_id=inventory.location_id,
            part_id=inventory.part_id,
            batch_id=inventory.batch_id,
            change_type=change_type,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            change_quantity=change_quantity,
            source_type=source_type,
            source_id=source_id,
            source_no=source_no,
            operator_id=operator_id,
            operation_time=datetime.utcnow(),
            remark=remark
        )
        
        db.session.add(log)
        
        return log
    
    @staticmethod
    def get_transaction_logs(inventory_id=None, part_id=None, warehouse_id=None, 
                             source_type=None, source_id=None, start_date=None, end_date=None,
                             page=1, per_page=50):
        """
        查询库存事务日志
        
        Args:
            inventory_id: 库存 ID
            part_id: 备件 ID
            warehouse_id: 仓库 ID
            source_type: 单据类型
            source_id: 单据 ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 日志列表和总数
        """
        query = InventoryTransactionLog.query
        
        if inventory_id:
            query = query.filter(InventoryTransactionLog.inventory_id == inventory_id)
        if part_id:
            query = query.filter(InventoryTransactionLog.part_id == part_id)
        if warehouse_id:
            query = query.filter(InventoryTransactionLog.warehouse_id == warehouse_id)
        if source_type:
            query = query.filter(InventoryTransactionLog.source_type == source_type)
        if source_id and source_type:
            query = query.filter(InventoryTransactionLog.source_id == source_id)
        if start_date:
            query = query.filter(InventoryTransactionLog.operation_time >= start_date)
        if end_date:
            query = query.filter(InventoryTransactionLog.operation_time <= end_date)
        
        # 按时间倒序
        query = query.order_by(InventoryTransactionLog.operation_time.desc())
        
        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        logs = [log.to_dict() for log in pagination.items]
        
        return {
            'list': logs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    
    @staticmethod
    def get_inventory_trace(inventory_id):
        """
        获取库存完整追溯链
        
        Args:
            inventory_id: 库存 ID
            
        Returns:
            list: 按时间排序的事务日志
        """
        logs = InventoryTransactionLog.query.filter_by(
            inventory_id=inventory_id
        ).order_by(InventoryTransactionLog.operation_time.asc()).all()
        
        return [log.to_dict() for log in logs]
    
    @staticmethod
    def get_part_trace(part_id, warehouse_id=None, start_date=None, end_date=None):
        """
        获取备件的库存变动追溯
        
        Args:
            part_id: 备件 ID
            warehouse_id: 仓库 ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 事务日志列表
        """
        query = InventoryTransactionLog.query.filter_by(part_id=part_id)
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        if start_date:
            query = query.filter(InventoryTransactionLog.operation_time >= start_date)
        if end_date:
            query = query.filter(InventoryTransactionLog.operation_time <= end_date)
        
        logs = query.order_by(InventoryTransactionLog.operation_time.desc()).all()
        
        return [log.to_dict() for log in logs]
    
    @staticmethod
    def generate_daily_summary(warehouse_id, part_id, transaction_date):
        """
        生成每日库存变动汇总
        
        Args:
            warehouse_id: 仓库 ID
            part_id: 备件 ID
            transaction_date: 交易日期
            
        Returns:
            InventoryTransactionSummary: 汇总对象
        """
        from app.models.warehouse_v3.inventory_transaction_log import InventoryTransactionSummary
        from datetime import date
        
        # 查询当日的日志
        start_datetime = datetime.combine(transaction_date, datetime.min.time())
        end_datetime = datetime.combine(transaction_date, datetime.max.time())
        
        logs = InventoryTransactionLog.query.filter(
            InventoryTransactionLog.warehouse_id == warehouse_id,
            InventoryTransactionLog.part_id == part_id,
            InventoryTransactionLog.operation_time >= start_datetime,
            InventoryTransactionLog.operation_time <= end_datetime
        ).all()
        
        # 计算汇总
        total_in = sum(log.change_quantity for log in logs if log.change_type == 'IN')
        total_out = sum(log.change_quantity for log in logs if log.change_type == 'OUT')
        total_adjust_in = sum(log.change_quantity for log in logs if log.change_type == 'ADJUST_IN')
        total_adjust_out = sum(log.change_quantity for log in logs if log.change_type == 'ADJUST_OUT')
        
        # 获取期初数量（前一天结束时的数量）
        prev_day = transaction_date - timedelta(days=1)
        prev_logs = InventoryTransactionLog.query.filter(
            InventoryTransactionLog.warehouse_id == warehouse_id,
            InventoryTransactionLog.part_id == part_id,
            InventoryTransactionLog.operation_time <= datetime.combine(prev_day, datetime.max.time())
        ).order_by(InventoryTransactionLog.operation_time.desc()).first()
        
        opening_quantity = prev_logs.new_quantity if prev_logs else 0
        closing_quantity = opening_quantity + total_in - total_out + total_adjust_in - total_adjust_out
        
        # 创建或更新汇总
        summary = InventoryTransactionSummary.query.filter_by(
            warehouse_id=warehouse_id,
            part_id=part_id,
            transaction_date=transaction_date
        ).first()
        
        if not summary:
            summary = InventoryTransactionSummary(
                warehouse_id=warehouse_id,
                part_id=part_id,
                transaction_date=transaction_date
            )
            db.session.add(summary)
        
        summary.total_in_quantity = total_in
        summary.total_out_quantity = total_out
        summary.total_adjust_in = total_adjust_in
        summary.total_adjust_out = total_adjust_out
        summary.inbound_count = sum(1 for log in logs if log.change_type == 'IN')
        summary.outbound_count = sum(1 for log in logs if log.change_type == 'OUT')
        summary.adjust_count = sum(1 for log in logs if log.change_type in ['ADJUST_IN', 'ADJUST_OUT'])
        summary.opening_quantity = opening_quantity
        summary.closing_quantity = closing_quantity
        
        return summary
