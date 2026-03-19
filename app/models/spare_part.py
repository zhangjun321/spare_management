from app.extensions import db
from datetime import datetime


class SparePart(db.Model):
    __tablename__ = 'spare_part'
    
    id = db.Column(db.Integer, primary_key=True)
    part_code = db.Column(db.String(50), unique=True, nullable=False, comment='备件代码')
    name = db.Column(db.String(200), nullable=False, comment='备件名称')
    specification = db.Column(db.String(200), comment='规格型号')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), comment='分类 ID')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    current_stock = db.Column(db.Integer, nullable=False, default=0, comment='当前库存')
    stock_status = db.Column(db.String(20), nullable=False, default='normal', comment='库存状态')
    min_stock = db.Column(db.Integer, default=0, comment='最低库存')
    max_stock = db.Column(db.Integer, comment='最高库存')
    unit = db.Column(db.String(20), comment='单位')
    unit_price = db.Column(db.Numeric(10, 2), comment='单价')
    location = db.Column(db.String(200), comment='存放位置')
    image_url = db.Column(db.String(500), comment='图片 URL')
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    brand = db.Column(db.String(100), index=True, comment='品牌')
    barcode = db.Column(db.String(100), unique=True, index=True, comment='条形码')
    safety_stock = db.Column(db.Integer, default=0, comment='安全库存')
    reorder_point = db.Column(db.Integer, comment='再订货点')
    last_purchase_price = db.Column(db.Numeric(10, 2), comment='最近采购价')
    currency = db.Column(db.String(10), default='CNY', comment='币种')
    warranty_period = db.Column(db.Integer, comment='质保期 (月)')
    last_purchase_date = db.Column(db.DateTime, comment='最后采购日期')
    technical_params = db.Column(db.JSON, comment='技术参数')
    datasheet_url = db.Column(db.String(500), comment='数据手册 URL')
    
    category = db.relationship('Category', foreign_keys=[category_id], backref='category_spare_parts')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_spare_parts')
    batches = db.relationship('Batch', foreign_keys='Batch.spare_part_id', backref='batch_spare_part', lazy='dynamic')
    transactions = db.relationship('Transaction', foreign_keys='Transaction.spare_part_id', lazy='dynamic')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.spare_part_id', lazy='dynamic')
    
    def update_stock_status(self):
        """更新库存状态并触发预警"""
        old_status = self.stock_status
        
        # 更新库存状态
        if self.current_stock == 0:
            self.stock_status = 'out'  # 缺货
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
        
        # 获取admin超级管理员
        admin_user = User.query.filter_by(username='admin', is_admin=True, is_active=True).first()
        
        # 只为admin超级管理员创建通知并发送邮件
        if admin_user and admin_user.email:
            # 创建系统内通知
            notification = Notification(
                user_id=admin_user.id,
                title=title,
                message=f"备件 {self.part_code} - {self.name} 触发{title}，当前库存：{self.current_stock}",
                type='stock_alert',
                level=level,
                related_object_id=self.id,
                related_object_type='spare_part'
            )
            db.session.add(notification)
            
            # 发送邮件通知 - 使用管理员自己的邮箱配置
            try:
                email_service.send_stock_alert(admin_user, self, user_id=admin_user.id)
            except Exception as e:
                logger.error(f"发送库存预警邮件失败：{str(e)}")
        
        logger.info(f"库存预警已触发：{self.part_code}, 状态：{self.stock_status}")
    
    def __repr__(self):
        return f'<SparePart {self.part_code}>'
