from app.extensions import db
from datetime import datetime


class EquipmentStatusHistory(db.Model):
    """设备状态变更历史记录"""
    __tablename__ = 'equipment_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    old_status = db.Column(db.String(20), comment='变更前状态')
    new_status = db.Column(db.String(20), comment='变更后状态')
    change_reason = db.Column(db.String(500), comment='变更原因')
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='变更人 ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<EquipmentStatusHistory {self.id}>'


class EquipmentChecklist(db.Model):
    """设备点检表"""
    __tablename__ = 'equipment_checklist'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    check_date = db.Column(db.Date, nullable=False)
    check_items = db.Column(db.JSON, comment='检查项目')
    check_result = db.Column(db.String(50), comment='检查结果：normal/abnormal')
    issues_found = db.Column(db.Text, comment='发现的问题')
    check_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    remarks = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    equipment = db.relationship('Equipment', backref='checklists')
    
    def __repr__(self):
        return f'<EquipmentChecklist {self.id}>'


class EquipmentAttachment(db.Model):
    """设备附件（照片、文档等）"""
    __tablename__ = 'equipment_attachment'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), comment='文件类型：image/pdf/doc/excel')
    file_size = db.Column(db.Integer, comment='文件大小（字节）')
    description = db.Column(db.String(500), comment='描述')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    equipment = db.relationship('Equipment', backref='attachments')
    
    def __repr__(self):
        return f'<EquipmentAttachment {self.id}>'


class EquipmentTag(db.Model):
    """设备标签"""
    __tablename__ = 'equipment_tag'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    color = db.Column(db.String(20), default='#3B82F6', comment='标签颜色')
    description = db.Column(db.String(500), comment='描述')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    equipments = db.relationship(
        'Equipment',
        secondary='equipment_tag_association',
        backref='tags'
    )
    
    def __repr__(self):
        return f'<EquipmentTag {self.name}>'


class EquipmentTagAssociation(db.Model):
    """设备-标签关联表"""
    __tablename__ = 'equipment_tag_association'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('equipment_tag.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class EquipmentMaintenancePlan(db.Model):
    """设备保养计划"""
    __tablename__ = 'equipment_maintenance_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    plan_name = db.Column(db.String(200), nullable=False)
    plan_type = db.Column(db.String(50), comment='保养类型：daily/weekly/monthly/quarterly/yearly')
    schedule_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    equipment = db.relationship('Equipment', backref='maintenance_plans')
    
    def __repr__(self):
        return f'<EquipmentMaintenancePlan {self.plan_name}>'