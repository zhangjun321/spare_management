"""
质检管理模型
"""

from datetime import datetime
from app.extensions import db


class QualityCheck(db.Model):
    """质检单"""
    
    __tablename__ = 'quality_check'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='质检单 ID')
    check_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='质检单号')
    
    # 关联信息
    inbound_order_id = db.Column(db.Integer, db.ForeignKey('inbound_order_v3.id'), nullable=False, comment='入库单 ID')
    
    # 质检类型
    check_type = db.Column(db.String(20), nullable=False, default='inbound', comment='质检类型')
    inspection_type = db.Column(db.String(20), nullable=False, comment='检验类型：抽检/全检')
    check_method = db.Column(db.String(20), default='sampling', comment='质检方式')
    sample_ratio = db.Column(db.Numeric(5, 2), comment='抽检比例')
    sample_size = db.Column(db.Integer, comment='抽样数量')
    
    # 状态管理
    status = db.Column(db.String(20), default='pending', comment='质检状态')
    
    # 质检结果
    total_quantity = db.Column(db.Numeric(12, 4), comment='总数量')
    qualified_count = db.Column(db.Numeric(12, 4), comment='合格数量')
    unqualified_count = db.Column(db.Numeric(12, 4), comment='不合格数量')
    pass_rate = db.Column(db.Numeric(5, 2), comment='合格率')
    defect_description = db.Column(db.Text, comment='缺陷描述')
    inspection_report = db.Column(db.Text, comment='质检报告')
    result = db.Column(db.String(20), comment='质检结果')
    
    # 质检信息
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='质检员')
    started_at = db.Column(db.DateTime, comment='开始时间')
    started_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='开始人')
    inspection_date = db.Column(db.DateTime, comment='质检日期')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='完成人')
    cancelled_at = db.Column(db.DateTime, comment='取消时间')
    cancelled_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='取消人')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 备注
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    inbound_order = db.relationship('InboundOrderV3', backref='quality_checks')
    inspector = db.relationship('User', foreign_keys=[inspector_id])
    starter = db.relationship('User', foreign_keys=[started_by])
    completer = db.relationship('User', foreign_keys=[completed_by])
    items = db.relationship('QualityCheckItem', back_populates='check', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<QualityCheck {self.check_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'check_no': self.check_no,
            'inbound_order_id': self.inbound_order_id,
            'inbound_order_no': self.inbound_order.order_no if self.inbound_order else None,
            'check_type': self.check_type,
            'inspection_type': self.inspection_type,
            'check_method': self.check_method,
            'sample_ratio': float(self.sample_ratio) if self.sample_ratio else 0,
            'sample_size': self.sample_size,
            'status': self.status,
            'total_quantity': float(self.total_quantity) if self.total_quantity else 0,
            'qualified_count': float(self.qualified_count) if self.qualified_count else 0,
            'unqualified_count': float(self.unqualified_count) if self.unqualified_count else 0,
            'pass_rate': float(self.pass_rate) if self.pass_rate else 0,
            'defect_description': self.defect_description,
            'inspection_report': self.inspection_report,
            'result': self.result,
            'inspector_id': self.inspector_id,
            'inspector_name': self.inspector.name if self.inspector else None,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'started_by': self.started_by,
            'inspection_date': self.inspection_date.strftime('%Y-%m-%d %H:%M:%S') if self.inspection_date else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'completed_by': self.completed_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'remark': self.remark
        }
    
    @staticmethod
    def generate_check_no():
        """生成质检单号"""
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        # 获取当天的最大单号
        last_check = QualityCheck.query.filter(
            QualityCheck.check_no.like(f'QC{date_str}%')
        ).order_by(QualityCheck.check_no.desc()).first()
        
        if last_check:
            # 提取序号
            import re
            match = re.search(r'QC(\d{8})(\d{4})', last_check.check_no)
            if match:
                last_no = int(match.group(2))
                new_no = last_no + 1
            else:
                new_no = 1
        else:
            new_no = 1
        
        return f'QC{date_str}{new_no:04d}'
    
    def calculate_result(self):
        """计算质检结果"""
        if not self.total_quantity or self.total_quantity == 0:
            self.result = 'pending'
            return
        
        unqualified_rate = float(self.unqualified_count) / float(self.total_quantity)
        
        if self.unqualified_count == 0:
            self.result = 'qualified'  # 合格
        elif unqualified_rate < 0.05:
            self.result = 'conditional'  # 让步接收
        else:
            self.result = 'unqualified'  # 不合格
        
        # 计算合格率
        self.pass_rate = round((1 - unqualified_rate) * 100, 2)


class QualityCheckItem(db.Model):
    """质检明细"""
    
    __tablename__ = 'quality_check_item'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='质检明细 ID')
    check_id = db.Column(db.Integer, db.ForeignKey('quality_check.id'), nullable=False, index=True, comment='质检单 ID')
    inbound_item_id = db.Column(db.Integer, db.ForeignKey('inbound_order_item_v3.id'), comment='入库明细 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    
    # 数量信息
    expected_quantity = db.Column(db.Numeric(12, 4), comment='应检数量')
    checked_quantity = db.Column(db.Numeric(12, 4), comment='实检数量')
    qualified_quantity = db.Column(db.Numeric(12, 4), comment='合格数量')
    unqualified_quantity = db.Column(db.Numeric(12, 4), comment='不合格数量')
    unit = db.Column(db.String(20), comment='单位')
    
    # 缺陷信息
    defect_type = db.Column(db.String(50), comment='缺陷类型')
    defect_level = db.Column(db.String(20), comment='缺陷等级')
    defect_description = db.Column(db.Text, comment='缺陷描述')
    
    # 检验员
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='检验员')
    inspected_at = db.Column(db.DateTime, comment='检验时间')
    
    # 状态
    status = db.Column(db.String(20), default='pending', comment='状态')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    check = db.relationship('QualityCheck', back_populates='items')
    inbound_item = db.relationship('InboundOrderItemV3')
    part = db.relationship('SparePart')
    inspector = db.relationship('User', foreign_keys=[inspector_id])
    
    def __repr__(self):
        return f'<QualityCheckItem {self.id}@{self.check_id}>'
    
    def to_dict(self):
        # 计算合格率
        pass_rate = 0
        if self.checked_quantity and self.checked_quantity > 0:
            pass_rate = (float(self.qualified_quantity) / float(self.checked_quantity)) * 100
        
        return {
            'id': self.id,
            'check_id': self.check_id,
            'inbound_item_id': self.inbound_item_id,
            'part_id': self.part_id,
            'part_name': self.part.name if self.part else None,
            'specification': self.part.specification if self.part else None,
            'expected_quantity': float(self.expected_quantity) if self.expected_quantity else 0,
            'checked_quantity': float(self.checked_quantity) if self.checked_quantity else 0,
            'qualified_quantity': float(self.qualified_quantity) if self.qualified_quantity else 0,
            'unqualified_quantity': float(self.unqualified_quantity) if self.unqualified_quantity else 0,
            'pass_rate': pass_rate,
            'unit': self.unit,
            'defect_type': self.defect_type,
            'defect_level': self.defect_level,
            'defect_description': self.defect_description,
            'inspector_id': self.inspector_id,
            'inspector_name': self.inspector.name if self.inspector else None,
            'inspected_at': self.inspected_at.strftime('%Y-%m-%d %H:%M:%S') if self.inspected_at else None,
            'status': self.status,
            'remark': self.remark
        }


