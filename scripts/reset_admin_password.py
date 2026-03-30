#!/usr/bin/env python3
"""
重置管理员密码脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db, generate_password_hash
from app.models.user import User

# 创建应用实例
app = create_app()

with app.app_context():
    # 确保所有表都已创建
    db.create_all()
    
    # 查找管理员用户
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        # 创建管理员用户
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            real_name='管理员',
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print('已创建管理员账号')
    else:
        # 重置管理员密码
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()
        print('已重置管理员密码')
    
    print('管理员账号: admin')
    print('密码: admin123')
    print('请使用此账号登录系统')
