"""
入库联动服务
处理入库业务逻辑，实现备件与仓库的联动
"""

from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.inbound_outbound import InboundOrder
# from app.models.inventory_transaction_log import InventoryTransactionLog
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation
from app.models.batch import Batch
from sqlalchemy import and_


class InboundLinkageService:
    """入库联动服务"""
    
    @staticmethod
    def create_inbound_order(data, user_id=None):
        """
        创建入库单
        
        Args:
            data: 入库单数据
            user_id: 用户 ID
            
        Returns:
            tuple: (inbound_order, error_message)
        """
        try:
            # 生成入库单号
            order_no = InboundLinkageService._generate_order_no()
            
            # 创建入库单
            inbound_order = InboundOrder(
                order_no=order_no,
                inbound_type=data.get('inbound_type', 'purchase'),
                spare_part_id=data.get('spare_part_id'),
                warehouse_id=data.get('warehouse_id'),
                location_id=data.get('location_id'),
                quantity=data.get('quantity', 0),
                received_quantity=0,
                unit_price=data.get('unit_price'),
                total_amount=data.get('total_amount'),
                batch_number=data.get('batch_number'),
                production_date=datetime.strptime(data['production_date'], '%Y-%m-%d').date() if data.get('production_date') else None,
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
                supplier_id=data.get('supplier_id'),
                quality_check=data.get('quality_check', False),
                carrier=data.get('carrier'),
                tracking_number=data.get('tracking_number'),
                remark=data.get('remark'),
                created_by=user_id
            )
            
            db.session.add(inbound_order)
            db.session.flush()  # 获取 ID
            
            return inbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建入库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def confirm_inbound(order_id, user_id=None):
        """
        确认入库单
        
        Args:
            order_id: 入库单 ID
            user_id: 用户 ID
            
        Returns:
            tuple: (inbound_order, error_message)
        """
        try:
            inbound_order = InboundOrder.query.get(order_id)
            if not inbound_order:
                return None, "入库单不存在"
            
            if inbound_order.status != 'pending':
                return None, f"入库单状态不允许确认：{inbound_order.status}"
            
            # 更新状态
            inbound_order.status = 'confirmed'
            inbound_order.confirmed_at = datetime.utcnow()
            inbound_order.confirmed_by = user_id
            
            db.session.commit()
            
            return inbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"确认入库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def complete_inbound(order_id, received_quantity=None, user_id=None):
        """
        完成入库 - 核心联动方法
        
        执行以下操作：
        1. 更新或创建库存记录
        2. 更新备件库存
        3. 创建库存变动日志
        4. 更新入库单状态
        
        Args:
            order_id: 入库单 ID
            received_quantity: 实收数量（可选，默认为入库单数量）
            user_id: 用户 ID
            
        Returns:
            tuple: (inbound_order, inventory_record, error_message)
        """
        try:
            inbound_order = InboundOrder.query.get(order_id)
            if not inbound_order:
                return None, None, "入库单不存在"
            
            if inbound_order.status not in ['pending', 'confirmed']:
                return None, None, f"入库单状态不允许完成：{inbound_order.status}"
            
            # 实收数量
            if received_quantity is None:
                received_quantity = inbound_order.quantity
            
            # 检查库存记录是否存在
            inventory_record = InventoryRecord.query.filter_by(
                spare_part_id=inbound_order.spare_part_id,
                warehouse_id=inbound_order.warehouse_id,
                location_id=inbound_order.location_id
            ).first()
            
            # 库存变动前的数量
            quantity_before = inventory_record.quantity if inventory_record else 0
            
            if inventory_record:
                # 更新现有库存记录
                inventory_record.quantity += received_quantity
                inventory_record.last_inbound_time = datetime.utcnow()
            else:
                # 创建新的库存记录
                spare_part = SparePart.query.get(inbound_order.spare_part_id)
                warehouse = Warehouse.query.get(inbound_order.warehouse_id)
                
                inventory_record = InventoryRecord(
                    spare_part_id=inbound_order.spare_part_id,
                    warehouse_id=inbound_order.warehouse_id,
                    location_id=inbound_order.location_id,
                    quantity=received_quantity,
                    batch_number=inbound_order.batch_number,
                    production_date=inbound_order.production_date,
                    expiry_date=inbound_order.expiry_date,
                    unit_cost=inbound_order.unit_price,
                    total_amount=inbound_order.total_amount,
                    min_stock=spare_part.min_stock if spare_part else 0,
                    max_stock=spare_part.max_stock if spare_part else None,
                    safety_stock=spare_part.safety_stock if spare_part else 0,
                    last_inbound_time=datetime.utcnow(),
                    created_by=user_id
                )
                
                db.session.add(inventory_record)
                db.session.flush()
            
            # 更新可用数量
            inventory_record.update_available_quantity()
            
            # 更新库存状态
            inventory_record.update_stock_status()
            
            # 更新入库单
            inbound_order.received_quantity = received_quantity
            inbound_order.status = 'completed'
            inbound_order.completed_at = datetime.utcnow()
            inbound_order.completed_by = user_id
            inbound_order.inventory_record_id = inventory_record.id
            
            # 更新备件库存（联动）
            spare_part = SparePart.query.get(inbound_order.spare_part_id)
            if spare_part:
                old_stock = spare_part.current_stock
                spare_part.current_stock += received_quantity
                spare_part.update_stock_status()  # 触发预警
                
                # 如果是首次入库，更新默认仓库和货位
                if old_stock == 0:
                    spare_part.warehouse_id = inbound_order.warehouse_id
                    spare_part.location_id = inbound_order.location_id
                
                # 更新最后采购信息
                if inbound_order.inbound_type == 'purchase':
                    spare_part.last_purchase_date = datetime.utcnow()
                    if inbound_order.unit_price:
                        spare_part.last_purchase_price = inbound_order.unit_price
            
            # 创建库存变动日志
            transaction_log = InventoryTransactionLog.create_log(
                transaction_type='inbound',
                sub_type=inbound_order.inbound_type,
                spare_part_id=inbound_order.spare_part_id,
                warehouse_id=inbound_order.warehouse_id,
                location_id=inbound_order.location_id,
                inventory_record_id=inventory_record.id,
                quantity_before=quantity_before,
                quantity_change=received_quantity,
                quantity_after=inventory_record.quantity,
                unit_cost=inbound_order.unit_price,
                total_amount=inbound_order.total_amount,
                batch_number=inbound_order.batch_number,
                stock_status_before=inventory_record.stock_status,
                stock_status_after=inventory_record.stock_status,
                reason=f"入库单 {inbound_order.order_no} 完成",
                remark=inbound_order.remark,
                order_type='inbound_order',
                order_id=inbound_order.id,
                order_no=inbound_order.order_no,
                created_by=user_id
            )
            
            db.session.add(transaction_log)
            db.session.commit()
            
            current_app.logger.info(f"入库完成：{inbound_order.order_no}, 数量：{received_quantity}, 库存记录 ID: {inventory_record.id}")
            
            return inbound_order, inventory_record, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"完成入库失败：{str(e)}")
            return None, None, str(e)
    
    @staticmethod
    def cancel_inbound(order_id, user_id=None, reason=None):
        """
        取消入库单
        
        Args:
            order_id: 入库单 ID
            user_id: 用户 ID
            reason: 取消原因
            
        Returns:
            tuple: (inbound_order, error_message)
        """
        try:
            inbound_order = InboundOrder.query.get(order_id)
            if not inbound_order:
                return None, "入库单不存在"
            
            if inbound_order.status == 'completed':
                return None, "已完成的入库单不能取消"
            
            # 更新状态
            inbound_order.status = 'cancelled'
            inbound_order.cancelled_at = datetime.utcnow()
            inbound_order.remark = f"{inbound_order.remark or ''}\n取消原因：{reason}"
            
            db.session.commit()
            
            return inbound_order, None
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"取消入库单失败：{str(e)}")
            return None, str(e)
    
    @staticmethod
    def _generate_order_no():
        """生成入库单号"""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:4].upper()
        return f"IN{timestamp}{unique_id}"
    
    @staticmethod
    def get_inventory_record(spare_part_id, warehouse_id, location_id=None):
        """
        获取库存记录
        
        Args:
            spare_part_id: 备件 ID
            warehouse_id: 仓库 ID
            location_id: 货位 ID（可选）
            
        Returns:
            InventoryRecord or None
        """
        query = InventoryRecord.query.filter_by(
            spare_part_id=spare_part_id,
            warehouse_id=warehouse_id
        )
        
        if location_id:
            query = query.filter_by(location_id=location_id)
        
        return query.first()