class QualityCheckStandard(db.Model):
    """质检标准"""
    
    __tablename__ = 'quality_check_standard'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='质检标准 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    part_code = db.Column(db.String(50), nullable=False, index=True, comment='备件编码')
    
    # 检验项目
    check_item = db.Column(db.String(100), nullable=False, comment='检验项目')
    check_method = db.Column(db.String(50), comment='检验方法')
    
    # 标准值
    standard_value = db.Column(db.String(100), comment='标准值')
    min_value = db.Column(db.Numeric(12, 4), comment='最小值')
    max_value = db.Column(db.Numeric(12, 4), comment='最大值')
    unit = db.Column(db.String(20), comment='单位')
    
    # 严重程度
    severity_level = db.Column(db.String(20), default='normal', comment='严重程度')
    
    # 启用状态
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    part = db.relationship('SparePart')
    
    def __repr__(self):
        return f'<QualityCheckStandard {self.part_code}-{self.check_item}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'part_code': self.part_code,
            'part_name': self.part.name if self.part else None,
            'check_item': self.check_item,
            'check_method': self.check_method,
            'standard_value': self.standard_value,
            'min_value': float(self.min_value) if self.min_value else None,
            'max_value': float(self.max_value) if self.max_value else None,
            'unit': self.unit,
            'severity_level': self.severity_level,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
