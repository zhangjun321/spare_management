"""
出库管理服务
包含：多种出库策略、库存校验、出库执行
"""

from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.inbound_outbound import OutboundOrder
from app.models.inventory import OutboundOrderItem, OutboundSourceLocation, OperationLog
from app.models.warehouse import Warehouse


def _get_operator_name(operator_id):
    """根据 operator_id 获取操作人姓名"""
    if not operator_id:
        return 'Unknown'
    try:
        from app.models.user import User
        user = User.query.get(operator_id)
        return user.real_name or user.username if user else 'Unknown'
    except Exception:
        return 'Unknown'


class OutboundService:
    """出库管理服务类"""
    
    @staticmethod
    def create_order(warehouse_id, spare_part_items, **kwargs):
        """
        创建出库单
        
        Args:
            warehouse_id: 仓库 ID
            spare_part_items: 备件项列表 [(spare_part_id, quantity), ...]
            **kwargs: 其他参数（type, strategy, requester_id, department, purpose 等）
        
        Returns:
            OutboundOrder: 创建的出库单
        """
        # 生成出库单号
        order_number = OutboundService._generate_order_number()
        
        # 创建出库单
        order = OutboundOrder(
            order_no=order_number,
            warehouse_id=warehouse_id,
            outbound_type=kwargs.get('outbound_type', kwargs.get('type', 'requisition')),
            strategy=kwargs.get('strategy', 'fifo'),
            requester_id=kwargs.get('requester_id'),
            department=kwargs.get('department'),
            purpose=kwargs.get('purpose'),
            created_by=kwargs.get('created_by'),
            remark=kwargs.get('remark')
        )
        
        db.session.add(order)
        db.session.flush()
        
        # 创建出库单明细
        for spare_part_id, quantity in spare_part_items:
            item = OutboundOrderItem(
                order_id=order.id,
                spare_part_id=spare_part_id,
                requested_quantity=quantity,
                approved_quantity=quantity
            )
            db.session.add(item)
        
        # 记录操作日志
        OutboundService._log_operation(order, 'create', kwargs.get('created_by'))
        
        db.session.commit()
        return order
    
    @staticmethod
    def allocate_locations(order_id):
        """
        分配出库库位（根据策略）
        
        Args:
            order_id: 出库单 ID
        
        Returns:
            dict: 分配结果
        """
        order = OutboundOrder.query.get_or_404(order_id)
        
        if order.status != 'pending':
            return {'success': False, 'error': f'出库单状态不正确：{order.status}'}
        
        allocation_results = []
        
        # 处理每个出库明细
        for item in order.items.all():
            # 根据策略分配库位
            if order.strategy == 'fifo':
                allocated = OutboundService._allocate_fifo(
                    order.warehouse_id,
                    item.spare_part_id,
                    item.approved_quantity
                )
            elif order.strategy == 'lifo':
                allocated = OutboundService._allocate_lifo(
                    order.warehouse_id,
                    item.spare_part_id,
                    item.approved_quantity
                )
            elif order.strategy == 'fefo':
                allocated = OutboundService._allocate_fefo(
                    order.warehouse_id,
                    item.spare_part_id,
                    item.approved_quantity
                )
            else:  # manual
                allocated = []
            
            # 创建来源库位记录
            for alloc in allocated:
                source_location = OutboundSourceLocation(
                    order_item_id=item.id,
                    inventory_record_id=alloc['inventory_record_id'],
                    location_id=alloc['location_id'],
                    quantity=alloc['quantity']
                )
                db.session.add(source_location)
            
            allocation_results.append({
                'item_id': item.id,
                'spare_part_id': item.spare_part_id,
                'allocated': allocated,
                'total_quantity': sum(a['quantity'] for a in allocated)
            })
        
        db.session.commit()
        
        return {
            'success': True,
            'order_id': order_id,
            'allocations': allocation_results
        }
    
    @staticmethod
    def _allocate_fifo(warehouse_id, spare_part_id, quantity):
        """
        FIFO 策略：按入库时间正序分配
        
        Args:
            warehouse_id: 仓库 ID
            spare_part_id: 备件 ID
            quantity: 需要出库的数量
        
        Returns:
            list: 分配的库位列表 [{inventory_record_id, location_id, quantity}, ...]
        """
        # 查询库存记录，按入库时间正序
        inventory_records = InventoryRecord.query.filter(
            InventoryRecord.warehouse_id == warehouse_id,
            InventoryRecord.spare_part_id == spare_part_id,
            InventoryRecord.stock_status != 'out'
        ).order_by(InventoryRecord.last_inbound_time.asc()).all()
        
        return OutboundService._allocate_from_records(inventory_records, quantity)
    
    @staticmethod
    def _allocate_lifo(warehouse_id, spare_part_id, quantity):
        """
        LIFO 策略：按入库时间倒序分配
        """
        inventory_records = InventoryRecord.query.filter(
            InventoryRecord.warehouse_id == warehouse_id,
            InventoryRecord.spare_part_id == spare_part_id,
            InventoryRecord.stock_status != 'out'
        ).order_by(InventoryRecord.last_inbound_time.desc()).all()
        
        return OutboundService._allocate_from_records(inventory_records, quantity)
    
    @staticmethod
    def _allocate_fefo(warehouse_id, spare_part_id, quantity):
        """
        FEFO 策略：按有效期正序分配（先到期的先出）
        """
        # 有有效期的按有效期排序，没有的按入库时间
        inventory_records = InventoryRecord.query.filter(
            InventoryRecord.warehouse_id == warehouse_id,
            InventoryRecord.spare_part_id == spare_part_id,
            InventoryRecord.stock_status != 'out'
        ).order_by(
            InventoryRecord.expiry_date.asc().nullslast(),
            InventoryRecord.last_inbound_time.asc()
        ).all()
        
        return OutboundService._allocate_from_records(inventory_records, quantity)
    
    @staticmethod
    def _allocate_from_records(inventory_records, quantity):
        """
        从库存记录中分配数量
        
        Args:
            inventory_records: 库存记录列表
            quantity: 需要分配的总数量
        
        Returns:
            list: 分配结果
        """
        allocated = []
        remaining = quantity
        
        for record in inventory_records:
            if remaining <= 0:
                break
            
            # 计算可用数量（available_quantity 为数据库列：quantity - locked_quantity）
            available = record.available_quantity if record.available_quantity is not None else (record.quantity - record.locked_quantity)
            if available <= 0:
                continue
            
            # 分配数量
            allocate_qty = min(remaining, available)
            allocated.append({
                'inventory_record_id': record.id,
                'location_id': record.location_id,
                'quantity': allocate_qty
            })
            
            remaining -= allocate_qty
        
        if remaining > 0:
            current_app.logger.warning(f'库存不足，缺少 {remaining} 个')
        
        return allocated
    
    @staticmethod
    def execute_outbound(order_id, operator_id=None):
        """
        执行出库操作
        
        Args:
            order_id: 出库单 ID
            operator_id: 操作员 ID
        
        Returns:
            dict: 执行结果
        """
        order = OutboundOrder.query.get_or_404(order_id)
        
        if order.status not in ['pending', 'approved']:
            return {'success': False, 'error': f'出库单状态不正确：{order.status}'}
        
        # 更新状态
        order.status = 'processing'
        db.session.flush()
        
        success_items = []
        failed_items = []
        
        # 处理每个出库明细
        for item in order.items.all():
            try:
                # 获取来源库位
                source_locations = item.source_locations.all()
                
                if not source_locations:
                    failed_items.append({
                        'item_id': item.id,
                        'error': '未分配库位'
                    })
                    continue
                
                total_issued = 0
                
                # 从各个库位扣减库存
                for source in source_locations:
                    inventory = InventoryRecord.query.get(source.inventory_record_id)
                    
                    if not inventory:
                        raise Exception(f'库存记录不存在：{source.inventory_record_id}')
                    
                    if inventory.available_quantity() < source.quantity:
                        raise Exception(f'库存不足：需要{source.quantity}，可用{inventory.available_quantity()}')
                    
                    # 扣减库存
                    inventory.quantity -= source.quantity
                    inventory.total_value = (inventory.quantity * inventory.unit_cost) if inventory.unit_cost else None
                    inventory.last_outbound_time = datetime.utcnow()
                    inventory.update_available_quantity()
                    inventory.update_stock_status()
                    
                    # 如果库存为 0，标记状态而非删除（保留历史记录以支持回滚）
                    if inventory.quantity <= 0:
                        inventory.quantity = 0
                        inventory.available_quantity = 0
                        inventory.stock_status = 'out'
                        location = inventory.warehouse_location
                        if location:
                            location.status = 'available'
                    
                    total_issued += source.quantity
                
                # 更新明细状态
                item.issued_quantity = total_issued
                item.status = 'issued'
                
                if total_issued >= item.approved_quantity:
                    success_items.append(item.id)
                else:
                    failed_items.append({
                        'item_id': item.id,
                        'error': f'出库数量不足：应出{item.approved_quantity}，实出{total_issued}'
                    })
                
            except Exception as e:
                current_app.logger.error(f'出库失败：{str(e)}')
                failed_items.append({
                    'item_id': item.id,
                    'error': str(e)
                })
        
        # 更新出库单状态
        if failed_items:
            order.status = 'partial' if success_items else 'failed'
        else:
            order.status = 'completed'
            order.completed_at = datetime.utcnow()
            order.completed_by = operator_id
        
        # 记录操作日志
        OutboundService._log_operation(
            order,
            'execute',
            operator_id,
            details={'success_items': success_items, 'failed_items': failed_items}
        )
        
        db.session.commit()
        
        return {
            'success': len(success_items) > 0,
            'order_id': order_id,
            'success_items': success_items,
            'failed_items': failed_items,
            'status': order.status
        }
    
    @staticmethod
    def rollback_outbound(order_id, operator_id=None):
        """
        撤销出库操作
        
        Args:
            order_id: 出库单 ID
            operator_id: 操作员 ID
        
        Returns:
            dict: 撤销结果
        """
        order = OutboundOrder.query.get_or_404(order_id)
        
        if order.status not in ['completed', 'partial']:
            return {'success': False, 'error': '出库单尚未完成，无法撤销'}
        
        # 记录操作前数据
        before_data = {
            'order_status': order.status,
            'items': [item.to_dict() for item in order.items.all()]
        }
        
        # 恢复库存
        for item in order.items.all():
            for source in item.source_locations.all():
                inventory = InventoryRecord.query.get(source.inventory_record_id)
                
                if not inventory:
                    # 库存记录已被删除，需要重新创建
                    # 这里简化处理，实际应该从 source_locations 获取完整信息
                    continue
                
                # 恢复库存
                inventory.quantity += source.quantity
                inventory.total_value += (source.quantity * inventory.unit_price)
        
        # 更新出库单状态
        order.status = 'cancelled'
        
        # 记录操作日志
        OutboundService._log_operation(
            order,
            'rollback',
            operator_id,
            before_data=before_data,
            after_data={'order_status': 'cancelled'}
        )
        
        db.session.commit()
        
        return {'success': True, 'order_id': order_id}
    
    @staticmethod
    def check_inventory(warehouse_id, spare_part_items):
        """
        检查库存是否充足
        
        Args:
            warehouse_id: 仓库 ID
            spare_part_items: 备件项列表 [(spare_part_id, quantity), ...]
        
        Returns:
            dict: 检查结果 {success, details: [{spare_part_id, requested, available, sufficient}]}
        """
        details = []
        all_sufficient = True
        
        for spare_part_id, quantity in spare_part_items:
            # 查询总可用库存
            inventory_records = InventoryRecord.query.filter(
                InventoryRecord.warehouse_id == warehouse_id,
                InventoryRecord.spare_part_id == spare_part_id,
                InventoryRecord.stock_status != 'out'
            ).all()
            
            available = sum(
                (r.available_quantity if r.available_quantity is not None else (r.quantity - r.locked_quantity))
                for r in inventory_records
            )
            sufficient = available >= quantity
            
            if not sufficient:
                all_sufficient = False
            
            details.append({
                'spare_part_id': spare_part_id,
                'requested': quantity,
                'available': available,
                'sufficient': sufficient
            })
        
        return {
            'success': all_sufficient,
            'details': details
        }
    
    @staticmethod
    def _generate_order_number():
        """生成出库单号"""
        prefix = 'OUT'
        date_str = datetime.utcnow().strftime('%Y%m%d')
        
        # 获取今日最后一个单号
        last_order = OutboundOrder.query.filter(
            OutboundOrder.order_no.like(f'{prefix}{date_str}%')
        ).order_by(OutboundOrder.id.desc()).first()
        
        if last_order:
            seq = int(last_order.order_no[-4:]) + 1
        else:
            seq = 1
        
        return f'{prefix}{date_str}{seq:04d}'
    
    @staticmethod
    def _log_operation(order, action, operator_id, **kwargs):
        """记录操作日志"""
        from flask import request
        
        log = OperationLog(
            order_type='outbound',
            order_id=order.id,
            action=action,
            operator_id=operator_id,
            operator_name=_get_operator_name(operator_id),
            ip_address=request.remote_addr if request else '',
            details=kwargs.get('details'),
            before_data=kwargs.get('before_data'),
            after_data=kwargs.get('after_data')
        )
        db.session.add(log)


# 全局服务实例
outbound_service = OutboundService()
