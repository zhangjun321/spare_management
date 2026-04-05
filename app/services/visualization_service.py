"""
仓库可视化服务
包含：仓库平面图、库存热力图、动画数据生成
"""

from flask import current_app
from app.extensions import db
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation as StorageLocation
from app.models.inventory import InventoryRecord
from sqlalchemy import func


class WarehouseVisualizationService:
    """仓库可视化服务类"""
    
    @staticmethod
    def get_warehouse_layout(warehouse_id):
        """
        获取仓库布局数据（用于平面图绘制）
        注意：此功能需要 StorageZone 和 StorageRack 模型
        目前返回简化版本
        """
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        
        # 获取库位数据
        from app.models.warehouse_location import WarehouseLocation
        locations_data = []
        
        locations = WarehouseLocation.query.filter_by(
            warehouse_id=warehouse_id
        ).all()
        
        for location in locations:
            locations_data.append({
                'id': location.id,
                'code': location.location_code,
                'name': location.location_name,
                'type': location.location_type,
                'is_occupied': location.current_capacity > 0 if location.current_capacity else False,
                'quantity': location.current_capacity or 0,
                'max_capacity': location.max_capacity,
                'status': location.status,
                'color': WarehouseVisualizationService._get_location_status_color(location.status)
            })
        
        return {
            'warehouse_id': warehouse_id,
            'warehouse_name': warehouse.name,
            'zones': [],  # 暂不支持库区
            'racks': [],  # 暂不支持货架
            'locations': locations_data,
            'statistics': {
                'total_zones': 0,
                'total_racks': 0,
                'total_locations': len(locations_data),
                'occupied_locations': sum(1 for loc in locations_data if loc['is_occupied']),
                'usage_rate': (sum(1 for loc in locations_data if loc['is_occupied']) / len(locations_data) * 100) if locations_data else 0
            }
        }
    
    @staticmethod
    def get_heatmap_data(warehouse_id, dimension='density'):
        """
        获取热力图数据
        
        Args:
            warehouse_id: 仓库 ID
            dimension: 维度 (density-密度/turnover-周转率/age-库龄)
        
        Returns:
            dict: 热力图数据 {points: [{x, y, value}], max_value, min_value}
        """
        locations = StorageLocation.query.join(StorageRack).join(StorageZone).filter(
            StorageZone.warehouse_id == warehouse_id,
            StorageLocation.is_active == True
        ).all()
        
        heatmap_points = []
        values = []
        
        for location in locations:
            # 获取库存数据
            inventory = InventoryRecord.query.filter_by(
                location_id=location.id,
                status='normal'
            ).first()
            
            # 根据维度计算值
            if dimension == 'density':
                # 库存密度
                value = inventory.quantity if inventory else 0
            elif dimension == 'turnover':
                # 周转率（简化计算：出库次数/库存量）
                value = WarehouseVisualizationService._calculate_turnover_rate(inventory)
            elif dimension == 'age':
                # 库龄
                value = inventory.stock_age_days if inventory else 0
            else:
                value = 0
            
            if value > 0 or dimension == 'density':
                heatmap_points.append({
                    'location_id': location.id,
                    'location_code': location.code,
                    'x': location.column,  # 列作为 X 坐标
                    'y': location.row,     # 层作为 Y 坐标
                    'rack_id': location.rack_id,
                    'value': value
                })
                values.append(value)
        
        return {
            'dimension': dimension,
            'points': heatmap_points,
            'max_value': max(values) if values else 0,
            'min_value': min(values) if values else 0,
            'avg_value': sum(values) / len(values) if values else 0
        }
    
    @staticmethod
    def get_inbound_animation_data(order_id):
        """
        获取入库动画数据
        
        Args:
            order_id: 入库单 ID
        
        Returns:
            dict: 动画数据 {steps: [...], duration, items: [...]}
        """
        from app.models.inventory import InboundOrder
        
        order = InboundOrder.query.get_or_404(order_id)
        
        animation_steps = []
        items_data = []
        
        # 为每个入库项生成动画
        for index, item in enumerate(order.items.all()):
            if not item.location_id:
                continue
            
            location = StorageLocation.query.get(item.location_id)
            if not location:
                continue
            
            rack = StorageRack.query.get(location.rack_id)
            zone = StorageZone.query.get(rack.zone_id) if rack else None
            
            # 动画步骤
            step_data = {
                'item_id': item.id,
                'spare_part_id': item.spare_part_id,
                'spare_part_name': item.spare_part.name,
                'quantity': item.actual_quantity,
                'steps': [
                    {
                        'order': 1,
                        'name': '入库口出现',
                        'position': 'entrance',
                        'duration': 1000,
                        'description': f'{item.spare_part.name} 从入库口出现'
                    },
                    {
                        'order': 2,
                        'name': '移动到库区',
                        'position': f'zone_{zone.id}' if zone else 'zone',
                        'duration': 1500,
                        'description': f'移动到 {zone.name if zone else "库区"}'
                    },
                    {
                        'order': 3,
                        'name': '移动到货架',
                        'position': f'rack_{rack.id}' if rack else 'rack',
                        'duration': 1000,
                        'description': f'移动到 {rack.code if rack else "货架"}'
                    },
                    {
                        'order': 4,
                        'name': '放入库位',
                        'position': f'location_{location.id}',
                        'duration': 1500,
                        'description': f'放入库位 {location.code}'
                    },
                    {
                        'order': 5,
                        'name': '库位高亮',
                        'position': f'location_{location.id}',
                        'duration': 2000,
                        'highlight': True,
                        'description': f'库位 {location.code} 高亮显示，数量更新为 {item.actual_quantity}'
                    }
                ],
                'total_duration': 7000
            }
            
            animation_steps.append(step_data)
            
            items_data.append({
                'item_id': item.id,
                'spare_part_name': item.spare_part.name,
                'quantity': item.actual_quantity,
                'target_location': location.code if location else '未知',
                'zone_name': zone.name if zone else '未知'
            })
        
        return {
            'order_id': order_id,
            'order_number': order.order_number,
            'items': items_data,
            'animation_steps': animation_steps,
            'total_duration': sum(step['total_duration'] for step in animation_steps),
            'can_play': len(animation_steps) > 0
        }
    
    @staticmethod
    def get_inventory_status(warehouse_id):
        """
        获取库存状态概览
        
        Args:
            warehouse_id: 仓库 ID
        
        Returns:
            dict: 库存状态数据
        """
        # 按状态统计
        status_stats = db.session.query(
            InventoryRecord.status,
            func.count(InventoryRecord.id),
            func.sum(InventoryRecord.quantity)
        ).filter(
            InventoryRecord.warehouse_id == warehouse_id
        ).group_by(InventoryRecord.status).all()
        
        # 按 ABC 分类统计
        abc_stats = db.session.query(
            InventoryRecord.spare_part_id,
            func.sum(InventoryRecord.quantity)
        ).filter(
            InventoryRecord.warehouse_id == warehouse_id,
            InventoryRecord.status == 'normal'
        ).group_by(InventoryRecord.spare_part_id).all()
        
        # 获取备件的 ABC 分类
        from app.models.spare_part import SparePart
        abc_counts = {'A': 0, 'B': 0, 'C': 0}
        for part_id, qty in abc_stats:
            part = SparePart.query.get(part_id)
            if part and part.abc_class:
                abc_counts[part.abc_class] = abc_counts.get(part.abc_class, 0) + 1
        
        return {
            'status_stats': [
                {'status': status, 'count': count, 'quantity': qty or 0}
                for status, count, qty in status_stats
            ],
            'abc_classification': abc_counts,
            'total_items': sum(abc_counts.values()),
            'total_quantity': sum(stat[2] or 0 for stat in status_stats if stat[0] == 'normal')
        }
    
    @staticmethod
    def _get_zone_color(zone_type):
        """获取库区颜色"""
        color_map = {
            'A': '#4CAF50',  # 绿色 - A 类区（快速周转）
            'B': '#2196F3',  # 蓝色 - B 类区
            'C': '#FF9800',  # 橙色 - C 类区
            'fast-moving': '#4CAF50',  # 快速周转区
            'normal': '#2196F3',  # 普通区
            'cold': '#00BCD4',  # 冷藏区
            'hazardous': '#F44336',  # 危险品区
            'valuable': '#9C27B0'  # 贵重物品区
        }
        return color_map.get(zone_type, '#9E9E9E')
    
    @staticmethod
    def _get_location_status(location, inventory):
        """获取库位状态"""
        if not location.is_active:
            return 'inactive'
        if not location.is_occupied:
            return 'empty'
        if inventory and inventory.status != 'normal':
            return inventory.status
        if inventory and inventory.quantity > 0:
            return 'occupied'
        return 'empty'
    
    @staticmethod
    def _get_location_color(location, inventory):
        """获取库位颜色"""
        status = WarehouseVisualizationService._get_location_status(location, inventory)
        
        color_map = {
            'empty': '#E0E0E0',      # 灰色 - 空闲
            'occupied': '#4CAF50',   # 绿色 - 正常占用
            'locked': '#FF9800',     # 橙色 - 锁定
            'damaged': '#F44336',    # 红色 - 损坏
            'expired': '#9E9E9E',    # 深灰 - 过期
            'inactive': '#BDBDBD'    # 浅灰 - 未启用
        }
        
        return color_map.get(status, '#9E9E9E')
    
    @staticmethod
    def _calculate_turnover_rate(inventory):
        """计算周转率（简化版本）"""
        if not inventory or inventory.quantity == 0:
            return 0
        
        # 实际应该查询出库记录计算
        # 这里简化为：30 / 库龄（假设 30 天为标准周期）
        if inventory.stock_age_days > 0:
            return min(30 / inventory.stock_age_days, 10)  # 最大为 10
        return 5  # 默认周转率


# 全局服务实例
warehouse_visualization_service = WarehouseVisualizationService()
