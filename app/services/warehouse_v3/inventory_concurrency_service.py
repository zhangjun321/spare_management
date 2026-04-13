"""
库存并发控制服务
提供乐观锁、防超卖等并发控制机制
"""

from typing import Tuple, Optional, Dict
from decimal import Decimal
from datetime import datetime
from app import db
from app.models.warehouse_v3.inventory import InventoryV3
import logging

logger = logging.getLogger(__name__)


class ConcurrencyError(Exception):
    """并发冲突异常"""
    pass


class InsufficientStockError(Exception):
    """库存不足异常"""
    pass


class InventoryConcurrencyService:
    """库存并发控制服务类"""
    
    @staticmethod
    def decrease_stock_with_optimistic_lock(
        inventory_id: int,
        quantity: Decimal,
        user_id: int,
        reason: str = None
    ) -> Tuple[bool, str, Optional[InventoryV3]]:
        """
        使用乐观锁扣减库存
        
        Args:
            inventory_id: 库存 ID
            quantity: 扣减数量
            user_id: 用户 ID
            reason: 扣减原因
            
        Returns:
            (成功标志，消息，库存对象)
        """
        try:
            # 获取库存（带版本号）
            inventory = InventoryV3.query.get(inventory_id)
            if not inventory:
                return False, "库存不存在", None
            
            # 检查可用库存
            if inventory.available_quantity < quantity:
                return False, f"可用库存不足：当前 {inventory.available_quantity}，需要 {quantity}", None
            
            # 使用乐观锁更新
            current_version = inventory.version
            result = db.session.query(InventoryV3).filter(
                InventoryV3.id == inventory_id,
                InventoryV3.version == current_version,
                InventoryV3.available_quantity >= quantity
            ).update({
                'quantity': InventoryV3.quantity - quantity,
                'available_quantity': InventoryV3.available_quantity - quantity,
                'locked_quantity': InventoryV3.locked_quantity + quantity,
                'version': InventoryV3.version + 1,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)

            
            if result == 0:
                # 更新失败，可能是版本号不匹配或库存不足
                db.session.rollback()
                logger.warning(f"库存扣减失败（乐观锁冲突）：ID={inventory_id}, 版本={current_version}")
                return False, "库存数据已被其他操作修改，请重试", None
            
            db.session.commit()
            
            # 重新获取最新数据
            inventory = InventoryV3.query.get(inventory_id)
            
            logger.info(f"库存扣减成功：ID={inventory_id}, 数量={quantity}, 版本={current_version + 1}")
            return True, "库存扣减成功", inventory
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"库存扣减异常：{str(e)}")
            return False, f"扣减失败：{str(e)}", None
    
    @staticmethod
    def increase_stock_with_optimistic_lock(
        inventory_id: int,
        quantity: Decimal,
        user_id: int,
        reason: str = None
    ) -> Tuple[bool, str, Optional[InventoryV3]]:
        """
        使用乐观锁增加库存
        
        Args:
            inventory_id: 库存 ID
            quantity: 增加数量
            user_id: 用户 ID
            reason: 增加原因
            
        Returns:
            (成功标志，消息，库存对象)
        """
        try:
            # 获取库存（带版本号）
            inventory = InventoryV3.query.get(inventory_id)
            if not inventory:
                return False, "库存不存在", None
            
            # 使用乐观锁更新
            current_version = inventory.version
            result = db.session.query(InventoryV3).filter(
                InventoryV3.id == inventory_id,
                InventoryV3.version == current_version
            ).update({
                'quantity': InventoryV3.quantity + quantity,
                'available_quantity': InventoryV3.available_quantity + quantity,
                'version': InventoryV3.version + 1,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)
            
            if result == 0:
                db.session.rollback()
                logger.warning(f"库存增加失败（乐观锁冲突）：ID={inventory_id}, 版本={current_version}")
                return False, "库存数据已被其他操作修改，请重试", None
            
            db.session.commit()
            
            # 重新获取最新数据
            inventory = InventoryV3.query.get(inventory_id)
            
            logger.info(f"库存增加成功：ID={inventory_id}, 数量={quantity}, 版本={current_version + 1}")
            return True, "库存增加成功", inventory
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"库存增加异常：{str(e)}")
            return False, f"增加失败：{str(e)}", None
    
    @staticmethod
    def lock_stock(inventory_id: int, quantity: Decimal, user_id: int) -> Tuple[bool, str]:
        """
        锁定库存（用于出库流程）
        
        Args:
            inventory_id: 库存 ID
            quantity: 锁定数量
            user_id: 用户 ID
            
        Returns:
            (成功标志，消息)
        """
        try:
            inventory = InventoryV3.query.get(inventory_id)
            if not inventory:
                return False, "库存不存在"
            
            if inventory.available_quantity < quantity:
                return False, f"可用库存不足：当前 {inventory.available_quantity}，需要 {quantity}"
            
            # 使用乐观锁锁定
            current_version = inventory.version
            result = db.session.query(InventoryV3).filter(
                InventoryV3.id == inventory_id,
                InventoryV3.version == current_version,
                InventoryV3.available_quantity >= quantity
            ).update({
                'available_quantity': InventoryV3.available_quantity - quantity,
                'locked_quantity': InventoryV3.locked_quantity + quantity,
                'version': InventoryV3.version + 1,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)
            
            if result == 0:
                db.session.rollback()
                logger.warning(f"库存锁定失败（乐观锁冲突）：ID={inventory_id}, 版本={current_version}")
                return False, "库存数据已被其他操作修改，请重试"
            
            db.session.commit()
            
            logger.info(f"库存锁定成功：ID={inventory_id}, 数量={quantity}")
            return True, "库存锁定成功"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"库存锁定异常：{str(e)}")
            return False, f"锁定失败：{str(e)}"
    
    @staticmethod
    def unlock_stock(inventory_id: int, quantity: Decimal, user_id: int) -> Tuple[bool, str]:
        """
        解锁库存
        
        Args:
            inventory_id: 库存 ID
            quantity: 解锁数量
            user_id: 用户 ID
            
        Returns:
            (成功标志，消息)
        """
        try:
            inventory = InventoryV3.query.get(inventory_id)
            if not inventory:
                return False, "库存不存在"
            
            if inventory.locked_quantity < quantity:
                return False, f"锁定库存不足：当前 {inventory.locked_quantity}，需要 {quantity}"
            
            # 使用乐观锁解锁
            current_version = inventory.version
            result = db.session.query(InventoryV3).filter(
                InventoryV3.id == inventory_id,
                InventoryV3.version == current_version,
                InventoryV3.locked_quantity >= quantity
            ).update({
                'available_quantity': InventoryV3.available_quantity + quantity,
                'locked_quantity': InventoryV3.locked_quantity - quantity,
                'version': InventoryV3.version + 1,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)
            
            if result == 0:
                db.session.rollback()
                logger.warning(f"库存解锁失败（乐观锁冲突）：ID={inventory_id}, 版本={current_version}")
                return False, "库存数据已被其他操作修改，请重试"
            
            db.session.commit()
            
            logger.info(f"库存解锁成功：ID={inventory_id}, 数量={quantity}")
            return True, "库存解锁成功"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"库存解锁异常：{str(e)}")
            return False, f"解锁失败：{str(e)}"
    
    @staticmethod
    def transfer_stock(
        from_inventory_id: int,
        to_inventory_id: int,
        quantity: Decimal,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        库存调拨（原子操作）
        
        Args:
            from_inventory_id: 源库存 ID
            to_inventory_id: 目标库存 ID
            quantity: 调拨数量
            user_id: 用户 ID
            
        Returns:
            (成功标志，消息)
        """
        try:
            # 获取两个库存（都带版本号）
            from_inventory = InventoryV3.query.get(from_inventory_id)
            to_inventory = InventoryV3.query.get(to_inventory_id)
            
            if not from_inventory:
                return False, "源库存不存在"
            if not to_inventory:
                return False, "目标库存不存在"
            
            if from_inventory.available_quantity < quantity:
                return False, f"源库存不足：当前 {from_inventory.available_quantity}，需要 {quantity}"
            
            # 使用乐观锁同时更新两个库存
            from_version = from_inventory.version
            to_version = to_inventory.version
            
            # 更新源库存
            from_result = db.session.query(InventoryV3).filter(
                InventoryV3.id == from_inventory_id,
                InventoryV3.version == from_version,
                InventoryV3.available_quantity >= quantity
            ).update({
                'quantity': InventoryV3.quantity - quantity,
                'available_quantity': InventoryV3.available_quantity - quantity,
                'version': InventoryV3.version + 1,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)
            
            if from_result == 0:
                db.session.rollback()
                logger.warning(f"调拨失败：源库存乐观锁冲突 ID={from_inventory_id}")
                return False, "源库存数据已被修改，请重试"
            
            # 更新目标库存
            to_result = db.session.query(InventoryV3).filter(
                InventoryV3.id == to_inventory_id,
                InventoryV3.version == to_version
            ).update({
                'quantity': InventoryV3.quantity + quantity,
                'available_quantity': InventoryV3.available_quantity + quantity,
                'version': InventoryV3.version + 1,
                'updated_at': datetime.utcnow()
            }, synchronize_session=False)
            
            if to_result == 0:
                db.session.rollback()
                logger.warning(f"调拨失败：目标库存乐观锁冲突 ID={to_inventory_id}")
                return False, "目标库存数据已被修改，请重试"
            
            db.session.commit()
            
            logger.info(f"库存调拨成功：从 {from_inventory_id} 到 {to_inventory_id}, 数量={quantity}")
            return True, "库存调拨成功"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"库存调拨异常：{str(e)}")
            return False, f"调拨失败：{str(e)}"
    
    @staticmethod
    def check_and_lock_batch(
        warehouse_id: int,
        part_id: int,
        total_quantity: Decimal,
        fifo: bool = True
    ) -> Tuple[bool, str, list]:
        """
        批量锁定库存（先进先出策略）
        
        Args:
            warehouse_id: 仓库 ID
            part_id: 备件 ID
            total_quantity: 总数量
            fifo: 是否使用先进先出
            
        Returns:
            (成功标志，消息，锁定的库存列表)
        """
        try:
            # 查询库存
            query = InventoryV3.query.filter_by(
                warehouse_id=warehouse_id,
                part_id=part_id
            )
            
            # 按入库日期排序（先进先出）
            if fifo:
                query = query.order_by(InventoryV3.inbound_date.asc())
            
            inventories = query.all()
            
            if not inventories:
                return False, "库存不存在", []
            
            # 计算可用总量
            total_available = sum(inv.available_quantity for inv in inventories)
            if total_available < total_quantity:
                return False, f"库存不足：当前 {total_available}，需要 {total_quantity}", []
            
            # 逐个锁定
            locked_inventories = []
            remaining = total_quantity
            
            for inventory in inventories:
                if remaining <= 0:
                    break
                
                lock_qty = min(remaining, inventory.available_quantity)
                if lock_qty > 0:
                    success, msg = InventoryConcurrencyService.lock_stock(
                        inventory.id,
                        lock_qty,
                        0  # user_id 根据实际需要传入
                    )
                    
                    if not success:
                        # 回滚已锁定的
                        for locked in locked_inventories:
                            InventoryConcurrencyService.unlock_stock(
                                locked['id'],
                                locked['quantity'],
                                0
                            )
                        return False, f"锁定失败：{msg}", []
                    
                    locked_inventories.append({
                        'id': inventory.id,
                        'quantity': lock_qty
                    })
                    remaining -= lock_qty
            
            logger.info(f"批量锁定成功：备件 {part_id}, 数量={total_quantity}")
            return True, "批量锁定成功", locked_inventories
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"批量锁定异常：{str(e)}")
            return False, f"锁定失败：{str(e)}", []
    
    @staticmethod
    def get_stock_status(inventory_id: int) -> Dict:
        """
        获取库存状态
        
        Args:
            inventory_id: 库存 ID
            
        Returns:
            库存状态字典
        """
        inventory = InventoryV3.query.get(inventory_id)
        if not inventory:
            return {'error': '库存不存在'}
        
        return {
            'id': inventory.id,
            'warehouse_id': inventory.warehouse_id,
            'part_id': inventory.part_id,
            'quantity': float(inventory.quantity),
            'available_quantity': float(inventory.available_quantity),
            'locked_quantity': float(inventory.locked_quantity),
            'version': inventory.version,
            'status': inventory.status,
            'updated_at': inventory.updated_at.strftime('%Y-%m-%d %H:%M:%S') if inventory.updated_at else None
        }
