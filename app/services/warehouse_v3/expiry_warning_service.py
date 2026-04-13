"""
库存效期预警服务
"""

from datetime import datetime, timedelta
from app.models.warehouse_v3.inventory import InventoryV3
from app import db


class ExpiryWarningService:
    """效期预警服务类"""
    
    @staticmethod
    def get_expiry_warnings(days_threshold=30, warehouse_id=None):
        """
        获取近效期库存预警
        
        Args:
            days_threshold: 预警天数阈值（默认 30 天）
            warehouse_id: 仓库 ID（可选，不传则查询所有仓库）
            
        Returns:
            list: 近效期库存列表
        """
        # 计算预警日期范围
        today = datetime.now().date()
        warning_date = today + timedelta(days=days_threshold)
        
        # 构建查询
        query = InventoryV3.query.filter(
            InventoryV3.expiry_date != None,
            InventoryV3.expiry_date <= warning_date,
            InventoryV3.expiry_date >= today,
            InventoryV3.quantity > 0
        )
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        # 按过期日期排序
        query = query.order_by(InventoryV3.expiry_date.asc())
        
        inventories = query.all()
        
        warnings = []
        for inv in inventories:
            days_remaining = (inv.expiry_date - today).days
            
            # 确定预警级别
            if days_remaining <= 7:
                warning_level = 'red'  # 红色预警：7 天内过期
            elif days_remaining <= 15:
                warning_level = 'orange'  # 橙色预警：15 天内过期
            else:
                warning_level = 'yellow'  # 黄色预警：30 天内过期
            
            warnings.append({
                'inventory_id': inv.id,
                'warehouse_id': inv.warehouse_id,
                'warehouse_name': inv.warehouse.name if inv.warehouse else None,
                'part_id': inv.part_id,
                'part_code': inv.part.code if inv.part else None,
                'part_name': inv.part.name if inv.part else None,
                'specification': inv.part.specification if inv.part else None,
                'quantity': float(inv.quantity),
                'unit': inv.unit,
                'expiry_date': inv.expiry_date.strftime('%Y-%m-%d'),
                'days_remaining': days_remaining,
                'warning_level': warning_level,
                'batch_no': inv.batch.batch_no if inv.batch else None,
                'location_name': inv.location.name if inv.location else None
            })
        
        return warnings
    
    @staticmethod
    def get_expired_inventory(warehouse_id=None):
        """
        获取已过期库存
        
        Args:
            warehouse_id: 仓库 ID（可选）
            
        Returns:
            list: 已过期库存列表
        """
        today = datetime.now().date()
        
        query = InventoryV3.query.filter(
            InventoryV3.expiry_date != None,
            InventoryV3.expiry_date < today,
            InventoryV3.quantity > 0
        )
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        query = query.order_by(InventoryV3.expiry_date.asc())
        
        inventories = query.all()
        
        expired_list = []
        for inv in inventories:
            days_overdue = (today - inv.expiry_date).days
            
            expired_list.append({
                'inventory_id': inv.id,
                'warehouse_id': inv.warehouse_id,
                'warehouse_name': inv.warehouse.name if inv.warehouse else None,
                'part_id': inv.part_id,
                'part_code': inv.part.code if inv.part else None,
                'part_name': inv.part.name if inv.part else None,
                'specification': inv.part.specification if inv.part else None,
                'quantity': float(inv.quantity),
                'unit': inv.unit,
                'expiry_date': inv.expiry_date.strftime('%Y-%m-%d'),
                'days_overdue': days_overdue,
                'batch_no': inv.batch.batch_no if inv.batch else None,
                'location_name': inv.location.name if inv.location else None,
                'status': inv.status,
                'quality_status': inv.quality_status
            })
        
        return expired_list
    
    @staticmethod
    def get_expiry_statistics(warehouse_id=None):
        """
        获取效期统计信息
        
        Args:
            warehouse_id: 仓库 ID（可选）
            
        Returns:
            dict: 统计信息
        """
        today = datetime.now().date()
        
        # 查询所有有有效期的库存
        query = InventoryV3.query.filter(
            InventoryV3.expiry_date != None,
            InventoryV3.quantity > 0
        )
        
        if warehouse_id:
            query = query.filter(InventoryV3.warehouse_id == warehouse_id)
        
        inventories = query.all()
        
        stats = {
            'total_items': len(inventories),
            'expired_count': 0,
            'expired_quantity': 0,
            'warning_7days_count': 0,
            'warning_7days_quantity': 0,
            'warning_15days_count': 0,
            'warning_15days_quantity': 0,
            'warning_30days_count': 0,
            'warning_30days_quantity': 0,
            'normal_count': 0,
            'normal_quantity': 0
        }
        
        for inv in inventories:
            days_remaining = (inv.expiry_date - today).days if inv.expiry_date else None
            quantity = float(inv.quantity)
            
            if days_remaining is not None:
                if days_remaining < 0:
                    # 已过期
                    stats['expired_count'] += 1
                    stats['expired_quantity'] += quantity
                elif days_remaining <= 7:
                    stats['warning_7days_count'] += 1
                    stats['warning_7days_quantity'] += quantity
                elif days_remaining <= 15:
                    stats['warning_15days_count'] += 1
                    stats['warning_15days_quantity'] += quantity
                elif days_remaining <= 30:
                    stats['warning_30days_count'] += 1
                    stats['warning_30days_quantity'] += quantity
                else:
                    stats['normal_count'] += 1
                    stats['normal_quantity'] += quantity
        
        return stats
    
    @staticmethod
    def lock_near_expiry_inventory(inventory_id, days_threshold=7):
        """
        锁定近效期库存
        
        Args:
            inventory_id: 库存 ID
            days_threshold: 天数阈值
            
        Returns:
            bool: 是否成功锁定
        """
        inv = InventoryV3.query.get(inventory_id)
        if not inv:
            return False, '库存不存在'
        
        if not inv.expiry_date:
            return False, '该库存没有有效期信息'
        
        days_remaining = (inv.expiry_date - datetime.now().date()).days
        
        if days_remaining > days_threshold:
            return False, f'距离过期还有{days_remaining}天，不需要锁定'
        
        # 锁定库存
        old_status = inv.status
        inv.status = 'locked'
        inv.quality_status = '近效期'
        
        # 记录操作日志
        from app.services.warehouse_v3.inventory_transaction_log_service import InventoryTransactionLogService
        from flask_login import current_user
        
        log = InventoryTransactionLogService.create_transaction_log(
            inventory_id=inventory_id,
            change_type='LOCK',
            change_quantity=0,
            operator_id=current_user.id if current_user else 1,
            source_type='EXPIRY_WARNING',
            remark=f'近效期自动锁定（剩余{days_remaining}天）'
        )
        
        db.session.add(log)
        
        return True, f'已锁定库存，距离过期还有{days_remaining}天'
    
    @staticmethod
    def generate_expiry_report(warehouse_id=None, start_date=None, end_date=None):
        """
        生成效期预警报告
        
        Args:
            warehouse_id: 仓库 ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 报告数据
        """
        warnings = ExpiryWarningService.get_expiry_warnings(days_threshold=30, warehouse_id=warehouse_id)
        expired = ExpiryWarningService.get_expired_inventory(warehouse_id=warehouse_id)
        stats = ExpiryWarningService.get_expiry_statistics(warehouse_id=warehouse_id)
        
        report = {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'warehouse_id': warehouse_id,
            'statistics': stats,
            'warnings': {
                'near_expiry': warnings,
                'expired': expired
            },
            'recommendations': []
        }
        
        # 生成建议
        if stats['expired_count'] > 0:
            report['recommendations'].append({
                'priority': 'HIGH',
                'type': 'EXPIRED',
                'message': f'发现{stats["expired_count"]}项已过期库存，总计{stats["expired_quantity"]:.2f}，建议立即处理'
            })
        
        if stats['warning_7days_count'] > 0:
            report['recommendations'].append({
                'priority': 'HIGH',
                'type': 'NEAR_EXPIRY',
                'message': f'发现{stats["warning_7days_count"]}项 7 天内过期的库存，建议优先销售或使用'
            })
        
        if stats['warning_15days_count'] > 0:
            report['recommendations'].append({
                'priority': 'MEDIUM',
                'type': 'NEAR_EXPIRY',
                'message': f'发现{stats["warning_15days_count"]}项 15 天内过期的库存，建议加快销售'
            })
        
        return report
