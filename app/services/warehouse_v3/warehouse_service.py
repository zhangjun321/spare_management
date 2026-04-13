"""
仓库服务 V3
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.warehouse_v3.warehouse import WarehouseV3
from app.extensions import db


class WarehouseV3Service:
    """仓库服务 V3"""
    
    @staticmethod
    def create_warehouse(data: Dict) -> WarehouseV3:
        """创建仓库"""
        warehouse = WarehouseV3(
            code=data['code'],
            name=data['name'],
            type=data.get('type', 'general'),
            level=data.get('level', 'A'),
            total_area=data.get('total_area'),
            total_capacity=data.get('total_capacity'),
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email'),
            manager_id=data.get('manager_id'),
            temperature_control=data.get('temperature_control', False),
            humidity_control=data.get('humidity_control', False),
            security_level=data.get('security_level', 'normal'),
            ai_enabled=data.get('ai_enabled', True),
            ai_config=data.get('ai_config'),
            description=data.get('description'),
            remarks=data.get('remarks'),
            created_by=data.get('created_by'),
            updated_by=data.get('updated_by')
        )
        
        db.session.add(warehouse)
        db.session.commit()
        return warehouse
    
    @staticmethod
    def get_warehouse_by_id(warehouse_id: int) -> Optional[WarehouseV3]:
        """根据 ID 获取仓库"""
        return WarehouseV3.query.filter_by(id=warehouse_id, is_active=True).first()
    
    @staticmethod
    def get_all_warehouses(page: int = 1, per_page: int = 20, filters: Dict = None) -> Dict:
        """获取所有仓库（分页）"""
        query = WarehouseV3.query.filter_by(is_active=True)
        
        if filters:
            if filters.get('type'):
                query = query.filter_by(type=filters['type'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('keyword'):
                keyword = f"%{filters['keyword']}%"
                query = query.filter(
                    (WarehouseV3.name.like(keyword)) | 
                    (WarehouseV3.code.like(keyword))
                )
        
        pagination = query.order_by(WarehouseV3.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }
    
    @staticmethod
    def update_warehouse(warehouse_id: int, data: Dict) -> Optional[WarehouseV3]:
        """更新仓库"""
        warehouse = WarehouseV3Service.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            return None
        
        # 更新字段
        updatable_fields = [
            'name', 'type', 'level', 'status', 'total_area', 'usable_area',
            'total_volume', 'total_capacity', 'address', 'phone', 'email',
            'manager_id', 'temperature_control', 'humidity_control',
            'security_level', 'ai_enabled', 'ai_config', 'description',
            'remarks', 'updated_by'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(warehouse, field, data[field])
        
        warehouse.updated_at = datetime.utcnow()
        db.session.commit()
        return warehouse
    
    @staticmethod
    def delete_warehouse(warehouse_id: int) -> bool:
        """删除仓库（软删除）"""
        warehouse = WarehouseV3Service.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            return False
        
        warehouse.is_active = False
        db.session.commit()
        return True
    
    @staticmethod
    def get_warehouse_statistics(warehouse_id: int) -> Dict:
        """获取仓库统计信息"""
        from app.models.warehouse_v3.inventory import InventoryV3
        from app.models.warehouse_v3.location import WarehouseLocationV3
        
        warehouse = WarehouseV3Service.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            return {}
        
        # 货位统计
        total_locations = warehouse.locations.count()
        available_locations = warehouse.locations.filter_by(status='available').count()
        occupied_locations = warehouse.locations.filter_by(status='occupied').count()
        
        # 库存统计
        total_skus = warehouse.inventories.count()
        total_quantity = db.session.query(db.func.sum(InventoryV3.quantity)).filter_by(
            warehouse_id=warehouse_id
        ).scalar() or 0
        
        # 计算使用率
        utilization_rate = (occupied_locations / total_locations * 100) if total_locations > 0 else 0
        
        return {
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'total_locations': total_locations,
            'available_locations': available_locations,
            'occupied_locations': occupied_locations,
            'utilization_rate': round(utilization_rate, 2),
            'total_skus': total_skus,
            'total_quantity': float(total_quantity) if total_quantity else 0
        }
