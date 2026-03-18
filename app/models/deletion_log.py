from app.extensions import db
from datetime import datetime


class DeletionLog(db.Model):
    __tablename__ = 'deletion_log'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False, comment='表名')
    record_id = db.Column(db.Integer, nullable=False, comment='记录 ID')
    record_data = db.Column(db.Text, nullable=False, comment='记录数据')
    deleted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='删除人 ID')
    deleted_at = db.Column(db.DateTime, default=datetime.now, comment='删除时间')
    reason = db.Column(db.Text, comment='删除原因')
    ip_address = db.Column(db.String(50), comment='IP 地址')
    can_restore = db.Column(db.Boolean, default=True, comment='是否可恢复')
    restored = db.Column(db.Boolean, default=False, comment='是否已恢复')
    restored_at = db.Column(db.DateTime, comment='恢复时间')
    restored_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='恢复人 ID')
    
    deleter = db.relationship('User', foreign_keys=[deleted_by], backref='deleted_records')
    restorer = db.relationship('User', foreign_keys=[restored_by], backref='restored_records')
    
    def __repr__(self):
        return f'<DeletionLog {self.table_name}:{self.record_id}>'
