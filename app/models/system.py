from app.extensions import db
from datetime import datetime


class Tag(db.Model):
    __tablename__ = 'tag'
    
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(50), unique=True, nullable=False, comment='标签名称')
    tag_type = db.Column(db.String(20), comment='标签类型')
    color = db.Column(db.String(20), comment='颜色')
    description = db.Column(db.String(200), comment='描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    def __repr__(self):
        return f'<Tag {self.tag_name}>'


class Alert(db.Model):
    __tablename__ = 'alert'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(20), nullable=False, comment='告警类型')
    title = db.Column(db.String(200), nullable=False, comment='告警标题')
    message = db.Column(db.Text, nullable=False, comment='告警内容')
    level = db.Column(db.String(20), default='info', comment='告警级别')
    status = db.Column(db.String(20), default='active', comment='状态')
    related_object_id = db.Column(db.Integer, comment='关联对象 ID')
    related_object_type = db.Column(db.String(20), comment='关联对象类型')
    triggered_at = db.Column(db.DateTime, default=datetime.now, comment='触发时间')
    acknowledged_at = db.Column(db.DateTime, comment='确认时间')
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='确认人 ID')
    resolved_at = db.Column(db.DateTime, comment='解决时间')
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='解决人 ID')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    acknowledger = db.relationship('User', foreign_keys=[acknowledged_by], backref='acknowledged_alerts')
    resolver = db.relationship('User', foreign_keys=[resolved_by], backref='resolved_alerts')
    
    def __repr__(self):
        return f'<Alert {self.title}>'


class AlertRule(db.Model):
    __tablename__ = 'alert_rule'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False, comment='规则名称')
    rule_type = db.Column(db.String(20), nullable=False, comment='规则类型')
    condition = db.Column(db.Text, nullable=False, comment='条件')
    threshold = db.Column(db.String(50), comment='阈值')
    alert_level = db.Column(db.String(20), default='warning', comment='告警级别')
    notification_methods = db.Column(db.String(100), comment='通知方式')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    def __repr__(self):
        return f'<AlertRule {self.rule_name}>'


class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户 ID')
    title = db.Column(db.String(200), nullable=False, comment='通知标题')
    message = db.Column(db.Text, nullable=False, comment='通知内容')
    type = db.Column(db.String(20), comment='通知类型')
    level = db.Column(db.String(20), default='info', comment='通知级别')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    related_object_id = db.Column(db.Integer, comment='关联对象 ID')
    related_object_type = db.Column(db.String(20), comment='关联对象类型')
    read_at = db.Column(db.DateTime, comment='阅读时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    user = db.relationship('User', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class EmailConfig(db.Model):
    __tablename__ = 'email_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_name = db.Column(db.String(100), comment='配置名称')
    smtp_server = db.Column(db.String(200), nullable=False, comment='SMTP 服务器')
    smtp_port = db.Column(db.Integer, nullable=False, comment='SMTP 端口')
    use_tls = db.Column(db.Boolean, default=True, comment='是否使用 TLS')
    username = db.Column(db.String(100), nullable=False, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='密码')
    sender_email = db.Column(db.String(100), nullable=False, comment='发件人邮箱')
    sender_name = db.Column(db.String(100), comment='发件人名称')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认配置')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    last_test_at = db.Column(db.DateTime, comment='最后测试时间')
    last_test_result = db.Column(db.Boolean, comment='最后测试结果')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<EmailConfig {self.sender_email}>'


class UserEmailConfig(db.Model):
    """用户邮箱配置 - 支持每个管理员配置自己的邮箱"""
    __tablename__ = 'user_email_config'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户 ID')
    smtp_server = db.Column(db.String(200), nullable=False, comment='SMTP 服务器')
    smtp_port = db.Column(db.Integer, nullable=False, comment='SMTP 端口')
    use_tls = db.Column(db.Boolean, default=True, comment='是否使用 TLS')
    username = db.Column(db.String(100), nullable=False, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='密码')
    sender_email = db.Column(db.String(100), nullable=False, comment='发件人邮箱')
    sender_name = db.Column(db.String(100), comment='发件人名称')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('email_config', uselist=False))
    
    def __repr__(self):
        return f'<UserEmailConfig {self.user.username} - {self.sender_email}>'
