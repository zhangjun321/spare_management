"""
系统设置表单
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, NumberRange, Length


class EmailConfigForm(FlaskForm):
    """邮件配置表单"""
    
    config_name = StringField('配置名称', validators=[
        Optional(),
        Length(max=100)
    ], description='例如：默认配置')
    
    smtp_server = StringField('SMTP 服务器', validators=[
        DataRequired(message='请输入 SMTP 服务器'),
        Length(max=200)
    ], description='例如：smtp.qq.com')
    
    smtp_port = IntegerField('SMTP 端口', validators=[
        DataRequired(message='请输入 SMTP 端口'),
        NumberRange(min=1, max=65535, message='端口范围 1-65535')
    ], description='SSL 加密通常为 465 或 587')
    
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(max=100)
    ], description='SMTP 登录用户名')
    
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(max=255)
    ], description='SMTP 登录密码或授权码')
    
    sender_email = StringField('发件人邮箱', validators=[
        DataRequired(message='请输入发件人邮箱'),
        Email(message='邮箱格式不正确'),
        Length(max=100)
    ])
    
    sender_name = StringField('发件人名称', validators=[
        Optional(),
        Length(max=100)
    ], description='显示在邮件中的发件人名称')
    
    use_tls = BooleanField('使用 SSL/TLS 加密', default=True)
    
    is_active = BooleanField('启用此配置', default=True)
    
    submit = SubmitField('保存配置')


class SystemSettingsForm(FlaskForm):
    """系统设置表单"""
    
    # 库存预警设置
    enable_stock_alert = BooleanField('启用库存预警', default=True)
    alert_low_stock = BooleanField('低库存预警', default=True)
    alert_out_of_stock = BooleanField('缺货预警', default=True)
    alert_overstock = BooleanField('超储预警', default=True)
    
    # 通知设置
    notify_by_email = BooleanField('邮件通知', default=True)
    notify_by_system = BooleanField('系统内通知', default=True)
    
    submit = SubmitField('保存设置')
