"""
用户认证模块
处理用户登录、登出等功能
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.extensions import db, check_password_hash
from app.models.user import User
from app.models.role import Role
from app.extensions import generate_password_hash

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('请输入用户名和密码', 'warning')
            return render_template('auth/login.html')
        
        # 查找用户 (支持用户名或邮箱登录)
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')
        
        # 验证密码
        if not check_password_hash(user.password_hash, password):
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html')
        
        # 检查用户是否激活
        if not user.is_active:
            flash('账户已被禁用，请联系管理员', 'danger')
            return render_template('auth/login.html')
        
        # 更新登录信息
        user.last_login = datetime.utcnow()
        user.last_login_ip = request.remote_addr
        db.session.commit()
        
        # 登录用户
        login_user(user, remember=remember)
        
        # 存储权限到 session
        session['user_permissions'] = user.role.permissions if user.role else {}
        
        # 重定向到下一页或仪表盘
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    return render_template('auth/profile.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证旧密码
        if not check_password_hash(current_user.password_hash, old_password):
            flash('原密码错误', 'danger')
            return render_template('auth/change_password.html')
        
        # 验证新密码
        if len(new_password) < 6:
            flash('新密码长度不能少于 6 位', 'warning')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'warning')
            return render_template('auth/change_password.html')
        
        # 更新密码
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('密码修改成功', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')


# 管理员功能
@auth_bp.route('/users')
@login_required
def user_list():
    """用户列表 (仅管理员)"""
    if not current_user.has_permission('users', 'read'):
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.all()
    return render_template('auth/user_list.html', users=users)


@auth_bp.route('/user/add', methods=['GET', 'POST'])
@login_required
def user_add():
    """添加用户 (仅管理员)"""
    if not current_user.has_permission('users', 'create'):
        flash('您没有权限添加用户', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        real_name = request.form.get('real_name', '')
        phone = request.form.get('phone', '')
        role_id = request.form.get('role_id')
        department_id = request.form.get('department_id')
        
        # 验证
        if not username or not email or not password or not real_name:
            flash('请填写必填字段', 'warning')
            return render_template('auth/user_form.html', action='add')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'warning')
            return render_template('auth/user_form.html', action='add')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'warning')
            return render_template('auth/user_form.html', action='add')
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            real_name=real_name,
            phone=phone,
            role_id=int(role_id) if role_id else None,
            department_id=int(department_id) if department_id else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('用户添加成功', 'success')
        return redirect(url_for('auth.user_list'))
    
    roles = Role.query.all()
    return render_template('auth/user_form.html', action='add', user=None, roles=roles)


@auth_bp.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """编辑用户 (仅管理员)"""
    if not current_user.has_permission('users', 'update'):
        flash('您没有权限编辑用户', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        real_name = request.form.get('real_name', '')
        phone = request.form.get('phone', '')
        role_id = request.form.get('role_id')
        department_id = request.form.get('department_id')
        is_active = request.form.get('is_active', False)
        
        # 验证邮箱
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('邮箱已被其他用户使用', 'warning')
            return render_template('auth/user_form.html', action='edit', user=user)
        
        # 更新用户信息
        user.email = email
        user.real_name = real_name
        user.phone = phone
        user.role_id = int(role_id) if role_id else None
        user.department_id = int(department_id) if department_id else None
        user.is_active = is_active
        
        db.session.commit()
        
        flash('用户信息更新成功', 'success')
        return redirect(url_for('auth.user_list'))
    
    roles = Role.query.all()
    return render_template('auth/user_form.html', action='edit', user=user, roles=roles)


@auth_bp.route('/user/delete/<int:user_id>')
@login_required
def user_delete(user_id):
    """删除用户 (仅管理员)"""
    if not current_user.has_permission('users', 'delete'):
        flash('您没有权限删除用户', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己的账户', 'warning')
        return redirect(url_for('auth.user_list'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('用户删除成功', 'success')
    return redirect(url_for('auth.user_list'))
