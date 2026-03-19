"""
用户邮箱配置路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.system import UserEmailConfig
from app.forms.user_email import UserEmailConfigForm
from app.utils.email_service import EmailService
from app.utils.decorators import permission_required

user_email_bp = Blueprint('user_email', __name__, template_folder='../templates/user_email')


@user_email_bp.route('/my-email-config', methods=['GET', 'POST'])
@login_required
def my_email_config():
    """我的邮箱配置 - 每个管理员配置自己的邮箱"""
    config = UserEmailConfig.query.filter_by(user_id=current_user.id).first()
    
    form = UserEmailConfigForm()
    
    if form.validate_on_submit():
        if config:
            # 更新现有配置
            config.smtp_server = form.smtp_server.data
            config.smtp_port = form.smtp_port.data
            config.username = form.username.data
            config.password = form.password.data
            config.sender_email = form.sender_email.data
            config.sender_name = form.sender_name.data
            config.use_tls = form.use_tls.data
            config.is_active = form.is_active.data
        else:
            # 创建新配置
            config = UserEmailConfig(
                user_id=current_user.id,
                smtp_server=form.smtp_server.data,
                smtp_port=form.smtp_port.data,
                username=form.username.data,
                password=form.password.data,
                sender_email=form.sender_email.data,
                sender_name=form.sender_name.data,
                use_tls=form.use_tls.data,
                is_active=form.is_active.data
            )
            db.session.add(config)
        
        db.session.commit()
        flash('邮箱配置保存成功！', 'success')
        return redirect(url_for('user_email.my_email_config'))
    
    # GET 请求时填充现有配置
    if request.method == 'GET' and config:
        form.smtp_server.data = config.smtp_server
        form.smtp_port.data = config.smtp_port
        form.username.data = config.username
        form.password.data = config.password
        form.sender_email.data = config.sender_email
        form.sender_name.data = config.sender_name
        form.use_tls.data = config.use_tls
        form.is_active.data = config.is_active
    
    return render_template('user_email/my_config.html', form=form, has_config=config is not None)


@user_email_bp.route('/test-email', methods=['POST'])
@login_required
def test_email():
    """测试邮箱连接"""
    from flask import request
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 检查是否要发送测试邮件
    send_email = request.form.get('send_email') == '1'
    
    # 获取表单数据
    form = UserEmailConfigForm()
    if form.validate_on_submit():
        logger.info(f"表单验证通过，使用表单数据测试")
        logger.info(f"用户名：{form.username.data}")
        logger.info(f"密码长度：{len(form.password.data) if form.password.data else 0}")
        
        # 使用表单数据进行测试
        temp_config = UserEmailConfig(
            user_id=current_user.id,
            smtp_server=form.smtp_server.data,
            smtp_port=form.smtp_port.data,
            username=form.username.data,
            password=form.password.data,
            sender_email=form.sender_email.data,
            sender_name=form.sender_name.data,
            use_tls=form.use_tls.data,
            is_active=True
        )
        
        test_service = EmailService()
        test_service.config = temp_config
        success, message = test_service.test_connection(send_test_email=send_email)
    else:
        logger.info(f"表单验证失败，使用数据库配置")
        
        # 使用数据库中的配置
        config = UserEmailConfig.query.filter_by(user_id=current_user.id).first()
        if config:
            test_service = EmailService()
            test_service.config = config
            if send_email:
                success, message = test_service.test_connection(send_test_email=True)
            else:
                success, message = test_service.test_connection()
        else:
            success, message = False, '未找到邮箱配置'
    
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
    
    return redirect(url_for('user_email.my_email_config'))


@user_email_bp.route('/admin/email-configs')
@login_required
def admin_email_configs():
    """管理员邮箱配置管理 - 系统管理员查看所有管理员的邮箱配置"""
    # 只有admin超级管理员能访问
    if current_user.username != 'admin' or not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # 获取所有管理员及其邮箱配置
    from app.models.user import User
    admins = User.query.filter_by(is_admin=True, is_active=True).all()
    
    return render_template('user_email/admin_configs.html', admins=admins)
