"""
货位服务 V3
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.models.warehouse_v3.location import WarehouseLocationV3
from app.extensions import db


class LocationV3Service:
    """货位服务 V3"""
    
    @staticmethod
    def create_location(data: Dict) -> WarehouseLocationV3:
        """创建货位"""
        location = WarehouseLocationV3(
            warehouse_id=data['warehouse_id'],
            code=data['code'],
            name=data.get('name'),
            zone_code=data.get('zone_code'),
            aisle_code=data.get('aisle_code'),
            rack_code=data.get('rack_code'),
            level_code=data.get('level_code'),
            type=data.get('type', 'standard'),
            size_type=data.get('size_type', 'medium'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            max_weight=data.get('max_weight'),
            max_volume=data.get('max_volume'),
            storage_type=data.get('storage_type', 'mixed'),
            temperature_range=data.get('temperature_range'),
            humidity_range=data.get('humidity_range'),
            priority=data.get('priority', 0),
            description=data.get('description')
        )
        
        db.session.add(location)
        db.session.commit()
        return location
    
    @staticmethod
    def get_available_locations(warehouse_id: int, filters: Dict = None) -> List[WarehouseLocationV3]:
        """获取可用货位"""
        query = WarehouseLocationV3.query.filter_by(
            warehouse_id=warehouse_id,
            status='available',
            is_active=True
        )
        
        if filters:
            if filters.get('type'):
                query = query.filter_by(type=filters['type'])
            if filters.get('size_type'):
                query = query.filter_by(size_type=filters['size_type'])
            if filters.get('zone_code'):
                query = query.filter_by(zone_code=filters['zone_code'])
        
        return query.order_by(WarehouseLocationV3.priority.desc()).all()
    
    @staticmethod
    def update_location_status(location_id: int, status: str) -> bool:
        """更新货位状态"""
        location = WarehouseLocationV3.query.filter_by(id=location_id).first()
        if not location:
            return False
        
        location.status = status
        location.updated_at = datetime.utcnow()
        db.session.commit()
        return True
