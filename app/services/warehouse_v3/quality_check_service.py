"""
质检管理服务
提供质检单创建、质检数据录入、结果处理等功能
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from app import db
from app.models.warehouse_v3.quality_check import QualityCheck, QualityCheckItem
from app.models.warehouse_v3.inbound import InboundOrderV3, InboundOrderItemV3
from app.models.warehouse_v3.inventory import InventoryV3
from app.models.warehouse_v3.warehouse import WarehouseV3
import logging

logger = logging.getLogger(__name__)


class QualityCheckService:
    """质检服务类"""
    
    @staticmethod
    def create_quality_check(data: Dict) -> QualityCheck:
        """
        创建质检单
        
        Args:
            data: 质检单数据
            
        Returns:
            质检单对象
        """
        # 获取入库单
        inbound_order = InboundOrderV3.query.get(data['inbound_order_id'])
        if not inbound_order:
            raise ValueError('入库单不存在')
        
        # 检查是否已存在质检单
        existing = QualityCheck.query.filter_by(
            inbound_order_id=data['inbound_order_id']
        ).first()
        if existing:
            raise ValueError('该入库单已创建质检单')
        
        # 生成质检单号
        check_no = QualityCheck.generate_check_no()
        
        # 创建质检单
        quality_check = QualityCheck(
            check_no=check_no,
            inbound_order_id=data['inbound_order_id'],
            check_type=data.get('check_type', 'inbound'),
            inspection_type=data.get('inspection_type', 'sampling'),
            check_method=data.get('check_method', 'sampling'),
            sample_ratio=data.get('sample_ratio'),
            sample_size=data.get('sample_size'),
            status='pending',
            created_by=data.get('created_by'),
            remark=data.get('remark')
        )
        
        db.session.add(quality_check)
        db.session.flush()  # 获取 ID
        
        # 自动生成质检项目
        QualityCheckService.generate_check_items(quality_check, inbound_order)
        
        db.session.commit()
        
        logger.info(f"创建质检单：{check_no}")
        return quality_check
    
    @staticmethod
    def generate_check_items(quality_check: QualityCheck, inbound_order: InboundOrderV3):
        """
        自动生成质检项目
        
        Args:
            quality_check: 质检单
            inbound_order: 入库单
        """
        items = inbound_order.items.all()
        
        for item in items:
            check_item = QualityCheckItem(
                check_id=quality_check.id,
                inbound_item_id=item.id,
                part_id=item.part_id,
                part_no=item.part_no,
                part_name=item.part_name,
                expected_quantity=item.quantity,
                status='pending'
            )
            db.session.add(check_item)
        
        logger.info(f"为质检单 {quality_check.check_no} 生成 {len(items)} 个质检项目")
    
    @staticmethod
    def start_inspection(check_id: int, user_id: int) -> bool:
        """
        开始质检
        
        Args:
            check_id: 质检单 ID
            user_id: 用户 ID
            
        Returns:
            是否成功
        """
        quality_check = QualityCheck.query.get(check_id)
        if not quality_check:
            return False
        
        if quality_check.status != 'pending':
            logger.warning(f"质检单 {quality_check.check_no} 状态不是待检状态")
            return False
        
        quality_check.status = 'inspecting'
        quality_check.started_at = datetime.utcnow()
        quality_check.started_by = user_id
        quality_check.inspector_id = user_id
        
        db.session.commit()
        
        logger.info(f"开始质检：{quality_check.check_no}")
        return True
    
    @staticmethod
    def submit_inspection_result(
        check_id: int, 
        items_data: List[Dict],
        user_id: int
    ) -> Tuple[bool, str]:
        """
        提交质检结果
        
        Args:
            check_id: 质检单 ID
            items_data: 质检项目数据列表
            user_id: 用户 ID
            
        Returns:
            (成功标志，消息)
        """
        quality_check = QualityCheck.query.get(check_id)
        if not quality_check:
            return False, "质检单不存在"
        
        if quality_check.status != 'inspecting':
            return False, "质检单未开始或已完成"
        
        total_quantity = Decimal('0')
        qualified_count = Decimal('0')
        unqualified_count = Decimal('0')
        
        # 处理每个质检项目
        for item_data in items_data:
            check_item = QualityCheckItem.query.get(item_data['id'])
            if not check_item:
                continue
            
            # 更新质检项目
            check_item.checked_quantity = Decimal(str(item_data.get('checked_quantity', 0)))
            check_item.qualified_quantity = Decimal(str(item_data.get('qualified_quantity', 0)))
            check_item.unqualified_quantity = Decimal(str(item_data.get('unqualified_quantity', 0)))
            check_item.pass_rate = item_data.get('pass_rate')
            check_item.status = 'completed'
            check_item.remark = item_data.get('remark', '')
            
            # 累计总数
            total_quantity += check_item.checked_quantity
            qualified_count += check_item.qualified_quantity
            unqualified_count += check_item.unqualified_quantity
        
        # 计算总合格率
        if total_quantity > 0:
            pass_rate = (qualified_count / total_quantity) * 100
        else:
            pass_rate = Decimal('0')
        
        # 更新质检单
        quality_check.total_quantity = total_quantity
        quality_check.qualified_count = qualified_count
        quality_check.unqualified_count = unqualified_count
        quality_check.pass_rate = pass_rate
        quality_check.status = 'completed'
        quality_check.completed_at = datetime.utcnow()
        quality_check.completed_by = user_id
        
        # 判定结果
        if pass_rate >= 100:
            quality_check.result = 'pass'
        elif pass_rate >= 95:
            quality_check.result = 'conditional_pass'
        else:
            quality_check.result = 'fail'
        
        db.session.commit()
        
        logger.info(f"提交质检结果：{quality_check.check_no}, 合格率：{pass_rate}%")
        return True, "质检结果提交成功"
    
    @staticmethod
    def approve_quality_check(check_id: int, user_id: int, approved: bool) -> bool:
        """
        审批质检结果
        
        Args:
            check_id: 质检单 ID
            user_id: 用户 ID
            approved: 是否批准
            
        Returns:
            是否成功
        """
        quality_check = QualityCheck.query.get(check_id)
        if not quality_check:
            return False
        
        if quality_check.status != 'completed':
            logger.warning(f"质检单 {quality_check.check_no} 未完成，无法审批")
            return False
        
        if approved:
            quality_check.status = 'approved'
            # 更新入库单状态
            inbound_order = quality_check.inbound_order
            if inbound_order:
                inbound_order.status = 'completed'
        else:
            quality_check.status = 'rejected'
        
        db.session.commit()
        
        logger.info(f"审批质检单：{quality_check.check_no}, 结果：{'批准' if approved else '拒绝'}")
        return True
    
    @staticmethod
    def complete_inbound_with_check(inbound_order_id: int, user_id: int) -> Tuple[bool, str]:
        """
        完成质检并入库
        
        Args:
            inbound_order_id: 入库单 ID
            user_id: 用户 ID
            
        Returns:
            (成功标志，消息)
        """
        inbound_order = InboundOrderV3.query.get(inbound_order_id)
        if not inbound_order:
            return False, "入库单不存在"
        
        # 获取质检单
        quality_check = QualityCheck.query.filter_by(
            inbound_order_id=inbound_order_id
        ).first()
        
        if not quality_check:
            return False, "该入库单没有质检单"
        
        if quality_check.status != 'approved':
            return False, "质检单未批准，无法入库"
        
        # 创建库存记录
        for item in inbound_order.items.all():
            # 查找对应的质检项目
            check_item = QualityCheckItem.query.filter_by(
                check_id=quality_check.id,
                inbound_item_id=item.id
            ).first()
            
            if not check_item:
                continue
            
            # 只入库合格品
            if check_item.qualified_quantity > 0:
                QualityCheckService.create_inventory_from_check(
                    quality_check,
                    check_item,
                    item,
                    user_id
                )
        
        # 更新入库单状态
        inbound_order.status = 'completed'
        inbound_order.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"完成质检入库：{inbound_order.order_no}")
        return True, "质检入库完成"
    
    @staticmethod
    def create_inventory_from_check(
        quality_check: QualityCheck,
        check_item: QualityCheckItem,
        inbound_item: InboundOrderItemV3,
        user_id: int
    ):
        """
        从质检项目创建库存记录
        
        Args:
            quality_check: 质检单
            check_item: 质检项目
            inbound_item: 入库项目
            user_id: 用户 ID
        """
        # 检查是否已有库存
        inventory = InventoryV3.query.filter_by(
            warehouse_id=inbound_item.warehouse_id,
            part_id=inbound_item.part_id,
            location_id=inbound_item.location_id,
            batch_no=inbound_item.batch_no
        ).first()
        
        if inventory:
            # 更新现有库存
            inventory.quantity += check_item.qualified_quantity
            inventory.available_quantity += check_item.qualified_quantity
            inventory.last_inbound_date = datetime.utcnow()
        else:
            # 创建新库存
            inventory = InventoryV3(
                warehouse_id=inbound_item.warehouse_id,
                part_id=inbound_item.part_id,
                part_no=inbound_item.part_no,
                location_id=inbound_item.location_id,
                quantity=check_item.qualified_quantity,
                available_quantity=check_item.qualified_quantity,
                locked_quantity=0,
                batch_no=inbound_item.batch_no,
                unit=inbound_item.unit,
                unit_cost=inbound_item.unit_price or Decimal('0'),
                total_cost=check_item.qualified_quantity * (inbound_item.unit_price or Decimal('0')),
                status='normal',
                quality_status='qualified',
                last_inbound_date=datetime.utcnow()
            )
            db.session.add(inventory)
        
        logger.info(f"创建/更新库存：备件 {inbound_item.part_no}, 数量 {check_item.qualified_quantity}")
    
    @staticmethod
    def get_quality_check_statistics(
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict:
        """
        获取质检统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        query = QualityCheck.query
        
        if start_date:
            query = query.filter(QualityCheck.created_at >= start_date)
        if end_date:
            query = query.filter(QualityCheck.created_at <= end_date)
        
        total = query.count()
        pending = query.filter_by(status='pending').count()
        inspecting = query.filter_by(status='inspecting').count()
        completed = query.filter_by(status='completed').count()
        approved = query.filter_by(status='approved').count()
        rejected = query.filter_by(status='rejected').count()
        
        # 计算平均合格率
        checks_with_result = query.filter(QualityCheck.pass_rate.isnot(None)).all()
        if checks_with_result:
            avg_pass_rate = sum(c.pass_rate for c in checks_with_result) / len(checks_with_result)
        else:
            avg_pass_rate = 0
        
        return {
            'total': total,
            'pending': pending,
            'inspecting': inspecting,
            'completed': completed,
            'approved': approved,
            'rejected': rejected,
            'avg_pass_rate': float(avg_pass_rate) if avg_pass_rate else 0
        }
