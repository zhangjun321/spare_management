#!/usr/bin/env python
"""
在 Flask 应用环境中测试邮件配置
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models.system import EmailConfig
from app.utils.email_service import EmailService

app = create_app()

with app.app_context():
    print("=" * 70)
    print("Flask 应用中测试邮件配置")
    print("=" * 70)
    
    # 获取配置
    config = EmailConfig.query.filter_by(is_active=True).first()
    
    if not config:
        print("✗ 未找到配置")
        sys.exit(1)
    
    print("\n读取到的配置:")
    print(f"  SMTP: {config.smtp_server}:{config.smtp_port}")
    print(f"  用户名：{config.username}")
    print(f"  发件人邮箱：{config.sender_email}")
    print(f"  密码：'{config.password}' (长度：{len(config.password) if config.password else 0})")
    print(f"  SSL: {config.use_tls}")
    
    # 测试连接
    print("\n测试连接...")
    service = EmailService()
    service.config = config
    
    success, msg = service.test_connection()
    if success:
        print(f"✓ 成功：{msg}")
    else:
        print(f"✗ 失败：{msg}")
    
    print("=" * 70)
