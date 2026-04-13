"""
预警服务
提供预警规则检查、预警生成和通知发送等功能
"""

from datetime import datetime
from typing import List, Dict, Optional
from app import db
from app.models.warehouse_v3.warning import WarningRule, WarningLog
from app.models.warehouse_v3.inventory import InventoryV3
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class WarningService:
    """预警服务类"""
    
    @staticmethod
    def check_all_rules() -> List[WarningLog]:
        """
        检查所有启用的预警规则
        
        Returns:
            生成的预警日志列表
        """
        generated_warnings = []
        
        # 获取所有启用的规则
        rules = WarningRule.query.filter_by(enabled=True).all()
        
        for rule in rules:
            try:
                warnings = WarningService.check_rule(rule)
                generated_warnings.extend(warnings)
            except Exception as e:
                logger.error(f"检查规则 {rule.rule_name} 时出错：{str(e)}")
        
        return generated_warnings
    
    @staticmethod
    def check_rule(rule: WarningRule) -> List[WarningLog]:
        """
        检查单条预警规则
        
        Args:
            rule: 预警规则
            
        Returns:
            生成的预警日志列表
        """
        generated_warnings = []
        
        # 根据规则的适用范围查询库存
        query = InventoryV3.query
        
        if rule.warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == rule.warehouse_id)
        
        if rule.category_id:
            query = query.join(InventoryV3.part).filter(
                InventoryV3.part.has(category_id=rule.category_id)
            )
        
        if rule.part_id:
            query = query.filter(InventoryV3.part_id == rule.part_id)
        
        inventories = query.all()
        
        for inventory in inventories:
            try:
                warning = WarningService.evaluate_inventory(inventory, rule)
                if warning:
                    generated_warnings.append(warning)
            except Exception as e:
                logger.error(f"检查库存 {inventory.id} 时出错：{str(e)}")
        
        return generated_warnings
    
    @staticmethod
    def evaluate_inventory(inventory: InventoryV3, rule: WarningRule) -> Optional[WarningLog]:
        """
        评估库存是否触发预警
        
        Args:
            inventory: 库存记录
            rule: 预警规则
            
        Returns:
            如果触发预警则返回预警日志，否则返回 None
        """
        # 获取当前值
        current_value = WarningService.get_field_value(inventory, rule.condition_field)
        
        if current_value is None:
            return None
        
        # 根据条件判断是否触发预警
        triggered = False
        threshold_value = float(rule.threshold_value)
        
        if rule.condition_operator == 'lt':  # 小于
            triggered = current_value < threshold_value
        elif rule.condition_operator == 'lte':  # 小于等于
            triggered = current_value <= threshold_value
        elif rule.condition_operator == 'gt':  # 大于
            triggered = current_value > threshold_value
        elif rule.condition_operator == 'gte':  # 大于等于
            triggered = current_value >= threshold_value
        elif rule.condition_operator == 'eq':  # 等于
            triggered = current_value == threshold_value
        elif rule.condition_operator == 'ne':  # 不等于
            triggered = current_value != threshold_value
        
        if triggered:
            # 生成预警内容
            warning_content = WarningService.generate_warning_content(
                inventory, rule, current_value, threshold_value
            )
            
            # 创建预警日志
            warning_log = WarningLog.create_warning(
                rule=rule,
                inventory=inventory,
                current_value=current_value,
                threshold_value=threshold_value,
                warning_content=warning_content,
                warning_level=rule.warning_level
            )
            
            db.session.add(warning_log)
            db.session.commit()
            
            # 发送通知
            WarningService.send_notification(warning_log, rule)
            
            logger.info(f"生成预警：{rule.rule_name} - 库存 {inventory.id}")
            return warning_log
        
        return None
    
    @staticmethod
    def get_field_value(inventory: InventoryV3, field_name: str) -> Optional[float]:
        """
        获取库存对象的字段值
        
        Args:
            inventory: 库存记录
            field_name: 字段名
            
        Returns:
            字段值
        """
        field_mapping = {
            'quantity': inventory.quantity,
            'available_quantity': inventory.available_quantity,
            'locked_quantity': inventory.locked_quantity,
            'min_stock': inventory.min_stock,
            'max_stock': inventory.max_stock,
            'reorder_point': inventory.reorder_point,
            'unit_cost': inventory.unit_cost,
            'total_cost': inventory.total_cost,
            'turnover_rate': inventory.turnover_rate,
        }
        
        value = field_mapping.get(field_name)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        
        return None
    
    @staticmethod
    def generate_warning_content(
        inventory: InventoryV3, 
        rule: WarningRule, 
        current_value: float, 
        threshold_value: float
    ) -> str:
        """
        生成预警内容
        
        Args:
            inventory: 库存记录
            rule: 预警规则
            current_value: 当前值
            threshold_value: 阈值
            
        Returns:
            预警内容字符串
        """
        part_name = inventory.part.name if inventory.part else '未知备件'
        part_no = inventory.part.part_no if inventory.part else '未知编号'
        warehouse_name = inventory.warehouse.name if inventory.warehouse else '未知仓库'
        
        content = (
            f"预警规则：{rule.rule_name}\n"
            f"备件：{part_name} ({part_no})\n"
            f"仓库：{warehouse_name}\n"
            f"当前值：{current_value}\n"
            f"阈值：{threshold_value}\n"
            f"预警级别：{rule.warning_level}"
        )
        
        return content
    
    @staticmethod
    def send_notification(warning_log: WarningLog, rule: WarningRule):
        """
        发送预警通知
        
        Args:
            warning_log: 预警日志
            rule: 预警规则
        """
        # TODO: 实现多渠道通知（邮件、短信、系统消息）
        # 目前仅记录日志
        logger.info(f"预警通知已生成：{warning_log.id}")
        
        # 标记已通知
        warning_log.notified_users = rule.notify_users or []
        warning_log.notified_time = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def handle_warning(warning_id: int, handler_id: int, notes: str = None) -> bool:
        """
        处理预警
        
        Args:
            warning_id: 预警 ID
            handler_id: 处理人 ID
            notes: 处理备注
            
        Returns:
            是否成功
        """
        warning = WarningLog.query.get(warning_id)
        if not warning:
            return False
        
        warning.status = 'handled'
        warning.handled_user = handler_id
        warning.handled_time = datetime.utcnow()
        warning.handled_notes = notes
        
        db.session.commit()
        return True
    
    @staticmethod
    def get_warning_statistics(
        start_date: datetime = None, 
        end_date: datetime = None
    ) -> Dict:
        """
        获取预警统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        query = WarningLog.query
        
        if start_date:
            query = query.filter(WarningLog.created_at >= start_date)
        if end_date:
            query = query.filter(WarningLog.created_at <= end_date)
        
        total = query.count()
        unhandled = query.filter_by(status='unhandled').count()
        handled = query.filter_by(status='handled').count()
        
        # 按级别统计
        by_level = db.session.query(
            WarningLog.warning_level, 
            db.func.count(WarningLog.id)
        ).group_by(WarningLog.warning_level).all()
        
        # 按规则统计
        by_rule = db.session.query(
            WarningLog.rule_id, 
            db.func.count(WarningLog.id)
        ).group_by(WarningLog.rule_id).all()
        
        return {
            'total': total,
            'unhandled': unhandled,
            'handled': handled,
            'by_level': dict(by_level),
            'by_rule': dict(by_rule)
        }
