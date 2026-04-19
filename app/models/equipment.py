from app.extensions import db
from datetime import datetime


class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_code = db.Column(db.String(50), unique=True, nullable=False, comment='设备代码')
    name = db.Column(db.String(200), nullable=False, comment='设备名称')
    model = db.Column(db.String(100), comment='型号')
    series = db.Column(db.String(20), comment='设备系列（FS/MT/CS/MB/FG/PB/RF）')
    category = db.Column(db.String(50), comment='类别')
    manufacturer = db.Column(db.String(200), default='同方威视', comment='生产厂家')
    serial_number = db.Column(db.String(100), comment='出厂编号')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), comment='使用部门 ID')
    location = db.Column(db.String(200), comment='安装位置')
    install_date = db.Column(db.Date, comment='安装日期')
    status = db.Column(db.String(20), default='running', comment='状态（running/stopped/maintenance/scrapped）')
    purchase_date = db.Column(db.Date, comment='购买日期')
    warranty_expiry = db.Column(db.Date, comment='保修到期日期')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    purchase_price = db.Column(db.Numeric(10, 2), comment='购买价格')
    responsible_person = db.Column(db.String(100), comment='责任人')
    remark = db.Column(db.Text, comment='备注')
    latitude = db.Column(db.Numeric(10, 8), comment='纬度')
    longitude = db.Column(db.Numeric(11, 8), comment='经度')
    map_address = db.Column(db.String(500), comment='地图地址')
    site_name = db.Column(db.String(100), comment='站点名称（格式：系列-城市-序号）')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    department = db.relationship('Department', foreign_keys=[department_id], backref='department_equipments')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_equipments')
    maintenance_orders = db.relationship('MaintenanceOrder', foreign_keys='MaintenanceOrder.equipment_id', backref='maintenance_equipment', lazy='dynamic')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.equipment_id', backref='serial_equipment', lazy='dynamic')
    specs = db.relationship('EquipmentSpecs', foreign_keys='EquipmentSpecs.equipment_id', backref='spec_equipment', uselist=False)
    status_history = db.relationship('EquipmentStatusHistory', backref='equipment', cascade='all, delete-orphan', order_by='EquipmentStatusHistory.created_at.desc()')
    
    def __repr__(self):
        return f'<Equipment {self.equipment_code}>'


class EquipmentSpecs(db.Model):
    __tablename__ = 'equipment_specs'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, comment='设备 ID')
    radiation_source = db.Column(db.String(100), comment='射线源类型（电子直线加速器/X 射线管）')
    energy = db.Column(db.String(50), comment='能量（如：6 MeV、4-6 MeV）')
    penetration = db.Column(db.String(50), comment='穿透力（如：320mm 钢板）')
    resolution = db.Column(db.String(50), comment='分辨率（如：3.5mm）')
    check_speed = db.Column(db.String(50), comment='检查速度（如：120-200 辆/小时）')
    channel_size = db.Column(db.String(100), comment='通道尺寸（如：4.5m×4.5m）')
    imaging_mode = db.Column(db.String(100), comment='成像方式（双能/CT/顶视/背散射）')
    shielding_mode = db.Column(db.String(100), comment='屏蔽方式（自屏蔽/混凝土）')
    other_specs = db.Column(db.JSON, comment='其他参数')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<EquipmentSpecs {self.id}>'
