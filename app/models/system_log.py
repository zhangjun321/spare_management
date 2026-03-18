from app.extensions import db
from datetime import datetime


class SystemLog(db.Model):
    __tablename__ = 'system_log'
    
    id = db.Column(db.Integer, primary_key=True)
    log_type = db.Column(db.String(20), nullable=False, comment='日志类型')
    action = db.Column(db.String(100), nullable=False, comment='操作')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='用户 ID')
    username = db.Column(db.String(50), comment='用户名')
    ip_address = db.Column(db.String(50), comment='IP 地址')
    user_agent = db.Column(db.String(500), comment='User-Agent')
    request_method = db.Column(db.String(10), comment='请求方法')
    request_url = db.Column(db.String(500), comment='请求 URL')
    request_data = db.Column(db.Text, comment='请求数据')
    response_status = db.Column(db.Integer, comment='响应状态')
    response_message = db.Column(db.Text, comment='响应消息')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    user = db.relationship('User', backref='system_logs')
    
    def __repr__(self):
        return f'<SystemLog {self.action}>'
