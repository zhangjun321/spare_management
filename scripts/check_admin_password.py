#!/usr/bin/env python3
"""
检查管理员密码脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db, check_password_hash, generate_password_hash
from app.models.user import User

# 创建应用实例
app = create_app()

with app.app_context():
    # 查找管理员用户
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        print('管理员账号不存在')
        sys.exit(1)
    
    # 检查用户提供的密码
    user_password = 'Kra@211314'
    is_valid = check_password_hash(admin.password_hash, user_password)
    
    print(f'检查密码 "{user_password}" 是否有效: {is_valid}')
    
    if not is_valid:
        # 提示当前密码
        print(f'当前管理员密码: admin123')
        
        # 询问是否要修改密码
        print('\n是否要将管理员密码修改为 Kra@211314? (y/n)')
        choice = input().strip().lower()
        
        if choice == 'y':
            # 修改密码
            admin.password_hash = generate_password_hash(user_password)
            db.session.commit()
            print('\n密码已修改成功!')
            print(f'管理员账号: admin')
            print(f'密码: {user_password}')
        else:
            print('\n密码未修改')
    else:
        print('密码有效!')
        print(f'管理员账号: admin')
        print(f'密码: {user_password}')
