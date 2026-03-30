"""
报表服务层
"""

from app.extensions import db
from datetime import datetime, timedelta


class ReportService:
    """报表服务类"""
    
    @staticmethod
    def generate_warehouse_utilization_report(warehouse_id=None, start_date=None, end_date=None):
        """生成仓库利用率报表"""
        from app.models.warehouse import Warehouse
        from app.services.warehouse_service import WarehouseService
        
        # 获取仓库列表
        if warehouse_id:
            warehouses = [Warehouse.query.get(warehouse_id)]
        else:
            warehouses = Warehouse.query.all()
        
        report_data = []
        for warehouse in warehouses:
            if not warehouse.capacity:
                continue
            
            utilization_rate = WarehouseService.get_utilization_rate(warehouse.id)
            total_inventory = WarehouseService.get_total_inventory(warehouse.id)
            
            report_data.append({
                'warehouse_id': warehouse.id,
                'warehouse_name': warehouse.name,
                'warehouse_code': warehouse.code,
                'capacity': warehouse.capacity,
                'total_inventory': total_inventory,
                'utilization_rate': round(utilization_rate, 2),
                'status': 'active' if warehouse.is_active else 'inactive'
            })
        
        return report_data
    
    @staticmethod
    def generate_inventory_flow_report(warehouse_id=None, start_date=None, end_date=None):
        """生成库存流动报表"""
        from app.models.transaction import Transaction, TransactionDetail
        
        # 默认时间范围为最近30天
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 构建查询
        query = Transaction.query.join(TransactionDetail).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if warehouse_id:
            query = query.filter(Transaction.warehouse_id == warehouse_id)
        
        transactions = query.all()
        
        # 按操作类型和日期统计
        daily_flow = {}
        for transaction in transactions:
            date_key = transaction.created_at.strftime('%Y-%m-%d')
            if date_key not in daily_flow:
                daily_flow[date_key] = {
                    'date': date_key,
                    'in': 0,
                    'out': 0,
                    'transfer_in': 0,
                    'transfer_out': 0,
                    'adjust_in': 0,
                    'adjust_out': 0
                }
            
            for detail in transaction.details:
                if transaction.transaction_type == 'in':
                    daily_flow[date_key]['in'] += detail.quantity
                elif transaction.transaction_type == 'out':
                    daily_flow[date_key]['out'] += detail.quantity
                elif transaction.transaction_type == 'transfer_in':
                    daily_flow[date_key]['transfer_in'] += detail.quantity
                elif transaction.transaction_type == 'transfer_out':
                    daily_flow[date_key]['transfer_out'] += detail.quantity
                elif transaction.transaction_type == 'adjust_in':
                    daily_flow[date_key]['adjust_in'] += detail.quantity
                elif transaction.transaction_type == 'adjust_out':
                    daily_flow[date_key]['adjust_out'] += detail.quantity
        
        # 转换为列表并按日期排序
        report_data = sorted(daily_flow.values(), key=lambda x: x['date'])
        
        return report_data
    
    @staticmethod
    def generate_inventory_value_report(warehouse_id=None, start_date=None, end_date=None):
        """生成库存价值报表"""
        from app.models.batch import Batch
        from app.models.spare_part import SparePart
        
        # 构建查询
        query = Batch.query
        if warehouse_id:
            query = query.filter(Batch.warehouse_id == warehouse_id)
        
        batches = query.all()
        
        # 按备件类型统计价值
        value_by_category = {}
        total_value = 0
        
        for batch in batches:
            if not batch.spare_part or not batch.purchase_price:
                continue
            
            category_name = batch.spare_part.category.name if batch.spare_part.category else '未分类'
            if category_name not in value_by_category:
                value_by_category[category_name] = {
                    'category': category_name,
                    'quantity': 0,
                    'value': 0,
                    'spare_part_count': 0
                }
            
            batch_value = batch.quantity * batch.purchase_price
            value_by_category[category_name]['quantity'] += batch.quantity
            value_by_category[category_name]['value'] += batch_value
            value_by_category[category_name]['spare_part_count'] += 1
            total_value += batch_value
        
        # 转换为列表并按价值排序
        report_data = sorted(value_by_category.values(), key=lambda x: x['value'], reverse=True)
        
        return {
            'total_value': float(total_value),
            'category_breakdown': report_data
        }
    
    @staticmethod
    def generate_inventory_turnover_report(warehouse_id=None, period_days=30):
        """生成库存周转率报表"""
        from app.models.transaction import Transaction, TransactionDetail
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # 计算期间出库总量
        out_query = Transaction.query.join(TransactionDetail).filter(
            Transaction.transaction_type.in_(['out', 'transfer_out']),
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if warehouse_id:
            out_query = out_query.filter(Transaction.warehouse_id == warehouse_id)
        
        out_transactions = out_query.all()
        total_out_quantity = 0
        for transaction in out_transactions:
            for detail in transaction.details:
                total_out_quantity += detail.quantity
        
        # 计算平均库存
        from app.services.inventory_service import InventoryService
        current_inventory = InventoryService.get_inventory_statistics(warehouse_id)
        average_inventory = current_inventory['total_quantity'] / 2  # 简化计算
        
        # 计算周转率
        turnover_rate = 0
        if average_inventory > 0:
            turnover_rate = total_out_quantity / average_inventory
        
        # 计算周转天数
        turnover_days = 0
        if turnover_rate > 0:
            turnover_days = period_days / turnover_rate
        
        return {
            'period_days': period_days,
            'total_out_quantity': total_out_quantity,
            'average_inventory': average_inventory,
            'turnover_rate': round(turnover_rate, 2),
            'turnover_days': round(turnover_days, 2)
        }
