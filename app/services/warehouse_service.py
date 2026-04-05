"""
仓库服务层
"""

from app.models.warehouse import Warehouse
from app.models.warehouse_location import WarehouseLocation
from app.extensions import db


class WarehouseService:
    """仓库服务类"""
    
    @staticmethod
    def create_warehouse(data):
        """创建仓库"""
        warehouse = Warehouse(
            name=data['name'],
            code=data['code'],
            type=data.get('type', 'general'),
            manager_id=data.get('manager_id'),
            address=data.get('address'),
            area=data.get('area'),
            capacity=data.get('capacity'),
            phone=data.get('phone'),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )
        db.session.add(warehouse)
        db.session.commit()
        return warehouse
    
    @staticmethod
    def update_warehouse(warehouse_id, data):
        """更新仓库"""
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return None
        
        for key, value in data.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        
        db.session.commit()
        return warehouse
    
    @staticmethod
    def delete_warehouse(warehouse_id):
        """删除仓库"""
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return False
        
        # 检查是否有关联的库位
        if warehouse.locations.count() > 0:
            return False
        
        db.session.delete(warehouse)
        db.session.commit()
        return True
    
    @staticmethod
    def get_warehouse(warehouse_id):
        """获取仓库详情"""
        return Warehouse.query.get(warehouse_id)
    
    @staticmethod
    def get_warehouses(filters=None, page=1, per_page=20):
        """获取仓库列表"""
        query = Warehouse.query
        
        if filters:
            if filters.get('name'):
                query = query.filter(Warehouse.name.like(f"%{filters['name']}%"))
            if filters.get('code'):
                query = query.filter(Warehouse.code.like(f"%{filters['code']}%"))
            if filters.get('type'):
                query = query.filter(Warehouse.type == filters['type'])
            if filters.get('is_active') is True:
                query = query.filter(Warehouse.is_active == True)
            elif filters.get('is_active') is False:
                query = query.filter(Warehouse.is_active == False)
        
        pagination = query.order_by(Warehouse.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return pagination
    
    @staticmethod
    def get_warehouse_statistics():
        """获取仓库统计信息"""
        total = Warehouse.query.count()
        active = Warehouse.query.filter_by(is_active=True).count()
        inactive = total - active
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive
        }
    
    @staticmethod
    def get_total_inventory(warehouse_id):
        """获取仓库总库存"""
        from app.models.transaction import Transaction, TransactionDetail
        
        # 计算入库总量
        in_total = db.session.query(db.func.sum(TransactionDetail.quantity)).join(
            Transaction
        ).filter(
            Transaction.warehouse_id == warehouse_id,
            Transaction.transaction_type.in_(['in', 'adjust_in'])
        ).scalar() or 0
        
        # 计算出库总量
        out_total = db.session.query(db.func.sum(TransactionDetail.quantity)).join(
            Transaction
        ).filter(
            Transaction.warehouse_id == warehouse_id,
            Transaction.transaction_type.in_(['out', 'adjust_out'])
        ).scalar() or 0
        
        return in_total - out_total
    
    @staticmethod
    def get_utilization_rate(warehouse_id):
        """获取仓库利用率"""
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse or not warehouse.capacity:
            return 0
        
        total_inventory = WarehouseService.get_total_inventory(warehouse_id)
        return min(100, (total_inventory / warehouse.capacity) * 100)
    
    @staticmethod
    def get_operations_count(warehouse_id):
        """获取操作次数"""
        from app.models.transaction import Transaction
        return Transaction.query.filter_by(warehouse_id=warehouse_id).count()
    
    @staticmethod
    def check_warehouse_inventory_alerts(warehouse_id):
        """检查仓库库存预警"""
        from app.models.spare_part import SparePart
        from app.models.transaction import Transaction, TransactionDetail
        from app.models.system import Alert, Notification
        from app.models.user import User
        from app.utils.email_service import email_service
        import logging
        
        logger = logging.getLogger(__name__)
        alerts = []
        
        # 获取仓库中的所有备件及其在该仓库的库存
        warehouse_spare_parts = db.session.query(
            SparePart,
            db.func.sum(
                db.case(
                    (Transaction.transaction_type.in_(['in', 'adjust_in']), TransactionDetail.quantity),
                    (Transaction.transaction_type.in_(['out', 'adjust_out']), -TransactionDetail.quantity),
                    else_=0
                )
            ).label('warehouse_stock')
        ).join(
            Transaction, Transaction.spare_part_id == SparePart.id
        ).join(
            TransactionDetail, TransactionDetail.transaction_id == Transaction.id
        ).filter(
            Transaction.warehouse_id == warehouse_id,
            SparePart.is_active == True
        ).group_by(
            SparePart.id
        ).all()
        
        # 检查每个备件的库存状态
        for spare_part, warehouse_stock in warehouse_spare_parts:
            warehouse_stock = warehouse_stock or 0
            
            # 检查低库存
            if warehouse_stock <= spare_part.min_stock and spare_part.min_stock > 0:
                alert = Alert(
                    alert_type='stock',
                    title=f'仓库低库存预警: {spare_part.part_code}',
                    message=f'仓库 {Warehouse.query.get(warehouse_id).name} 中的备件 {spare_part.part_code} - {spare_part.name} 库存不足，当前库存：{warehouse_stock}，最低库存：{spare_part.min_stock}',
                    level='warning',
                    status='active',
                    related_object_id=spare_part.id,
                    related_object_type='spare_part'
                )
                db.session.add(alert)
                alerts.append(alert)
                
                # 为管理员创建通知
                admin_user = User.query.filter_by(username='admin', is_admin=True, is_active=True).first()
                if admin_user:
                    notification = Notification(
                        user_id=admin_user.id,
                        title='仓库低库存预警',
                        message=f'仓库 {Warehouse.query.get(warehouse_id).name} 中的备件 {spare_part.part_code} - {spare_part.name} 库存不足',
                        type='stock_alert',
                        level='warning',
                        related_object_id=spare_part.id,
                        related_object_type='spare_part'
                    )
                    db.session.add(notification)
                    
                    # 发送邮件通知
                    if admin_user.email:
                        try:
                            email_service.send_stock_alert(admin_user, spare_part, user_id=admin_user.id)
                        except Exception as e:
                            logger.error(f"发送库存预警邮件失败：{str(e)}")
            
            # 检查缺货
            if warehouse_stock == 0:
                alert = Alert(
                    alert_type='stock',
                    title=f'仓库缺货预警: {spare_part.part_code}',
                    message=f'仓库 {Warehouse.query.get(warehouse_id).name} 中的备件 {spare_part.part_code} - {spare_part.name} 已缺货',
                    level='danger',
                    status='active',
                    related_object_id=spare_part.id,
                    related_object_type='spare_part'
                )
                db.session.add(alert)
                alerts.append(alert)
                
                # 为管理员创建通知
                admin_user = User.query.filter_by(username='admin', is_admin=True, is_active=True).first()
                if admin_user:
                    notification = Notification(
                        user_id=admin_user.id,
                        title='仓库缺货预警',
                        message=f'仓库 {Warehouse.query.get(warehouse_id).name} 中的备件 {spare_part.part_code} - {spare_part.name} 已缺货',
                        type='stock_alert',
                        level='danger',
                        related_object_id=spare_part.id,
                        related_object_type='spare_part'
                    )
                    db.session.add(notification)
                    
                    # 发送邮件通知
                    if admin_user.email:
                        try:
                            email_service.send_stock_alert(admin_user, spare_part, user_id=admin_user.id)
                        except Exception as e:
                            logger.error(f"发送库存预警邮件失败：{str(e)}")
            
            # 检查超储
            if spare_part.max_stock and warehouse_stock >= spare_part.max_stock:
                alert = Alert(
                    alert_type='stock',
                    title=f'仓库超储预警: {spare_part.part_code}',
                    message=f'仓库 {Warehouse.query.get(warehouse_id).name} 中的备件 {spare_part.part_code} - {spare_part.name} 库存超储，当前库存：{warehouse_stock}，最高库存：{spare_part.max_stock}',
                    level='info',
                    status='active',
                    related_object_id=spare_part.id,
                    related_object_type='spare_part'
                )
                db.session.add(alert)
                alerts.append(alert)
        
        if alerts:
            db.session.commit()
            logger.info(f"仓库 {warehouse_id} 库存预警检查完成，共触发 {len(alerts)} 个预警")
        
        return alerts
    
    @staticmethod
    def check_all_warehouses_inventory():
        """检查所有仓库的库存预警"""
        warehouses = Warehouse.query.filter_by(is_active=True).all()
        all_alerts = []
        
        for warehouse in warehouses:
            alerts = WarehouseService.check_warehouse_inventory_alerts(warehouse.id)
            all_alerts.extend(alerts)
        
        return all_alerts
