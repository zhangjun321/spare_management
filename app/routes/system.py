"""
系统管理模块路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.system import EmailConfig
from app.models.user import User
from app.forms.system import EmailConfigForm, SystemSettingsForm
from app.utils.email_service import email_service, EmailService
from app.utils.decorators import permission_required

system_bp = Blueprint('system', __name__, template_folder='../templates/system')


@system_bp.route('/')
@login_required
@permission_required('system', 'read')
def index():
    """系统设置首页"""
    return render_template('system/index.html')


@system_bp.route('/email-config', methods=['GET', 'POST'])
@login_required
@permission_required('system', 'update')
def email_config():
    """邮件配置"""
    import logging
    logger = logging.getLogger(__name__)
    
    config = EmailConfig.query.filter_by(is_active=True).first()
    
    form = EmailConfigForm()
    
    if form.validate_on_submit():
        logger.info(f"表单验证通过，保存配置")
        logger.info(f"用户名：{form.username.data}")
        logger.info(f"密码长度：{len(form.password.data) if form.password.data else 0}")
        logger.info(f"密码：{repr(form.password.data)}")
        
        # 如果已有配置，先停用
        if config:
            config.is_active = False
            config.is_default = False
        
        # 创建新配置
        new_config = EmailConfig(
            config_name='默认配置',
            smtp_server=form.smtp_server.data,
            smtp_port=form.smtp_port.data,
            username=form.username.data,
            password=form.password.data,
            sender_email=form.sender_email.data,
            sender_name=form.sender_name.data,
            use_tls=form.use_tls.data,
            is_default=True,
            is_active=True
        )
        
        db.session.add(new_config)
        db.session.commit()
        
        logger.info(f"配置保存成功，ID: {new_config.id}")
        
        flash('邮件配置保存成功！', 'success')
        return redirect(url_for('system.email_config'))
    
    # GET 请求时填充现有配置
    if request.method == 'GET' and config:
        form.config_name.data = config.config_name or '默认配置'
        form.smtp_server.data = config.smtp_server
        form.smtp_port.data = config.smtp_port
        form.username.data = config.username
        form.password.data = config.password
        form.sender_email.data = config.sender_email
        form.sender_name.data = config.sender_name
        form.use_tls.data = config.use_tls
        form.is_active.data = config.is_active
    
    return render_template('system/email_config.html', form=form, has_config=config is not None)


@system_bp.route('/test-email', methods=['POST'])
@login_required
@permission_required('system', 'update')
def test_email():
    """测试邮件连接"""
    from flask import request
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 检查是否要发送测试邮件
    send_email = request.form.get('send_email') == '1'
    
    # 先保存配置（如果表单数据有效）
    form = EmailConfigForm()
    if form.validate_on_submit():
        logger.info(f"表单验证通过，使用表单数据测试")
        logger.info(f"用户名：{form.username.data}")
        logger.info(f"密码长度：{len(form.password.data) if form.password.data else 0}")
        logger.info(f"密码：{repr(form.password.data)}")
        
        # 使用表单数据进行测试
        temp_config = EmailConfig(
            config_name=form.config_name.data or '临时配置',
            smtp_server=form.smtp_server.data,
            smtp_port=form.smtp_port.data,
            username=form.username.data,
            password=form.password.data,
            sender_email=form.sender_email.data,
            sender_name=form.sender_name.data,
            use_tls=form.use_tls.data,
            is_default=True,
            is_active=True
        )
        
        test_service = EmailService()
        test_service.config = temp_config
        success, message = test_service.test_connection(send_test_email=send_email)
    else:
        logger.info(f"表单验证失败，使用数据库配置")
        for field, errors in form.errors.items():
            logger.error(f"表单错误 - {field}: {errors}")
        
        # 使用数据库中的配置
        config = EmailConfig.query.filter_by(is_active=True).first()
        if config:
            test_service = EmailService()
            test_service.config = config
            if send_email:
                success, message = test_service.test_connection(send_test_email=True)
            else:
                success, message = test_service.test_connection()
        else:
            success, message = False, '未找到邮件配置'
    
    # 如果是 AJAX 请求，返回 JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': success,
            'message': message
        })
    
    # 否则重定向并显示 flash 消息
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('system.email_config'))


@system_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('system', 'update')
def settings():
    """系统设置"""
    form = SystemSettingsForm()
    
    if form.validate_on_submit():
        # 这里可以将设置保存到数据库或配置文件
        # 暂时只保存到 session
        from flask import session
        
        session['system_settings'] = {
            'enable_stock_alert': form.enable_stock_alert.data,
            'alert_low_stock': form.alert_low_stock.data,
            'alert_out_of_stock': form.alert_out_of_stock.data,
            'alert_overstock': form.alert_overstock.data,
            'notify_by_email': form.notify_by_email.data,
            'notify_by_system': form.notify_by_system.data
        }
        
        flash('系统设置保存成功！', 'success')
        return redirect(url_for('system.settings'))
    
    return render_template('system/settings.html', form=form)


@system_bp.route('/api/get-admin-emails')
@login_required
@permission_required('system', 'read')
def get_admin_emails():
    """获取管理员邮箱列表"""
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    emails = [admin.email for admin in admins if admin.email]
    
    return jsonify({'emails': emails})
