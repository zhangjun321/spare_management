"""
出库联动服务
处理出库业务逻辑，实现备件与仓库的联动
"""

from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.inbound_outbound import OutboundOrder
# from app.models.inventory_transaction_log import InventoryTransactionLog
from app.models.spare_part import SparePart
from app.models.department import Department
from sqlalchemy import and_


class OutboundLinkageService:
    """出库联动服务"""
    
    @staticmethod
    def create_outbound_order(data, user_id=None):
        """
        创建出库单
        
        Args:
            data: 出库单数据
            user_id: 用户 ID
            
        Returns:
            tuple: (outbound_order, error_message)
        """
        try:
            # 生成出库单号
            order_no = OutboundLinkageService._generate_order_no()
            
            # 检查库存是否充足
            inventory_record = InventoryRecord.query.filter_by(
                spare_part_id=data.get('spare_part_id'),
                warehouse_id=data.get('warehouse_id'),
                location_id=data.get('location_id')
            ).first()
            
            if not inventory_record:
                return None, "库存记录不存在"
            
            if inventory_record.available_quantity < data.get('quantity', 0):
                return None, f"库存不足，可用数量：{inventory_record.available_quantity}"
            
            # 创建出库单
            outbound_order = OutboundOrder(
                order_no=order_no,
                outbound_type=data.get('outbound_type', 'requisition'),
                spare_part_id=data.get('spare_part_id'),
                warehouse_id=data.get('warehouse_id'),
                location_id=data.get('location_id'),
                quantity=data.get('quantity', 0),
                shipped_quantity=0,
                department_id=data.get('department_id'),
                requester_id=data.get('requester_id'),
                unit_cost=inventory_record.unit_cost,
                approval_required=data.get('approval_required', False),
                carrier=data.get('carrier'),
                tracking_number=data.get('tracking_number'),
                recipient_name=data.get('recipient_name'),
                recipient_phone=data.get('recipient_phone'),
                recipient_address=data.get('recipient_address'),
                remark=data.get('remark'),
                created_by=user_id
            )
            
            db.session.add(outbound_order)
            db.session.flush()  # 获取 ID
            
            # 如果需要审批，设置为待审批状态
            if outbound_order.approval_required:
                outbound_order.status = 'pending_approval'
                outbound_order.approval_status = 'pending'
            else:
                outbound_order.status = 'pending'
            
            return outbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建出库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def approve_outbound(order_id, user_id=None, remark=None):
        """
        审批出库单
        
        Args:
            order_id: 出库单 ID
            user_id: 用户 ID
            remark: 审批备注
            
        Returns:
            tuple: (outbound_order, error_message)
        """
        try:
            outbound_order = OutboundOrder.query.get(order_id)
            if not outbound_order:
                return None, "出库单不存在"
            
            if outbound_order.status != 'pending_approval':
                return None, f"出库单状态不允许审批：{outbound_order.status}"
            
            # 更新审批状态
            outbound_order.approval_status = 'approved'
            outbound_order.approval_remark = remark
            outbound_order.approved_at = datetime.utcnow()
            outbound_order.approved_by = user_id
            outbound_order.status = 'pending'
            
            db.session.commit()
            
            return outbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"审批出库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def reject_outbound(order_id, user_id=None, reason=None):
        """
        拒绝出库单
        
        Args:
            order_id: 出库单 ID
            user_id: 用户 ID
            reason: 拒绝原因
            
        Returns:
            tuple: (outbound_order, error_message)
        """
        try:
            outbound_order = OutboundOrder.query.get(order_id)
            if not outbound_order:
                return None, "出库单不存在"
            
            if outbound_order.status != 'pending_approval':
                return None, f"出库单状态不允许拒绝：{outbound_order.status}"
            
            # 更新审批状态
            outbound_order.approval_status = 'rejected'
            outbound_order.approval_remark = reason
            outbound_order.approved_at = datetime.utcnow()
            outbound_order.approved_by = user_id
            outbound_order.status = 'cancelled'
            outbound_order.cancelled_at = datetime.utcnow()
            
            db.session.commit()
            
            return outbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"拒绝出库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def complete_outbound(order_id, shipped_quantity=None, user_id=None):
        """
        完成出库 - 核心联动方法
        
        执行以下操作：
        1. 更新库存记录
        2. 更新备件库存
        3. 创建库存变动日志
        4. 更新出库单状态
        
        Args:
            order_id: 出库单 ID
            shipped_quantity: 实发数量（可选，默认为出库单数量）
            user_id: 用户 ID
            
        Returns:
            tuple: (outbound_order, inventory_record, error_message)
        """
        try:
            outbound_order = OutboundOrder.query.get(order_id)
            if not outbound_order:
                return None, None, "出库单不存在"
            
            if outbound_order.status not in ['pending', 'confirmed']:
                return None, None, f"出库单状态不允许完成：{outbound_order.status}"
            
            # 检查审批状态
            if outbound_order.approval_required and outbound_order.approval_status != 'approved':
                return None, None, "出库单尚未审批通过"
            
            # 实发数量
            if shipped_quantity is None:
                shipped_quantity = outbound_order.quantity
            
            # 获取库存记录
            inventory_record = InventoryRecord.query.filter_by(
                spare_part_id=outbound_order.spare_part_id,
                warehouse_id=outbound_order.warehouse_id,
                location_id=outbound_order.location_id
            ).first()
            
            if not inventory_record:
                return None, None, "库存记录不存在"
            
            # 检查库存是否充足
            if inventory_record.available_quantity < shipped_quantity:
                return None, None, f"库存不足，可用数量：{inventory_record.available_quantity}"
            
            # 库存变动前的数量
            quantity_before = inventory_record.quantity
            
            # 更新库存记录
            inventory_record.quantity -= shipped_quantity
            inventory_record.last_outbound_time = datetime.utcnow()
            
            # 更新可用数量
            inventory_record.update_available_quantity()
            
            # 更新库存状态
            inventory_record.update_stock_status()
            
            # 更新出库单
            outbound_order.shipped_quantity = shipped_quantity
            outbound_order.status = 'completed'
            outbound_order.completed_at = datetime.utcnow()
            outbound_order.completed_by = user_id
            
            # 更新备件库存（联动）
            spare_part = SparePart.query.get(outbound_order.spare_part_id)
            if spare_part:
                spare_part.current_stock -= shipped_quantity
                spare_part.update_stock_status()  # 触发预警
                
                # 如果库存为 0，清除默认仓库和货位
                if spare_part.current_stock == 0:
                    spare_part.warehouse_id = None
                    spare_part.location_id = None
            
            # 创建库存变动日志
            transaction_log = InventoryTransactionLog.create_log(
                transaction_type='outbound',
                sub_type=outbound_order.outbound_type,
                spare_part_id=outbound_order.spare_part_id,
                warehouse_id=outbound_order.warehouse_id,
                location_id=outbound_order.location_id,
                inventory_record_id=inventory_record.id,
                quantity_before=quantity_before,
                quantity_change=-shipped_quantity,  # 负数表示减少
                quantity_after=inventory_record.quantity,
                unit_cost=outbound_order.unit_cost,
                total_amount=outbound_order.total_amount,
                stock_status_before=inventory_record.stock_status,
                stock_status_after=inventory_record.stock_status,
                reason=f"出库单 {outbound_order.order_no} 完成",
                remark=outbound_order.remark,
                order_type='outbound_order',
                order_id=outbound_order.id,
                order_no=outbound_order.order_no,
                created_by=user_id
            )
            
            db.session.add(transaction_log)
            db.session.commit()
            
            current_app.logger.info(f"出库完成：{outbound_order.order_no}, 数量：{shipped_quantity}, 库存记录 ID: {inventory_record.id}")
            
            return outbound_order, inventory_record, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"完成出库失败：{str(e)}")
            return None, None, str(e)
    
    @staticmethod
    def cancel_outbound(order_id, user_id=None, reason=None):
        """
        取消出库单
        
        Args:
            order_id: 出库单 ID
            user_id: 用户 ID
            reason: 取消原因
            
        Returns:
            tuple: (outbound_order, error_message)
        """
        try:
            outbound_order = OutboundOrder.query.get(order_id)
            if not outbound_order:
                return None, "出库单不存在"
            
            if outbound_order.status == 'completed':
                return None, "已完成的出库单不能取消"
            
            # 更新状态
            outbound_order.status = 'cancelled'
            outbound_order.cancelled_at = datetime.utcnow()
            outbound_order.remark = f"{outbound_order.remark or ''}\n取消原因：{reason}"
            
            db.session.commit()
            
            return outbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"取消出库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def _generate_order_no():
        """生成出库单号"""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:4].upper()
        return f"OUT{timestamp}{unique_id}"
