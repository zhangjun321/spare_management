#!/usr/bin/env python3
"""
更新管理员密码
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(basedir, '..'))

from app import create_app
from app.extensions import db, generate_password_hash
from app.models.user import User


def update_admin_password():
    """更新管理员密码"""
    app = create_app()
    
    with app.app_context():
        # 查找管理员用户
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            print("错误：未找到管理员用户 'admin'")
            return False
        
        # 新密码
        new_password = 'Kra@211314'
        
        # 更新密码
        admin.password_hash = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            print(f"成功：管理员密码已更新为 '{new_password}'")
            return True
        except Exception as e:
            print(f"错误：更新密码失败 - {e}")
            db.session.rollback()
            return False


if __name__ == '__main__':
    print("=" * 60)
    print("更新管理员密码")
    print("=" * 60)
    success = update_admin_password()
    print("=" * 60)
    sys.exit(0 if success else 1)
