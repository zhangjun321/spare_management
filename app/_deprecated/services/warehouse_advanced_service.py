
"""
仓库高级管理服务
包含：盘点管理、库龄分析、ABC分类、KPI计算等
"""

from datetime import datetime, timedelta
from app.extensions import db
from app.models.inventory_check import InventoryCheckLegacy as InventoryCheck, InventoryCheckItemLegacy as InventoryCheckItem, StockAgeAnalysis
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseZone, WarehouseRack, WarehouseLocation
from app.models.spare_part import SparePart
from app.models.batch import Batch
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)


class InventoryCheckService:
    """库存盘点服务"""
    
    @staticmethod
    def generate_check_code():
        """生成盘点单号"""
        today = datetime.now().strftime('%Y%m%d')
        last_check = InventoryCheck.query.filter(
            InventoryCheck.check_code.like(f'PC{today}%')
        ).order_by(InventoryCheck.check_code.desc()).first()
        
        if last_check:
            seq = int(last_check.check_code[-4:]) + 1
        else:
            seq = 1
        
        return f'PC{today}{seq:04d}'
    
    @staticmethod
    def create_inventory_check(data, user_id):
        """创建盘点单"""
        check_code = InventoryCheckService.generate_check_code()
        
        check = InventoryCheck(
            check_code=check_code,
            check_name=data.get('check_name'),
            check_type=data.get('check_type', 'full'),
            warehouse_id=data.get('warehouse_id'),
            location_id=data.get('location_id'),
            category_id=data.get('category_id'),
            abc_class=data.get('abc_class'),
            start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d') if data.get('start_date') else None,
            end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d') if data.get('end_date') else None,
            remark=data.get('remark'),
            created_by=user_id,
            status='draft'
        )
        
        db.session.add(check)
        db.session.flush()
        
        # 生成盘点明细
        InventoryCheckService.generate_check_items(check)
        
        db.session.commit()
        return check
    
    @staticmethod
    def generate_check_items(check):
        """生成盘点明细"""
        query = db.session.query(
            SparePart,
            Batch,
            func.coalesce(func.sum(Batch.quantity), 0).label('total_quantity')
        ).join(Batch, SparePart.id == Batch.spare_part_id)
        
        # 筛选条件
        filters = [Batch.warehouse_id == check.warehouse_id]
        
        if check.location_id:
            filters.append(Batch.location_id == check.location_id)
        
        if check.category_id:
            filters.append(SparePart.category_id == check.category_id)
        
        if check.abc_class:
            filters.append(SparePart.abc_class == check.abc_class)
        
        # 循环盘点：只盘点上次盘点时间超过30天的
        if check.check_type == 'cyclical':
            thirty_days_ago = datetime.now() - timedelta(days=30)
            subquery = db.session.query(InventoryCheckItem.spare_part_id).join(
                InventoryCheck
            ).filter(
                InventoryCheck.warehouse_id == check.warehouse_id,
                InventoryCheck.status == 'completed',
                InventoryCheck.updated_at &gt;= thirty_days_ago
            ).subquery()
            filters.append(~SparePart.id.in_(subquery))
        
        # 随机抽盘：随机选择20%的物料
        if check.check_type == 'random':
            all_parts = SparePart.query.join(Batch).filter(Batch.warehouse_id == check.warehouse_id).all()
            import random
            random_parts = random.sample(all_parts, min(len(all_parts), int(len(all_parts) * 0.2)))
            part_ids = [p.id for p in random_parts]
            filters.append(SparePart.id.in_(part_ids))
        
        # 执行查询
        query = query.filter(*filters).group_by(SparePart.id, Batch.id)
        results = query.all()
        
        # 创建盘点明细
        items = []
        for spare_part, batch, quantity in results:
            item = InventoryCheckItem(
                inventory_check_id=check.id,
                spare_part_id=spare_part.id,
                batch_id=batch.id,
                warehouse_id=check.warehouse_id,
                location_id=batch.location_id,
                system_quantity=quantity,
                status='pending'
            )
            items.append(item)
        
        db.session.bulk_save_objects(items)
        
        # 更新统计信息
        check.total_items = len(items)
        check.checked_items = 0
        check.discrepancy_items = 0
    
    @staticmethod
    def get_inventory_checks(filters=None, page=1, per_page=20):
        """获取盘点单列表"""
        query = InventoryCheck.query
        
        if filters:
            if filters.get('warehouse_id'):
                query = query.filter(InventoryCheck.warehouse_id == filters['warehouse_id'])
            if filters.get('check_type'):
                query = query.filter(InventoryCheck.check_type == filters['check_type'])
            if filters.get('status'):
                query = query.filter(InventoryCheck.status == filters['status'])
            if filters.get('start_date'):
                query = query.filter(InventoryCheck.created_at &gt;= filters['start_date'])
            if filters.get('end_date'):
                query = query.filter(InventoryCheck.created_at &lt;= filters['end_date'])
        
        return query.order_by(InventoryCheck.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def update_check_item(item_id, check_quantity, user_id, is_second_check=False):
        """更新盘点结果"""
        item = InventoryCheckItem.query.get(item_id)
        if not item:
            raise ValueError('盘点明细不存在')
        
        if is_second_check:
            item.second_check_quantity = check_quantity
            item.second_checked_by = user_id
            item.second_checked_at = datetime.now()
        else:
            item.check_quantity = check_quantity
            item.checked_by = user_id
            item.checked_at = datetime.now()
        
        # 计算差异
        item.calculate_difference()
        
        # 更新盘点单统计
        check = item.inventory_check
        check.checked_items = InventoryCheckItem.query.filter(
            InventoryCheckItem.inventory_check_id == check.id,
            InventoryCheckItem.status != 'pending'
        ).count()
        
        check.discrepancy_items = InventoryCheckItem.query.filter(
            InventoryCheckItem.inventory_check_id == check.id,
            InventoryCheckItem.status == 'difference'
        ).count()
        
        check.discrepancy_value = db.session.query(
            func.sum(InventoryCheckItem.difference_value)
        ).filter(InventoryCheckItem.inventory_check_id == check.id).scalar() or 0
        
        db.session.commit()
        return item
    
    @staticmethod
    def complete_check(check_id, user_id):
        """完成盘点"""
        check = InventoryCheck.query.get(check_id)
        if not check:
            raise ValueError('盘点单不存在')
        
        check.status = 'completed'
        check.checked_by = user_id
        check.updated_at = datetime.now()
        
        db.session.commit()
        return check
    
    @staticmethod
    def approve_check(check_id, user_id):
        """审核盘点"""
        check = InventoryCheck.query.get(check_id)
        if not check:
            raise ValueError('盘点单不存在')
        
        check.approved_by = user_id
        check.approved_at = datetime.now()
        
        db.session.commit()
        return check


class StockAgeService:
    """库龄分析服务"""
    
    @staticmethod
    def analyze_stock_age(warehouse_id=None):
        """分析库龄"""
        # 清空之前的分析结果
        StockAgeAnalysis.query.filter(
            StockAgeAnalysis.analysis_date &lt; datetime.now().date()
        ).delete()
        
        # 查询批次信息
        query = db.session.query(
            Batch,
            SparePart,
            Warehouse
        ).join(SparePart, Batch.spare_part_id == SparePart.id)\
         .join(Warehouse, Batch.warehouse_id == Warehouse.id)\
         .filter(Batch.quantity &gt; 0)
        
        if warehouse_id:
            query = query.filter(Batch.warehouse_id == warehouse_id)
        
        batches = query.all()
        
        analyses = []
        for batch, spare_part, warehouse in batches:
            # 计算库龄
            stock_age_days = (datetime.now() - batch.created_at).days
            
            # 确定库龄等级
            if stock_age_days &lt;= 30:
                stock_age_level = 'normal'
            elif stock_age_days &lt;= 90:
                stock_age_level = 'warning'
            elif stock_age_days &lt;= 180:
                stock_age_level = 'danger'
            else:
                stock_age_level = 'critical'
            
            # 判断是否呆滞
            is_slow_moving = stock_age_days &gt; 90
            is_obsolete = stock_age_days &gt; 365
            
            # 计算价值
            total_value = batch.quantity * float(spare_part.unit_price) if spare_part.unit_price else None
            
            analysis = StockAgeAnalysis(
                warehouse_id=warehouse.id,
                spare_part_id=spare_part.id,
                batch_id=batch.id,
                stock_age_days=stock_age_days,
                stock_age_level=stock_age_level,
                quantity=batch.quantity,
                unit_price=spare_part.unit_price,
                total_value=total_value,
                is_slow_moving=is_slow_moving,
                is_obsolete=is_obsolete,
                analysis_date=datetime.now()
            )
            analyses.append(analysis)
        
        db.session.bulk_save_objects(analyses)
        db.session.commit()
        
        return analyses
    
    @staticmethod
    def get_stock_age_statistics(warehouse_id=None):
        """获取库龄统计"""
        query = db.session.query(
            StockAgeAnalysis.stock_age_level,
            func.count(StockAgeAnalysis.id).label('count'),
            func.sum(StockAgeAnalysis.quantity).label('total_quantity'),
            func.sum(StockAgeAnalysis.total_value).label('total_value')
        )
        
        if warehouse_id:
            query = query.filter(StockAgeAnalysis.warehouse_id == warehouse_id)
        
        stats = query.group_by(StockAgeAnalysis.stock_age_level).all()
        
        result = {
            'normal': {'count': 0, 'quantity': 0, 'value': 0},
            'warning': {'count': 0, 'quantity': 0, 'value': 0},
            'danger': {'count': 0, 'quantity': 0, 'value': 0},
            'critical': {'count': 0, 'quantity': 0, 'value': 0}
        }
        
        for level, count, quantity, value in stats:
            result[level] = {
                'count': count,
                'quantity': quantity or 0,
                'value': float(value or 0)
            }
        
        return result
    
    @staticmethod
    def get_slow_moving_items(warehouse_id=None, page=1, per_page=20):
        """获取呆滞库存"""
        query = StockAgeAnalysis.query.filter(
            StockAgeAnalysis.is_slow_moving == True
        )
        
        if warehouse_id:
            query = query.filter(StockAgeAnalysis.warehouse_id == warehouse_id)
        
        return query.order_by(StockAgeAnalysis.stock_age_days.desc())\
                    .paginate(page=page, per_page=per_page, error_out=False)


class ABCClassificationService:
    """ABC分类管理服务"""
    
    @staticmethod
    def calculate_abc_classification(warehouse_id=None):
        """计算ABC分类"""
        # 获取所有备件的库存价值
        query = db.session.query(
            SparePart,
            func.sum(Batch.quantity * SparePart.unit_price).label('total_value')
        ).join(Batch, SparePart.id == Batch.spare_part_id)\
         .filter(Batch.quantity &gt; 0)
        
        if warehouse_id:
            query = query.filter(Batch.warehouse_id == warehouse_id)
        
        results = query.group_by(SparePart.id).order_by(
            func.sum(Batch.quantity * SparePart.unit_price).desc()
        ).all()
        
        # 计算总价值
        total_value = sum(float(r[1] or 0) for r in results)
        
        # 进行ABC分类
        cumulative_value = 0
        for spare_part, value in results:
            if total_value == 0:
                abc_class = 'C'
            else:
                cumulative_value += float(value or 0)
                percentage = cumulative_value / total_value * 100
                
                if percentage &lt;= 80:
                    abc_class = 'A'
                elif percentage &lt;= 95:
                    abc_class = 'B'
                else:
                    abc_class = 'C'
            
            spare_part.abc_class = abc_class
        
        db.session.commit()
        return results
    
    @staticmethod
    def get_abc_statistics(warehouse_id=None):
        """获取ABC分类统计"""
        query = db.session.query(
            SparePart.abc_class,
            func.count(SparePart.id).label('count'),
            func.sum(Batch.quantity).label('total_quantity'),
            func.sum(Batch.quantity * SparePart.unit_price).label('total_value')
        ).join(Batch, SparePart.id == Batch.spare_part_id)\
         .filter(Batch.quantity &gt; 0)
        
        if warehouse_id:
            query = query.filter(Batch.warehouse_id == warehouse_id)
        
        stats = query.group_by(SparePart.abc_class).all()
        
        result = {
            'A': {'count': 0, 'quantity': 0, 'value': 0},
            'B': {'count': 0, 'quantity': 0, 'value': 0},
            'C': {'count': 0, 'quantity': 0, 'value': 0}
        }
        
        for abc_class, count, quantity, value in stats:
            if abc_class in result:
                result[abc_class] = {
                    'count': count,
                    'quantity': quantity or 0,
                    'value': float(value or 0)
                }
        
        return result


class WarehouseKPIService:
    """仓库KPI计算服务"""
    
    @staticmethod
    def calculate_kpis(warehouse_id=None, period_days=30):
        """计算仓库KPI"""
        from app.models.transaction import Transaction
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # 基础统计
        total_warehouses = Warehouse.query.filter_by(is_active=True).count()
        if warehouse_id:
            warehouses = [Warehouse.query.get(warehouse_id)]
        else:
            warehouses = Warehouse.query.filter_by(is_active=True).all()
        
        kpis = {
            'period_days': period_days,
            'total_warehouses': total_warehouses,
            'warehouses': []
        }
        
        for warehouse in warehouses:
            # 仓库统计
            total_locations = WarehouseLocation.query.filter_by(warehouse_id=warehouse.id).count()
            occupied_locations = WarehouseLocation.query.filter_by(
                warehouse_id=warehouse.id,
                status='occupied'
            ).count()
            
            # 库存统计
            from app.services.inventory_service import InventoryService
            inventory_stats = InventoryService.get_inventory_statistics(warehouse.id)
            
            # 交易统计
            inbound_count = Transaction.query.filter(
                Transaction.warehouse_id == warehouse.id,
                Transaction.transaction_type == 'inbound',
                Transaction.created_at &gt;= start_date
            ).count()
            
            outbound_count = Transaction.query.filter(
                Transaction.warehouse_id == warehouse.id,
                Transaction.transaction_type == 'outbound',
                Transaction.created_at &gt;= start_date
            ).count()
            
            # 计算KPI
            location_utilization = (occupied_locations / total_locations * 100) if total_locations &gt; 0 else 0
            inventory_turnover = InventoryService.calculate_turnover_rate(warehouse.id, period_days)
            order_fulfillment_rate = WarehouseKPIService.calculate_fulfillment_rate(warehouse.id, start_date, end_date)
            accuracy_rate = WarehouseKPIService.calculate_accuracy_rate(warehouse.id, start_date, end_date)
            
            warehouse_kpi = {
                'warehouse_id': warehouse.id,
                'warehouse_name': warehouse.name,
                'warehouse_code': warehouse.code,
                'location_utilization': round(location_utilization, 2),
                'total_locations': total_locations,
                'occupied_locations': occupied_locations,
                'inventory_turnover': round(inventory_turnover, 2),
                'order_fulfillment_rate': round(order_fulfillment_rate, 2),
                'accuracy_rate': round(accuracy_rate, 2),
                'inbound_count': inbound_count,
                'outbound_count': outbound_count,
                'total_inventory_value': float(inventory_stats.get('total_value', 0)),
                'total_quantity': inventory_stats.get('total_quantity', 0)
            }
            
            kpis['warehouses'].append(warehouse_kpi)
        
        return kpis
    
    @staticmethod
    def calculate_fulfillment_rate(warehouse_id, start_date, end_date):
        """计算订单履约率"""
        from app.models.transaction import Transaction
        
        total_orders = Transaction.query.filter(
            Transaction.warehouse_id == warehouse_id,
            Transaction.transaction_type == 'outbound',
            Transaction.created_at &gt;= start_date,
            Transaction.created_at &lt;= end_date
        ).count()
        
        if total_orders == 0:
            return 100
        
        # 这里简化处理，实际应该根据订单完成时间计算
        return 95
    
    @staticmethod
    def calculate_accuracy_rate(warehouse_id, start_date, end_date):
        """计算库存准确率"""
        # 基于盘点结果计算准确率
        checks = InventoryCheck.query.filter(
            InventoryCheck.warehouse_id == warehouse_id,
            InventoryCheck.status == 'completed',
            InventoryCheck.updated_at &gt;= start_date,
            InventoryCheck.updated_at &lt;= end_date
        ).all()
        
        if not checks:
            return 100
        
        total_items = sum(c.total_items for c in checks)
        discrepancy_items = sum(c.discrepancy_items for c in checks)
        
        if total_items == 0:
            return 100
        
        return ((total_items - discrepancy_items) / total_items) * 100

