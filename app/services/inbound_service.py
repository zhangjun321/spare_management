"""
入库管理服务
包含：单条入库、批量入库、AI 库位推荐
"""

import json
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.inventory_record import InventoryRecord
from app.models.inbound_outbound import InboundOrder
from app.models.inventory import InboundOrderItem, OperationLog
from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation as StorageLocation
from app.models.spare_part import SparePart
from app.services.intelligent_warehouse_service import intelligent_warehouse_service


class InboundService:
    """入库管理服务类"""
    
    @staticmethod
    def create_order(warehouse_id, spare_part_ids, quantities, **kwargs):
        """
        创建入库单
        
        Args:
            warehouse_id: 仓库 ID
            spare_part_ids: 备件 ID 列表
            quantities: 数量列表
            **kwargs: 其他参数（type, supplier_id, batch_number 等）
        
        Returns:
            InboundOrder: 创建的入库单
        """
        # 生成入库单号
        order_number = InboundService._generate_order_number()
        
        # 创建入库单
        order = InboundOrder(
            order_number=order_number,
            warehouse_id=warehouse_id,
            type=kwargs.get('type', 'purchase'),
            supplier_id=kwargs.get('supplier_id'),
            created_by=kwargs.get('created_by'),
            remark=kwargs.get('remark')
        )
        
        db.session.add(order)
        db.session.flush()  # 获取 order.id
        
        # 创建入库单明细
        for spare_part_id, quantity in zip(spare_part_ids, quantities):
            item = InboundOrderItem(
                order_id=order.id,
                spare_part_id=spare_part_id,
                planned_quantity=quantity,
                actual_quantity=quantity,
                batch_number=kwargs.get('batch_number'),
                unit_price=kwargs.get('unit_price', 0.0)
            )
            item.total_value = item.actual_quantity * item.unit_price
            db.session.add(item)
        
        # 记录操作日志
        InboundService._log_operation(order, 'create', kwargs.get('operator_id'))
        
        db.session.commit()
        return order
    
    @staticmethod
    def ai_recommend_locations(order_id):
        """
        AI 推荐库位
        
        Args:
            order_id: 入库单 ID
        
        Returns:
            dict: AI 推荐结果
        """
        order = InboundOrder.query.get_or_404(order_id)
        warehouse = Warehouse.query.get(order.warehouse_id)
        
        if not warehouse:
            return {'success': False, 'error': '仓库不存在'}
        
        # 获取入库单明细
        items = order.items.all()
        spare_parts = [item.spare_part for item in items]
        
        # 调用 AI 服务分析备件数据
        ai_result = intelligent_warehouse_service.analyze_spare_parts_data(
            warehouse_id=order.warehouse_id
        )
        
        if not ai_result.get('success'):
            return {'success': False, 'error': ai_result.get('error')}
        
        # 为每个备件推荐库位
        recommendations = []
        for item in items:
            spare_part = item.spare_part
            
            # AI 分析备件特性
            recommendation = InboundService._analyze_part_and_recommend(
                spare_part=spare_part,
                quantity=item.actual_quantity,
                warehouse=warehouse,
                ai_analysis=ai_result
            )
            
            recommendations.append({
                'item_id': item.id,
                'spare_part_id': spare_part.id,
                'recommended_location_id': recommendation.get('location_id'),
                'reason': recommendation.get('reason'),
                'ai_recommended': True
            })
            
            # 更新入库单明细
            if recommendation.get('location_id'):
                item.location_id = recommendation['location_id']
                item.ai_recommended_location = True
        
        # 更新 AI 推荐信息
        order.ai_recommended = True
        order.ai_recommendation_data = {
            'analysis_result': ai_result,
            'recommendations': recommendations
        }
        
        db.session.commit()
        
        return {
            'success': True,
            'order_id': order_id,
            'recommendations': recommendations
        }
    
    @staticmethod
    def _analyze_part_and_recommend(spare_part, quantity, warehouse, ai_analysis):
        """
        分析备件特性并推荐库位
        
        Args:
            spare_part: 备件对象
            quantity: 数量
            warehouse: 仓库对象
            ai_analysis: AI 分析结果
        
        Returns:
            dict: 推荐库位信息
        """
        # 1. 分析备件物理特性
        storage_requirement = spare_part.storage_requirement or ''
        weight = spare_part.weight or 0
        dimensions = spare_part.dimensions or {}
        
        # 2. 分析 ABC 分类
        abc_class = spare_part.abc_class or 'C'
        
        # 3. 查找合适的库区
        suitable_zones = []
        for zone in warehouse.zones.filter_by(is_active=True).all():
            # 根据存储要求筛选库区
            if '冷藏' in storage_requirement and zone.type != 'cold':
                continue
            if '危险品' in storage_requirement and zone.type != 'hazardous':
                continue
            
            suitable_zones.append(zone)
        
        if not suitable_zones:
            return {'location_id': None, 'reason': '未找到合适的库区'}
        
        # 4. 在库区中查找可用库位
        for zone in suitable_zones:
            for rack in zone.racks.all():
                for location in rack.locations.filter_by(is_occupied=False).all():
                    # 检查库位承重
                    if weight > (location.max_weight or 0):
                        continue
                    
                    # ABC 分类优化：A 类放在靠近出入口的位置
                    if abc_class == 'A' and zone.type not in ['A', 'fast-moving']:
                        continue
                    
                    # 找到合适的库位
                    return {
                        'location_id': location.id,
                        'reason': f'基于备件特性（{abc_class}类，重量{weight}kg）和库位条件推荐'
                    }
        
        # 5. 如果没有完全匹配的库位，返回第一个可用库位
        for zone in suitable_zones:
            for rack in zone.racks.all():
                for location in rack.locations.filter_by(is_occupied=False).first():
                    return {
                        'location_id': location.id,
                        'reason': '默认推荐可用库位'
                    }
        
        return {'location_id': None, 'reason': '没有可用库位'}
    
    @staticmethod
    def execute_inbound(order_id, operator_id=None):
        """
        执行入库操作
        
        Args:
            order_id: 入库单 ID
            operator_id: 操作员 ID
        
        Returns:
            dict: 执行结果
        """
        order = InboundOrder.query.get_or_404(order_id)
        
        if order.status != 'pending':
            return {'success': False, 'error': f'入库单状态不正确：{order.status}'}
        
        # 更新状态
        order.status = 'processing'
        db.session.flush()
        
        success_items = []
        failed_items = []
        
        # 处理每个入库明细
        for item in order.items.all():
            try:
                # 检查是否已分配库位
                if not item.location_id:
                    failed_items.append({
                        'item_id': item.id,
                        'error': '未分配库位'
                    })
                    continue
                
                # 查找或创建库存记录
                inventory = InventoryRecord.query.filter_by(
                    warehouse_id=order.warehouse_id,
                    location_id=item.location_id,
                    spare_part_id=item.spare_part_id,
                    batch_number=item.batch_number
                ).first()
                
                if inventory:
                    # 更新现有库存
                    inventory.quantity += item.actual_quantity
                    inventory.total_value += item.total_value
                else:
                    # 创建新库存记录
                    inventory = InventoryRecord(
                        warehouse_id=order.warehouse_id,
                        location_id=item.location_id,
                        spare_part_id=item.spare_part_id,
                        batch_number=item.batch_number,
                        quantity=item.actual_quantity,
                        initial_quantity=item.actual_quantity,
                        unit_price=item.unit_price,
                        total_value=item.total_value,
                        entry_date=datetime.utcnow(),
                        created_by=operator_id
                    )
                    db.session.add(inventory)
                
                # 更新库位状态
                location = StorageLocation.query.get(item.location_id)
                if location:
                    location.is_occupied = True
                
                # 更新明细状态
                item.received_quantity = item.actual_quantity
                item.status = 'completed'
                
                success_items.append(item.id)
                
            except Exception as e:
                current_app.logger.error(f'入库失败：{str(e)}')
                failed_items.append({
                    'item_id': item.id,
                    'error': str(e)
                })
        
        # 更新入库单状态
        if failed_items:
            order.status = 'partial' if success_items else 'failed'
        else:
            order.status = 'completed'
            order.completed_at = datetime.utcnow()
            order.completed_by = operator_id
        
        # 记录操作日志
        InboundService._log_operation(
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
    def rollback_inbound(order_id, operator_id=None):
        """
        撤销入库操作
        
        Args:
            order_id: 入库单 ID
            operator_id: 操作员 ID
        
        Returns:
            dict: 撤销结果
        """
        order = InboundOrder.query.get_or_404(order_id)
        
        if order.status not in ['completed', 'partial']:
            return {'success': False, 'error': '入库单尚未完成，无法撤销'}
        
        # 记录操作前数据
        before_data = {
            'order_status': order.status,
            'items': [item.to_dict() for item in order.items.all()]
        }
        
        # 扣减库存
        for item in order.items.all():
            if not item.location_id:
                continue
            
            # 查找库存记录
            inventory = InventoryRecord.query.filter_by(
                warehouse_id=order.warehouse_id,
                location_id=item.location_id,
                spare_part_id=item.spare_part_id,
                batch_number=item.batch_number
            ).first()
            
            if inventory:
                # 扣减库存
                inventory.quantity -= item.actual_quantity
                inventory.total_value -= item.total_value
                
                # 如果库存为 0，删除记录并释放库位
                if inventory.quantity <= 0:
                    location = StorageLocation.query.get(item.location_id)
                    if location:
                        location.is_occupied = False
                    db.session.delete(inventory)
        
        # 更新入库单状态
        order.status = 'cancelled'
        
        # 记录操作日志
        InboundService._log_operation(
            order,
            'rollback',
            operator_id,
            before_data=before_data,
            after_data={'order_status': 'cancelled'}
        )
        
        db.session.commit()
        return {'success': True, 'order_id': order_id}
    
    @staticmethod
    def _generate_order_number():
        """生成入库单号"""
        from datetime import datetime
        prefix = 'IN'
        date_str = datetime.utcnow().strftime('%Y%m%d')
        
        # 获取今日最后一个单号
        last_order = InboundOrder.query.filter(
            InboundOrder.order_number.like(f'{prefix}{date_str}%')
        ).order_by(InboundOrder.id.desc()).first()
        
        if last_order:
            seq = int(last_order.order_number[-4:]) + 1
        else:
            seq = 1
        
        return f'{prefix}{date_str}{seq:04d}'
    
    @staticmethod
    def _log_operation(order, action, operator_id, **kwargs):
        """记录操作日志"""
        from flask import request
        
        log = OperationLog(
            order_type='inbound',
            order_id=order.id,
            action=action,
            operator_id=operator_id,
            operator_name=operator_id.user.real_name if operator_id and operator_id.user else 'Unknown',
            ip_address=request.remote_addr if request else '',
            details=kwargs.get('details'),
            before_data=kwargs.get('before_data'),
            after_data=kwargs.get('after_data')
        )
        db.session.add(log)


# 全局服务实例
inbound_service = InboundService()
