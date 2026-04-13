"""
库存服务 V3
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.warehouse_v3.inventory import InventoryV3
from app.extensions import db


class InventoryV3Service:
    """库存服务 V3"""
    
    @staticmethod
    def get_inventory_list(warehouse_id: int = None, page: int = 1, per_page: int = 20, filters: Dict = None) -> Dict:
        """获取库存列表（分页）"""
        query = InventoryV3.query
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        if filters:
            if filters.get('part_id'):
                query = query.filter_by(part_id=filters['part_id'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('abc_class'):
                query = query.filter_by(abc_class=filters['abc_class'])
        
        pagination = query.order_by(InventoryV3.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def get_inventory_summary(warehouse_id: int) -> Dict:
        """获取库存汇总"""
        from app.models.warehouse_v3.warehouse import WarehouseV3
        
        warehouse = WarehouseV3.query.get(warehouse_id)
        if not warehouse:
            return {}
        
        total_skus = warehouse.inventories.count()
        
        # 查询总数量
        result = db.session.query(
            db.func.sum(InventoryV3.quantity),
            db.func.sum(InventoryV3.total_cost)
        ).filter_by(warehouse_id=warehouse_id).first()
        
        total_quantity = float(result[0]) if result[0] else 0
        total_value = float(result[1]) if result[1] else 0
        
        # ABC 分类统计
        abc_stats = {}
        for abc_class in ['A', 'B', 'C']:
            count = InventoryV3.query.filter_by(
                warehouse_id=warehouse_id,
                abc_class=abc_class
            ).count()
            abc_stats[abc_class] = count
        
        # 预警统计
        warnings = InventoryV3.query.filter_by(
            warehouse_id=warehouse_id,
            status='warning'
        ).count()
        
        return {
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'total_skus': total_skus,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'abc_stats': abc_stats,
            'warning_count': warnings
        }
    
    @staticmethod
    def adjust_inventory(inventory_id: int, adjustment_data: Dict, user_id: int) -> bool:
        """调整库存"""
        inventory = InventoryV3.query.get(inventory_id)
        if not inventory:
            return False
        
        adjustment_type = adjustment_data.get('type')  # increase/decrease
        quantity = adjustment_data.get('quantity', 0)
        reason = adjustment_data.get('reason', '')
        
        if adjustment_type == 'increase':
            inventory.quantity += quantity
            inventory.available_quantity += quantity
        elif adjustment_type == 'decrease':
            inventory.quantity -= quantity
            inventory.available_quantity -= quantity
        
        inventory.updated_at = datetime.utcnow()
        
        # 记录调整日志（这里简化处理）
        print(f"库存调整：{inventory_id}, 类型：{adjustment_type}, 数量：{quantity}, 原因：{reason}")
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_inventory_warnings(warehouse_id: int = None) -> List[Dict]:
        """获取库存预警"""
        query = InventoryV3.query.filter_by(status='warning')
        
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        
        warnings = query.all()
        
        return [{
            'inventory_id': w.id,
            'part_id': w.part_id,
            'warehouse_id': w.warehouse_id,
            'current_quantity': float(w.quantity) if w.quantity else 0,
            'min_quantity': float(w.min_quantity) if w.min_quantity else 0,
            'max_quantity': float(w.max_quantity) if w.max_quantity else 0,
            'status': w.status,
            'abc_class': w.abc_class
        } for w in warnings]
