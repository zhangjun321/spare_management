"""
高级数据分析服务
提供库存趋势预测、智能补货建议等功能
"""

from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from app.models.transaction import Transaction
from datetime import datetime, timedelta
from sqlalchemy import func, extract


class AnalyticsService:
    """数据分析服务类"""
    
    @staticmethod
    def get_inventory_trend(warehouse_id=None, days=30):
        """
        获取库存趋势
        
        Args:
            warehouse_id: 仓库 ID（可选，不传则统计所有仓库）
            days: 统计天数
        
        Returns:
            每日库存数据列表
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 按日期分组统计库存总量
        query = db.session.query(
            extract('year', Transaction.created_at).label('year'),
            extract('month', Transaction.created_at).label('month'),
            extract('day', Transaction.created_at).label('day'),
            func.sum(Transaction.quantity).label('total_quantity')
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        if warehouse_id:
            query = query.filter(Transaction.warehouse_id == warehouse_id)
        
        query = query.group_by(
            extract('year', Transaction.created_at),
            extract('month', Transaction.created_at),
            extract('day', Transaction.created_at)
        ).order_by(
            'year', 'month', 'day'
        )
        
        results = query.all()
        
        # 转换为图表数据
        trend_data = []
        for row in results:
            date_str = f"{int(row.year):04d}-{int(row.month):02d}-{int(row.day):02d}"
            trend_data.append({
                'date': date_str,
                'quantity': row.total_quantity or 0
            })
        
        return trend_data
    
    @staticmethod
    def get_stock_turnover_rate(warehouse_id=None, days=30):
        """
        获取库存周转率
        
        Args:
            warehouse_id: 仓库 ID
            days: 统计天数
        
        Returns:
            周转率数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 计算出库总量
        outbound_query = db.session.query(
            func.sum(Transaction.quantity)
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.transaction_type == 'outbound'
        )
        
        if warehouse_id:
            outbound_query = outbound_query.filter(Transaction.warehouse_id == warehouse_id)
        
        total_outbound = outbound_query.scalar() or 0
        
        # 计算平均库存
        inventory_query = db.session.query(
            func.sum(InventoryRecord.quantity)
        )
        
        if warehouse_id:
            inventory_query = inventory_query.filter(InventoryRecord.warehouse_id == warehouse_id)
        
        avg_inventory = inventory_query.scalar() or 1  # 避免除零
        
        # 计算周转率
        turnover_rate = (total_outbound / avg_inventory) * (30 / days) if days > 0 else 0
        
        return {
            'turnover_rate': round(turnover_rate, 2),
            'total_outbound': total_outbound,
            'avg_inventory': round(avg_inventory, 2),
            'period_days': days,
            'interpretation': AnalyticsService._interpret_turnover_rate(turnover_rate)
        }
    
    @staticmethod
    def _interpret_turnover_rate(rate):
        """解释周转率"""
        if rate > 2:
            return '优秀 - 库存周转快'
        elif rate > 1:
            return '良好 - 库存周转正常'
        elif rate > 0.5:
            return '一般 - 库存周转较慢'
        else:
            return '较差 - 库存积压风险'
    
    @staticmethod
    def get_demand_forecast(spare_part_id, days=30):
        """
        需求预测（基于历史出库数据）
        
        Args:
            spare_part_id: 备件 ID
            days: 预测天数
        
        Returns:
            预测结果
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days * 2)  # 使用两倍时间进行预测
        
        # 获取历史出库数据
        outbound_data = db.session.query(
            func.sum(Transaction.quantity).label('quantity'),
            func.count(Transaction.id).label('order_count')
        ).filter(
            Transaction.spare_part_id == spare_part_id,
            Transaction.transaction_type == 'outbound',
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).first()
        
        if not outbound_data or not outbound_data.quantity:
            return {
                'predicted_demand': 0,
                'confidence': 'low',
                'recommendation': '历史数据不足，建议人工评估'
            }
        
        # 简单移动平均预测
        daily_avg = outbound_data.quantity / (days * 2)
        predicted_demand = int(daily_avg * days)
        
        # 计算置信度
        order_count = outbound_data.order_count
        if order_count > 20:
            confidence = 'high'
        elif order_count > 10:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # 获取当前库存
        current_stock = db.session.query(
            func.sum(InventoryRecord.quantity)
        ).filter(
            InventoryRecord.spare_part_id == spare_part_id
        ).scalar() or 0
        
        # 生成建议
        if current_stock < predicted_demand * 0.5:
            recommendation = f'建议立即补货，预计需求 {predicted_demand}，当前库存 {current_stock}'
        elif current_stock < predicted_demand:
            recommendation = f'建议准备补货，预计需求 {predicted_demand}，当前库存 {current_stock}'
        else:
            recommendation = f'库存充足，预计需求 {predicted_demand}，当前库存 {current_stock}'
        
        return {
            'predicted_demand': predicted_demand,
            'confidence': confidence,
            'historical_data': {
                'total_quantity': outbound_data.quantity,
                'order_count': order_count,
                'daily_avg': round(daily_avg, 2)
            },
            'current_stock': current_stock,
            'recommendation': recommendation
        }
    
    @staticmethod
    def get_reorder_suggestions(warehouse_id=None):
        """
        获取补货建议
        
        Args:
            warehouse_id: 仓库 ID（可选）
        
        Returns:
            需要补货的备件列表
        """
        # 查询库存低于安全库存的备件
        query = db.session.query(
            SparePart,
            InventoryRecord,
            Warehouse
        ).join(
            InventoryRecord, SparePart.id == InventoryRecord.spare_part_id
        ).join(
            Warehouse, InventoryRecord.warehouse_id == Warehouse.id
        ).filter(
            InventoryRecord.quantity <= InventoryRecord.min_stock,
            InventoryRecord.stock_status.in_(['low', 'out'])
        )
        
        if warehouse_id:
            query = query.filter(InventoryRecord.warehouse_id == warehouse_id)
        
        results = query.all()
        
        suggestions = []
        for spare_part, inventory, warehouse in results:
            # 计算建议补货量
            suggested_quantity = inventory.max_stock - inventory.quantity
            
            # 预测需求
            forecast = AnalyticsService.get_demand_forecast(spare_part.id, days=30)
            
            suggestions.append({
                'spare_part_id': spare_part.id,
                'spare_part_name': spare_part.name,
                'part_code': spare_part.part_code,
                'warehouse_id': warehouse.id,
                'warehouse_name': warehouse.name,
                'current_stock': inventory.quantity,
                'min_stock': inventory.min_stock,
                'max_stock': inventory.max_stock,
                'suggested_quantity': suggested_quantity,
                'stock_status': inventory.stock_status,
                'predicted_demand': forecast.get('predicted_demand', 0),
                'priority': AnalyticsService._calculate_priority(
                    inventory.quantity,
                    inventory.min_stock,
                    forecast.get('predicted_demand', 0)
                )
            })
        
        # 按优先级排序
        suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        return suggestions
    
    @staticmethod
    def _calculate_priority(current_stock, min_stock, predicted_demand):
        """计算补货优先级（1-10，10 为最高）"""
        if current_stock == 0:
            return 10
        elif current_stock < min_stock * 0.5:
            return 8
        elif current_stock < min_stock:
            return 6
        elif predicted_demand > current_stock:
            return 4
        else:
            return 2
    
    @staticmethod
    def get_warehouse_utilization_trend(warehouse_id, days=90):
        """
        获取仓库利用率趋势
        
        Args:
            warehouse_id: 仓库 ID
            days: 统计天数
        
        Returns:
            利用率趋势数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 获取仓库容量
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse or not warehouse.capacity:
            return None
        
        # 按日期统计库存总量
        query = db.session.query(
            extract('year', Transaction.created_at).label('year'),
            extract('month', Transaction.created_at).label('month'),
            extract('day', Transaction.created_at).label('day'),
            func.sum(Transaction.quantity).label('total_quantity')
        ).filter(
            Transaction.warehouse_id == warehouse_id,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).group_by(
            extract('year', Transaction.created_at),
            extract('month', Transaction.created_at),
            extract('day', Transaction.created_at)
        ).order_by(
            'year', 'month', 'day'
        )
        
        results = query.all()
        
        # 计算利用率
        utilization_data = []
        for row in results:
            date_str = f"{int(row.year):04d}-{int(row.month):02d}-{int(row.day):02d}"
            utilization = (row.total_quantity / warehouse.capacity * 100) if warehouse.capacity else 0
            utilization_data.append({
                'date': date_str,
                'utilization': round(utilization, 2),
                'quantity': row.total_quantity or 0,
                'capacity': warehouse.capacity
            })
        
        return utilization_data


# 导出便捷函数
def get_inventory_trend(warehouse_id=None, days=30):
    return AnalyticsService.get_inventory_trend(warehouse_id, days)


def get_stock_turnover_rate(warehouse_id=None, days=30):
    return AnalyticsService.get_stock_turnover_rate(warehouse_id, days)


def get_demand_forecast(spare_part_id, days=30):
    return AnalyticsService.get_demand_forecast(spare_part_id, days)


def get_reorder_suggestions(warehouse_id=None):
    return AnalyticsService.get_reorder_suggestions(warehouse_id)
