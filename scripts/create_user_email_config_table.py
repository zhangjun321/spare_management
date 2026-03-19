#!/usr/bin/env python
"""
创建用户邮箱配置表
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("创建用户邮箱配置表...")
    
    # 创建表
    db.create_all()
    
    print("✓ 用户邮箱配置表创建成功")
    print("\n表结构:")
    print("  - id: 主键")
    print("  - user_id: 用户 ID（外键关联 user 表）")
    print("  - smtp_server: SMTP 服务器")
    print("  - smtp_port: SMTP 端口")
    print("  - use_tls: 是否使用 TLS")
    print("  - username: 用户名")
    print("  - password: 密码/授权码")
    print("  - sender_email: 发件人邮箱")
    print("  - sender_name: 发件人名称")
    print("  - is_active: 是否启用")
    print("  - created_at: 创建时间")
    print("  - updated_at: 更新时间")
