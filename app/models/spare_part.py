from app.extensions import db
from datetime import datetime


class SparePart(db.Model):
    __tablename__ = 'spare_part'
    
    id = db.Column(db.Integer, primary_key=True)
    part_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='备件代码')
    name = db.Column(db.String(200), nullable=False, index=True, comment='备件名称')
    specification = db.Column(db.String(200), comment='规格型号')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), index=True, comment='分类 ID')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), index=True, comment='供应商 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), index=True, comment='默认仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), index=True, comment='默认货位 ID')
    current_stock = db.Column(db.Integer, nullable=False, default=0, comment='当前库存')
    stock_status = db.Column(db.String(20), nullable=False, default='normal', index=True, comment='库存状态')
    min_stock = db.Column(db.Integer, default=0, comment='最低库存')
    max_stock = db.Column(db.Integer, comment='最高库存')
    unit = db.Column(db.String(20), comment='单位')
    unit_price = db.Column(db.Numeric(10, 2), comment='单价')
    location = db.Column(db.String(200), comment='存放位置')
    image_url = db.Column(db.String(500), comment='图片 URL')
    thumbnail_url = db.Column(db.String(500), comment='缩略图 URL')
    side_image_url = db.Column(db.String(500), comment='侧面图 URL')
    detail_image_url = db.Column(db.String(500), comment='详细图 URL')
    circuit_image_url = db.Column(db.String(500), comment='电路图 URL')
    perspective_image_url = db.Column(db.String(500), comment='透视图 URL')
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')

    version = db.Column(db.Integer, default=1, nullable=False, comment='乐观锁版本号')
    
    brand = db.Column(db.String(100), index=True, comment='品牌')
    barcode = db.Column(db.String(100), unique=True, index=True, nullable=True, comment='条形码')
    safety_stock = db.Column(db.Integer, default=0, comment='安全库存')
    reorder_point = db.Column(db.Integer, comment='再订货点')
    last_purchase_price = db.Column(db.Numeric(10, 2), comment='最近采购价')
    currency = db.Column(db.String(10), default='CNY', comment='币种')
    warranty_period = db.Column(db.Integer, comment='质保期 (月)')
    last_purchase_date = db.Column(db.DateTime, comment='最后采购日期')
    technical_params = db.Column(db.JSON, comment='技术参数')
    datasheet_url = db.Column(db.String(500), comment='数据手册 URL')
    
    category = db.relationship('Category', foreign_keys=[category_id], back_populates='spare_parts')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], back_populates='spare_parts')
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id], back_populates='spare_parts')
    warehouse_location = db.relationship('WarehouseLocation', foreign_keys=[location_id], back_populates='spare_parts')
    batches = db.relationship('Batch', foreign_keys='Batch.spare_part_id', back_populates='spare_part', lazy='dynamic')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.spare_part_id', back_populates='spare_part', lazy='dynamic')
    inventory_records = db.relationship('InventoryRecord', back_populates='spare_part', lazy='dynamic')
    
    def update_stock_status(self):
        """更新库存状态并触发预警"""
        old_status = self.stock_status
        
        # 更新库存状态（safety_stock 优先于 min_stock）
        if self.current_stock == 0:
            self.stock_status = 'out'  # 缺货
        elif self.safety_stock and self.current_stock <= self.safety_stock:
            self.stock_status = 'low'  # 低于安全库存
        elif self.current_stock <= self.min_stock:
            self.stock_status = 'low'  # 低库存
        elif self.max_stock and self.current_stock >= self.max_stock:
            self.stock_status = 'overstocked'  # 超储
        else:
            self.stock_status = 'normal'  # 正常
        
        # 如果状态发生变化且不是变为正常，触发预警
        if old_status != self.stock_status and self.stock_status != 'normal':
            self._trigger_alert()
    
    def _trigger_alert(self):
        """触发库存预警"""
        from app.models.system import Alert, Notification
        from app.models.user import User
        from app.models.role import Role
        from app.utils.email_service import email_service
        from flask import current_app
        import logging
        
        logger = logging.getLogger(__name__)
        
        # 状态映射
        status_map = {
            'low': ('低库存预警', 'warning'),
            'out': ('缺货预警', 'danger'),
            'overstocked': ('超储预警', 'info')
        }
        
        title, level = status_map.get(self.stock_status, ('库存预警', 'warning'))
        
        # 创建告警记录
        alert = Alert(
            alert_type='stock',
            title=f"{title}: {self.part_code}",
            message=f"备件 {self.part_code} - {self.name} 当前库存：{self.current_stock}, 库存状态：{title}",
            level=level,
            status='active',
            related_object_id=self.id,
            related_object_type='spare_part'
        )
        
        from app.extensions import db
        db.session.add(alert)
        
        # 获取所有需要接收预警的用户
        # 1. 系统管理员
        admin_users = User.query.filter_by(is_admin=True, is_active=True).all()
        # 2. 仓库管理员
        warehouse_admin_role = Role.query.filter_by(name='warehouse_manager').first()
        warehouse_admins = []
        if warehouse_admin_role:
            warehouse_admins = User.query.filter_by(role_id=warehouse_admin_role.id, is_active=True).all()
        # 3. 采购员
        purchaser_role = Role.query.filter_by(name='purchaser').first()
        purchasers = []
        if purchaser_role:
            purchasers = User.query.filter_by(role_id=purchaser_role.id, is_active=True).all()
        
        # 合并所有需要通知的用户
        notify_users = set(admin_users + warehouse_admins + purchasers)
        
        # 为每个用户创建通知并发送邮件
        for user in notify_users:
            if user.email:
                # 创建系统内通知
                notification = Notification(
                    user_id=user.id,
                    title=title,
                    message=f"备件 {self.part_code} - {self.name} 触发{title}，当前库存：{self.current_stock}",
                    type='stock_alert',
                    level=level,
                    related_object_id=self.id,
                    related_object_type='spare_part'
                )
                db.session.add(notification)
                
                # 发送邮件通知 - 使用用户自己的邮箱配置
                try:
                    email_service.send_stock_alert(user, self, user_id=user.id)
                except Exception as e:
                    logger.error(f"发送库存预警邮件给用户 {user.username} 失败：{str(e)}")
        
        logger.info(f"库存预警已触发：{self.part_code}, 状态：{self.stock_status}，通知用户数：{len(notify_users)}")
    
    def __repr__(self):
        return f'<SparePart {self.part_code}>'

    # ──────────────────────────────────────────────
    # 并发安全的库存更新
    # ──────────────────────────────────────────────

    @classmethod
    def safe_stock_update(cls, part_id: int, delta: int, reason: str = '',
                          operator_id: int = None, warehouse_id: int = None,
                          order_no: str = ''):
        """
        使用 SELECT FOR UPDATE (悲观锁) 安全修改库存。

        Args:
            part_id: 备件 ID
            delta: 库存变更量（正数=入库，负数=出库）
            reason: 变更原因描述
            operator_id: 操作人 ID
            warehouse_id: 仓库 ID
            order_no: 关联单据编号

        Raises:
            StockInsufficientError: 出库时库存不足
        """
        from app.extensions import db
        # SELECT FOR UPDATE — 行级排他锁，防止并发读写
        part = db.session.query(cls).filter(
            cls.id == part_id
        ).with_for_update().first()

        if not part:
            from app.utils.exceptions import NotFoundError
            raise NotFoundError(f'备件不存在 (ID: {part_id})')

        new_stock = part.current_stock + delta
        if new_stock < 0:
            from app.utils.exceptions import StockInsufficientError
            raise StockInsufficientError(
                f'库存不足：当前 {part.current_stock}，试图扣减 {abs(delta)}',
                data={'current': part.current_stock, 'requested': abs(delta)}
            )

        part.current_stock = new_stock
        part.version = (part.version or 1) + 1  # 乐观锁版本号递增
        part.update_stock_status()
        # 不在此 commit，由调用方统一提交事务

    @classmethod
    def optimistic_update(cls, part_id: int, expected_version: int):
        """
        使用乐观锁更新备件（CAS 模式）。
        调用方需在 with_for_update() 锁内读取 version 后调用此方法做最终校验。

        如果版本不匹配，抛出 ConcurrentModificationError。

        用法：
            part = SparePart.query.filter_by(id=pid).with_for_update().first()
            SparePart.optimistic_update(pid, expected_version=client_version)
            # ... 修改字段 ...
            db.session.commit()
        """
        from app.extensions import db
        from app.utils.exceptions import ConcurrentModificationError
        part = db.session.query(cls).filter(cls.id == part_id).with_for_update().first()
        if not part:
            from app.utils.exceptions import NotFoundError
            raise NotFoundError(f'备件不存在 (ID: {part_id})')
        if part.version != expected_version:
            raise ConcurrentModificationError(
                f'数据已被其他用户修改（当前版本: {part.version}，期望版本: {expected_version}），请刷新后重试'
            )
