"""
优化的入库服务 - 带并发控制
"""

from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.inbound_outbound import InboundOrder
from app.models.inventory import InboundOrderItem, OperationLog
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation as StorageLocation
from app.models.spare_part import SparePart
from app.utils.concurrency import (
    TransactionManager, 
    LockManager, 
    safe_update_inventory,
    distributed_lock
)


class OptimizedInboundService:
    """优化的入库服务 - 带并发控制"""
    
    @staticmethod
    @distributed_lock('inbound_execute_{order_id}', timeout=60)
    def execute_inbound_optimized(order_id, operator_id):
        """
        优化版执行入库 - 带分布式锁
        
        Args:
            order_id: 入库单 ID
            operator_id: 操作员 ID
            
        Returns:
            dict: 执行结果
        """
        try:
            order = InboundOrder.query.get(order_id)
            if not order:
                return {'success': False, 'error': '入库单不存在'}
            
            if order.status != 'pending':
                return {'success': False, 'error': f'入库单状态不正确：{order.status}'}
            
            # 更新入库单状态
            order.status = 'completed'
            order.completed_at = datetime.utcnow()
            order.completed_by = operator_id
            
            success_items = []
            failed_items = []
            
            # 处理每个明细项
            for item in order.items:
                try:
                    # 使用安全更新库存方法
                    InboundService._process_item_with_lock(
                        item=item,
                        order=order,
                        operator_id=operator_id
                    )
                    success_items.append(item.id)
                    
                except Exception as e:
                    current_app.logger.error(f"处理入库明细项失败：{str(e)}")
                    failed_items.append({
                        'item_id': item.id,
                        'error': str(e)
                    })
            
            # 记录操作日志
            InboundService._log_operation(order, 'execute', operator_id)
            
            db.session.commit()
            
            return {
                'success': True,
                'order_id': order_id,
                'success_items': success_items,
                'failed_items': failed_items
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"执行入库失败：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _process_item_with_lock(item, order, operator_id):
        """
        处理入库明细项 - 带锁保护
        
        Args:
            item: 入库明细项
            order: 入库单
            operator_id: 操作员 ID
        """
        from app.models.inventory_v3 import InventoryV3
        
        # 获取或创建库存记录
        inventory = InventoryV3.query.filter_by(
            warehouse_id=order.warehouse_id,
            part_id=item.spare_part_id,
            batch_id=item.batch_id
        ).first()
        
        if not inventory:
            # 创建新的库存记录
            inventory = InventoryV3(
                warehouse_id=order.warehouse_id,
                part_id=item.spare_part_id,
                batch_id=item.batch_id,
                quantity=item.actual_quantity,
                available_quantity=item.actual_quantity,
                locked_quantity=0,
                unit=item.unit,
                unit_cost=item.unit_price,
                total_cost=item.total_value,
                inbound_date=order.actual_date,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version=0
            )
            db.session.add(inventory)
        else:
            # 使用乐观锁更新库存
            expected_version = inventory.version
            
            # 更新库存数量
            inventory.quantity += item.actual_quantity
            inventory.available_quantity += item.actual_quantity
            inventory.total_cost += item.total_value
            
            # 更新版本号和更新时间
            inventory.version = expected_version + 1
            inventory.updated_at = datetime.utcnow()
        
        # 创建库存移动记录
        record = InventoryRecord(
            warehouse_id=order.warehouse_id,
            part_id=item.spare_part_id,
            batch_id=item.batch_id,
            quantity=item.actual_quantity,
            operation_type='in',
            operation_time=datetime.utcnow(),
            operator_id=operator_id,
            reference_type='inbound',
            reference_id=order.id,
            remark=f'入库单 {order.order_number} 入库'
        )
        db.session.add(record)
        
        # 更新入库明细状态
        item.actual_quantity = item.actual_quantity
        item.status = 'completed'


class OptimizedOutboundService:
    """优化的出库服务 - 带并发控制"""
    
    @staticmethod
    @distributed_lock('outbound_execute_{order_id}', timeout=60)
    def execute_outbound_optimized(order_id, operator_id):
        """
        优化版执行出库 - 带分布式锁
        
        Args:
            order_id: 出库单 ID
            operator_id: 操作员 ID
            
        Returns:
            dict: 执行结果
        """
        try:
            from app.models.inbound_outbound import OutboundOrder
            
            order = OutboundOrder.query.get(order_id)
            if not order:
                return {'success': False, 'error': '出库单不存在'}
            
            if order.status != 'pending':
                return {'success': False, 'error': f'出库单状态不正确：{order.status}'}
            
            # 预检查库存是否充足
            check_result = OptimizedOutboundService._check_inventory_availability(order)
            if not check_result['success']:
                return check_result
            
            # 更新出库单状态
            order.status = 'completed'
            order.completed_at = datetime.utcnow()
            order.completed_by = operator_id
            
            success_items = []
            failed_items = []
            
            # 处理每个明细项
            for item in order.items:
                try:
                    # 使用安全更新库存方法
                    OptimizedOutboundService._process_item_with_lock(
                        item=item,
                        order=order,
                        operator_id=operator_id
                    )
                    success_items.append(item.id)
                    
                except Exception as e:
                    current_app.logger.error(f"处理出库明细项失败：{str(e)}")
                    failed_items.append({
                        'item_id': item.id,
                        'error': str(e)
                    })
            
            # 记录操作日志
            OutboundService._log_operation(order, 'execute', operator_id)
            
            db.session.commit()
            
            return {
                'success': True,
                'order_id': order_id,
                'success_items': success_items,
                'failed_items': failed_items
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"执行出库失败：{str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _check_inventory_availability(order):
        """
        检查库存可用性
        
        Args:
            order: 出库单对象
            
        Returns:
            dict: 检查结果
        """
        from app.models.inventory_v3 import InventoryV3
        
        for item in order.items:
            inventory = InventoryV3.query.filter_by(
                warehouse_id=order.warehouse_id,
                part_id=item.spare_part_id
            ).first()
            
            if not inventory:
                return {
                    'success': False,
                    'error': f'备件 {item.spare_part.name} 库存不足'
                }
            
            if inventory.available_quantity < item.planned_quantity:
                return {
                    'success': False,
                    'error': f'备件 {item.spare_part.name} 可用库存不足'
                }
        
        return {'success': True}
    
    @staticmethod
    def _process_item_with_lock(item, order, operator_id):
        """
        处理出库明细项 - 带锁保护
        
        Args:
            item: 出库明细项
            order: 出库单
            operator_id: 操作员 ID
        """
        from app.models.inventory_v3 import InventoryV3
        
        # 获取库存记录
        inventory = InventoryV3.query.filter_by(
            warehouse_id=order.warehouse_id,
            part_id=item.spare_part_id
        ).first()
        
        if not inventory:
            raise Exception('库存记录不存在')
        
        # 使用乐观锁更新库存
        expected_version = inventory.version
        
        # 检查可用数量
        if inventory.available_quantity < item.actual_quantity:
            raise Exception('可用库存不足')
        
        # 更新库存数量
        inventory.quantity -= item.actual_quantity
        inventory.available_quantity -= item.actual_quantity
        
        # 更新版本号和更新时间
        inventory.version = expected_version + 1
        inventory.updated_at = datetime.utcnow()
        
        # 创建库存移动记录
        record = InventoryRecord(
            warehouse_id=order.warehouse_id,
            part_id=item.spare_part_id,
            quantity=-item.actual_quantity,
            operation_type='out',
            operation_time=datetime.utcnow(),
            operator_id=operator_id,
            reference_type='outbound',
            reference_id=order.id,
            remark=f'出库单 {order.order_number} 出库'
        )
        db.session.add(record)
        
        # 更新出库明细状态
        item.status = 'completed'
