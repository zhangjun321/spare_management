"""
FIFO/FEFO 拣货推荐服务
"""

from app.models.warehouse_v3.inventory import InventoryV3
from app import db


class PickingRecommendationService:
    """拣货推荐服务类"""
    
    @staticmethod
    def recommend_inventory_fifo(part_id, quantity, warehouse_id=None):
        """
        基于 FIFO（先进先出）原则推荐拣货库存
        
        Args:
            part_id: 备件 ID
            quantity: 需要拣货的数量
            warehouse_id: 仓库 ID（可选）
            
        Returns:
            list: 推荐的库存列表
        """
        # 构建查询
        query = InventoryV3.query.filter(
            InventoryV3.part_id == part_id,
            InventoryV3.available_quantity > 0,
            InventoryV3.status == 'normal'
        )
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        # FIFO: 按入库日期升序排序（先入库的先出）
        query = query.order_by(
            InventoryV3.inbound_date.asc(),
            InventoryV3.created_at.asc()
        )
        
        available_inventory = query.all()
        
        return PickingRecommendationService._allocate_inventory(
            available_inventory, quantity
        )
    
    @staticmethod
    def recommend_inventory_fefo(part_id, quantity, warehouse_id=None):
        """
        基于 FEFO（先到期先出）原则推荐拣货库存
        
        Args:
            part_id: 备件 ID
            quantity: 需要拣货的数量
            warehouse_id: 仓库 ID（可选）
            
        Returns:
            list: 推荐的库存列表
        """
        # 构建查询
        query = InventoryV3.query.filter(
            InventoryV3.part_id == part_id,
            InventoryV3.available_quantity > 0,
            InventoryV3.status == 'normal'
        )
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        # FEFO: 按有效期升序排序（先到期的先出）
        # 没有有效期的排在最后
        query = query.order_by(
            InventoryV3.expiry_date.asc().nullslast(),
            InventoryV3.inbound_date.asc()
        )
        
        available_inventory = query.all()
        
        return PickingRecommendationService._allocate_inventory(
            available_inventory, quantity
        )
    
    @staticmethod
    def recommend_inventory_lifo(part_id, quantity, warehouse_id=None):
        """
        基于 LIFO（后进先出）原则推荐拣货库存
        
        Args:
            part_id: 备件 ID
            quantity: 需要拣货的数量
            warehouse_id: 仓库 ID（可选）
            
        Returns:
            list: 推荐的库存列表
        """
        # 构建查询
        query = InventoryV3.query.filter(
            InventoryV3.part_id == part_id,
            InventoryV3.available_quantity > 0,
            InventoryV3.status == 'normal'
        )
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        # LIFO: 按入库日期降序排序（后入库的先出）
        query = query.order_by(
            InventoryV3.inbound_date.desc(),
            InventoryV3.created_at.desc()
        )
        
        available_inventory = query.all()
        
        return PickingRecommendationService._allocate_inventory(
            available_inventory, quantity
        )
    
    @staticmethod
    def _allocate_inventory(available_inventory, quantity):
        """
        分配库存
        
        Args:
            available_inventory: 可用库存列表
            quantity: 需要分配的总数量
            
        Returns:
            list: 分配的库存列表
        """
        recommended = []
        remaining = quantity
        
        for inv in available_inventory:
            if remaining <= 0:
                break
            
            pick_qty = min(float(inv.available_quantity), remaining)
            
            recommended.append({
                'inventory_id': inv.id,
                'warehouse_id': inv.warehouse_id,
                'warehouse_name': inv.warehouse.name if inv.warehouse else None,
                'location_id': inv.location_id,
                'location_name': inv.location.name if inv.location else None,
                'part_id': inv.part_id,
                'part_code': inv.part.code if inv.part else None,
                'part_name': inv.part.name if inv.part else None,
                'quantity': pick_qty,
                'unit': inv.unit,
                'batch_no': inv.batch.batch_no if inv.batch else None,
                'inbound_date': inv.inbound_date.strftime('%Y-%m-%d') if inv.inbound_date else None,
                'expiry_date': inv.expiry_date.strftime('%Y-%m-%d') if inv.expiry_date else None,
                'expiry_days': inv.get_expiry_days(),
                'strategy_reason': 'FIFO/FEFO/LIFO 策略推荐'
            })
            
            remaining -= pick_qty
        
        # 检查是否满足需求
        total_allocated = quantity - remaining
        if total_allocated < quantity:
            # 库存不足
            return {
                'success': False,
                'recommended': recommended,
                'total_allocated': total_allocated,
                'shortage': remaining,
                'message': f'库存不足，需要{quantity}，可分配{total_allocated}'
            }
        
        return {
            'success': True,
            'recommended': recommended,
            'total_allocated': total_allocated,
            'shortage': 0,
            'message': '库存充足，可以满足需求'
        }
    
    @staticmethod
    def recommend_with_strategy(part_id, quantity, strategy='FEFO', warehouse_id=None):
        """
        根据指定策略推荐拣货库存
        
        Args:
            part_id: 备件 ID
            quantity: 需要拣货的数量
            strategy: 策略名称（FIFO/FEFO/LIFO）
            warehouse_id: 仓库 ID（可选）
            
        Returns:
            dict: 推荐结果
        """
        if strategy.upper() == 'FIFO':
            return PickingRecommendationService.recommend_inventory_fifo(
                part_id, quantity, warehouse_id
            )
        elif strategy.upper() == 'FEFO':
            return PickingRecommendationService.recommend_inventory_fefo(
                part_id, quantity, warehouse_id
            )
        elif strategy.upper() == 'LIFO':
            return PickingRecommendationService.recommend_inventory_lifo(
                part_id, quantity, warehouse_id
            )
        else:
            # 默认使用 FEFO
            return PickingRecommendationService.recommend_inventory_fefo(
                part_id, quantity, warehouse_id
            )
    
    @staticmethod
    def batch_recommend_multiple_parts(picking_list, strategy='FEFO', warehouse_id=None):
        """
        批量推荐多个备件的拣货
        
        Args:
            picking_list: 拣货清单 [{'part_id': 1, 'quantity': 10}, ...]
            strategy: 策略名称
            warehouse_id: 仓库 ID
            
        Returns:
            dict: 批量推荐结果
        """
        results = []
        total_shortage = 0
        
        for item in picking_list:
            part_id = item.get('part_id')
            quantity = item.get('quantity', 0)
            
            if not part_id or quantity <= 0:
                continue
            
            result = PickingRecommendationService.recommend_with_strategy(
                part_id=part_id,
                quantity=quantity,
                strategy=strategy,
                warehouse_id=warehouse_id
            )
            
            results.append({
                'part_id': part_id,
                'requested_quantity': quantity,
                'recommendation': result
            })
            
            if not result['success']:
                total_shortage += result.get('shortage', 0)
        
        return {
            'success': total_shortage == 0,
            'total_items': len(picking_list),
            'items': results,
            'total_shortage': total_shortage,
            'strategy': strategy
        }
