"""
库位服务层
"""

from app.models.warehouse_location import WarehouseLocation
from app.extensions import db


class LocationService:
    """库位服务类"""
    
    @staticmethod
    def create_location(data):
        """创建库位"""
        location = WarehouseLocation(
            warehouse_id=data['warehouse_id'],
            location_code=data['location_code'],
            location_name=data.get('location_name'),
            location_type=data.get('location_type'),
            max_capacity=data.get('max_capacity'),
            current_capacity=data.get('current_capacity', 0),
            status=data.get('status', 'available'),
            remark=data.get('remark'),
            created_by=data.get('created_by')
        )
        db.session.add(location)
        db.session.commit()
        return location
    
    @staticmethod
    def update_location(location_id, data):
        """更新库位"""
        location = WarehouseLocation.query.get(location_id)
        if not location:
            return None
        
        for key, value in data.items():
            if hasattr(location, key):
                setattr(location, key, value)
        
        db.session.commit()
        return location
    
    @staticmethod
    def delete_location(location_id):
        """删除库位"""
        location = WarehouseLocation.query.get(location_id)
        if not location:
            return False
        
        # 检查是否有关联的批次
        if location.batches.count() > 0:
            return False
        
        db.session.delete(location)
        db.session.commit()
        return True
    
    @staticmethod
    def get_location(location_id):
        """获取库位详情"""
        return WarehouseLocation.query.get(location_id)
    
    @staticmethod
    def get_locations(filters=None, page=1, per_page=20):
        """获取库位列表"""
        query = WarehouseLocation.query
        
        if filters:
            if filters.get('warehouse_id'):
                query = query.filter(WarehouseLocation.warehouse_id == filters['warehouse_id'])
            if filters.get('location_code'):
                query = query.filter(WarehouseLocation.location_code.like(f"%{filters['location_code']}%"))
            if filters.get('location_name'):
                query = query.filter(WarehouseLocation.location_name.like(f"%{filters['location_name']}%"))
            if filters.get('location_type'):
                query = query.filter(WarehouseLocation.location_type == filters['location_type'])
            if filters.get('status'):
                query = query.filter(WarehouseLocation.status == filters['status'])
        
        pagination = query.order_by(WarehouseLocation.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination
    
    @staticmethod
    def get_location_by_warehouse(warehouse_id):
        """获取仓库的库位"""
        return WarehouseLocation.query.filter_by(warehouse_id=warehouse_id).all()
    
    @staticmethod
    def get_inventory(location_id):
        """获取库位库存"""
        from app.models.batch import Batch
        
        # 计算库位中的库存总量
        total_quantity = db.session.query(db.func.sum(Batch.quantity)).filter(
            Batch.location_id == location_id
        ).scalar() or 0
        
        return total_quantity
    
    @staticmethod
    def get_utilization_rate(location_id):
        """获取库位利用率"""
        location = WarehouseLocation.query.get(location_id)
        if not location or not location.max_capacity:
            return 0
        
        inventory = LocationService.get_inventory(location_id)
        return min(100, (inventory / location.max_capacity) * 100)
    
    @staticmethod
    def get_available_space(location_id):
        """获取可用空间"""
        location = WarehouseLocation.query.get(location_id)
        if not location or not location.max_capacity:
            return 0
        
        inventory = LocationService.get_inventory(location_id)
        return max(0, location.max_capacity - inventory)
