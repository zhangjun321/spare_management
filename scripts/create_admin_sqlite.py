#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为SQLite数据库创建管理员账户
"""

import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role


def create_admin():
    """创建系统管理员账户"""
    app = create_app()
    
    with app.app_context():
        # 1. 检查并创建 admin 角色
        role = Role.query.filter_by(name='admin').first()
        
        if not role:
            # 创建 admin 角色
            role = Role(
                name='admin',
                display_name='系统管理员',
                description='拥有系统所有权限',
                is_system=True,
                permissions='{"*": ["create", "read", "update", "delete"]}'
            )
            db.session.add(role)
            db.session.commit()
            print("[OK] 创建 admin 角色成功")
        else:
            print("[OK] admin 角色已存在")
        
        # 2. 检查管理员账户是否存在
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            # 创建管理员账户
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                real_name='系统管理员',
                role_id=role.id,
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("\n[OK] 管理员账户创建成功！")
            print("=" * 60)
            print("用户名：admin")
            print("邮箱：admin@example.com")
            print("密码：admin123")
            print("=" * 60)
        else:
            # 更新现有管理员账户
            admin.email = 'admin@example.com'
            admin.password_hash = generate_password_hash('admin123')
            admin.role_id = role.id
            admin.is_admin = True
            admin.is_active = True
            db.session.commit()
            print("\n[OK] 管理员账户已更新！")
            print("=" * 60)
            print("用户名：admin")
            print("邮箱：admin@example.com")
            print("密码：admin123")
            print("=" * 60)


if __name__ == '__main__':
    print("=" * 60)
    print("开始创建系统管理员...")
    print("=" * 60)
    create_admin()
    print("\n完成！")
